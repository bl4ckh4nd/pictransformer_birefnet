# Background Removal App: Vercel + Modal Implementation Specification

## Overview

This document outlines the implementation strategy for deploying the background removal application with:
- Frontend hosted on Vercel
- GPU-intensive background removal processing on Modal.com

## Architecture Design

![Architecture Diagram](https://mermaid.ink/img/pako:eNptkstuwjAQRX9l5FUq8QGsoCQSRapAqig8NmRjJgQpsSPHQaWI_15DKlrcrTxn7twZz1O4JRIiEd1xTVtGK2DIShRkUXNDe1QEnSHnNcxKptdyOpmCzrzTygavvQatEB_hmIE2cMZFDaXQn6p17a3wJdd77_97MWPgMTppd4UHXxhnoUs3gG9t1KNS6whac3ntHxgHqXHBgIqwqXsYKV1QaJnGnqk1_FSv4-aZiSaMd8iaEqG8vNzZBv-t4oRAOmow8VsN591Ba6p5_AsBUZLYnmocf1Jes_0cZajBvSJQ8oZqS7IPKtIvbamkzFk7FHGD0GLf7J37mtnPMMfiWziIeIeGWq5BRZy24gfOksiSyZzlEt5EZ5iIOk4F18hfqZGsJmWUjMfJOJ1OkzRK4BgN0mGSpdPpYvbcw--QpOfwLLzAtu1PyOHTYQ)

### Components:

1. **Vercel Frontend**
   - Static React app
   - Makes API calls to Modal.com for image processing

2. **Modal.com Backend**
   - GPU-powered serverless functions
   - Handles model loading and background removal

3. **Cloud Storage**
   - For temporary storage of processed images

## Implementation Steps

### 1. Modal.com GPU Function Implementation

Create a Modal app that handles background removal:

```python
import modal
from typing import Optional
import io
import base64
from PIL import Image
import torch
from typing import Dict, Any

# Import your models
# We'll need to package these with the Modal app
from models.registry import registry
from models.rmbg import RMBG2Model
from models.ben2 import BEN2Model
from models.birefnet import BiRefNetModel

# Define the Modal image with GPU requirements and dependencies
image = modal.Image.debian_slim().pip_install(
    "torch==2.2.0",
    "torchvision==0.17.0",
    "transformers==4.38.2",
    "safetensors==0.4.2",
    "Pillow==10.2.0",
    "huggingface_hub==0.20.3",
    # Add other dependencies your models need
)

# Create the Modal app with GPU support
app = modal.App("background-removal", image=image)

# Create a volume for storing model weights persistently
model_cache = modal.Volume.persisted("model-cache-volume")

class BackgroundRemovalFunctions:
    # This class defines our Modal.com serverless functions
    
    def __init__(self):
        # This runs when the container is initialized
        self.registry = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    @app.function(
        gpu="T4",  # Use T4 GPU (or A10G for more power)
        volumes={"/model_cache": model_cache},
        timeout=60*10,  # 10 minute timeout
        concurrency_limit=5  # Limit concurrent executions
    )
    def initialize(self):
        """Initialize the model registry"""
        # Set model directory to use the persistent volume
        import os
        os.environ["MODEL_DIR"] = "/model_cache"
        
        # Initialize registry
        from models.registry import registry
        self.registry = registry
        
        return {"status": "initialized", "device": self.device}
    
    @app.function(
        gpu="T4",
        volumes={"/model_cache": model_cache},
        timeout=60*10,
        concurrency_limit=5
    )
    def remove_background(
        self, 
        image_data: str, 
        model: str = "rmbg2", 
        enable_refinement: bool = False
    ) -> Dict[str, Any]:
        """Remove background from an image
        
        Args:
            image_data: Base64 encoded image
            model: Model name (rmbg2, ben2, or birefnet)
            enable_refinement: Whether to enable refinement
            
        Returns:
            Dict with base64 encoded result image
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if not already
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            # Get the model from registry
            bg_model = self.registry.get_model(model)
            if bg_model is None:
                return {"error": f"Model {model} not available"}
            
            # Process the image
            result_image = bg_model(image, enable_refinement=enable_refinement)
            
            # Convert result back to base64
            buffer = io.BytesIO()
            result_image.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                "status": "success",
                "processed_image": img_str
            }
        
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    @app.function(
        gpu="T4",
        volumes={"/model_cache": model_cache}
    )
    def list_models(self) -> Dict[str, Any]:
        """List all available background removal models and their status"""
        try:
            models = self.registry.get_available_models()
            return {"models": models, "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    @app.function(
        gpu="T4",
        volumes={"/model_cache": model_cache}
    )
    def load_model(self, model_name: str) -> Dict[str, Any]:
        """Load a specific model into memory"""
        try:
            model = self.registry.get_model(model_name, load=True)
            if model is None:
                return {"error": f"Model {model_name} not found", "status": "failed"}
            return {"status": "success", "model": model_name}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

# Create a client for our functions
functions = app.cls(BackgroundRemovalFunctions)
```

### 2. Modal.com API Wrapper

Create a serverless REST API with Modal:

```python
import modal
from modal_app import app, functions
from fastapi import FastAPI, Body
from typing import Optional
import base64
from pydantic import BaseModel

web_app = FastAPI()

class ImageRequest(BaseModel):
    image: str  # base64 encoded image
    model: str = "rmbg2"
    enable_refinement: bool = False

@web_app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@web_app.get("/models")
async def list_models():
    """List all available models"""
    result = functions.list_models.remote()
    return result

@web_app.post("/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a specific model"""
    result = functions.load_model.remote(model_name)
    return result

@web_app.post("/remove-background")
async def remove_background(request: ImageRequest):
    """Process an image to remove the background"""
    result = functions.remove_background.remote(
        request.image, 
        request.model,
        request.enable_refinement
    )
    return result

# Deploy as a Modal web endpoint
@app.function(
    timeout=300,
    keep_warm=1
)
@modal.asgi_app()
def fastapi_app():
    # Initialize the registry when the app starts
    functions.initialize.remote()
    return web_app
```

### 3. Frontend Modifications for Vercel Deployment

Update the API service in the React frontend:

```typescript
import axios from 'axios';

export interface ModelsResponse {
  [key: string]: {
    loaded: boolean;
    metadata?: any;
  };
}

// Get the API base URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-modal-app-url.modal.run';

const api = {
  async getModels(): Promise<ModelsResponse> {
    try {
      const response = await axios.get(`${API_BASE_URL}/models`);
      return response.data.models || {};
    } catch (error) {
      console.error('Error fetching models:', error);
      throw error;
    }
  },

  async loadModel(modelName: string): Promise<void> {
    try {
      await axios.post(`${API_BASE_URL}/models/${modelName}/load`);
    } catch (error) {
      console.error(`Error loading model ${modelName}:`, error);
      throw error;
    }
  },

  async removeBackground(
    file: File, 
    modelName: string = 'rmbg2',
    enableRefinement: boolean = false
  ): Promise<Blob> {
    try {
      // Convert file to base64
      const base64 = await fileToBase64(file);
      
      // Remove the data URL prefix
      const base64Data = base64.split(',')[1];
      
      // Send the request to remove background
      const response = await axios.post(
        `${API_BASE_URL}/remove-background`,
        {
          image: base64Data,
          model: modelName,
          enable_refinement: enableRefinement
        },
        {
          // Increase timeout for large images
          timeout: 120000,
        }
      );
      
      // Handle potential error response
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      // Convert base64 response back to Blob
      const imgBlob = base64ToBlob(
        response.data.processed_image,
        'image/png'
      );
      
      return imgBlob;
    } catch (error) {
      console.error('Error removing background:', error);
      throw error;
    }
  }
};

// Helper function to convert File to base64
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = error => reject(error);
  });
}

// Helper function to convert base64 to Blob
function base64ToBlob(base64: string, mimeType: string): Blob {
  const byteCharacters = atob(base64);
  const byteArrays = [];
  
  for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
    const slice = byteCharacters.slice(offset, offset + 1024);
    const byteNumbers = new Array(slice.length);
    
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }
  
  return new Blob(byteArrays, { type: mimeType });
}

export default api;
```

### 4. Next.js Configuration for Vercel

Convert the React app to Next.js for better Vercel compatibility:

```typescript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  images: {
    domains: ['localhost'],
    // Add any other domains you might load images from
  },
};

module.exports = nextConfig;
```

### 5. Environment Setup

Create a `.env.local` file for Vercel:

```
NEXT_PUBLIC_API_URL=https://your-modal-app-name.modal.run
```

### 6. Modal Package Configuration

Create a requirements file for Modal:

```
torch==2.2.0
torchvision==0.17.0
transformers==4.38.2
Pillow==10.2.0
safetensors==0.4.1
huggingface_hub==0.20.3
fastapi==0.104.1
pydantic==2.4.2
```

### 7. Deployment Instructions

#### Modal.com Deployment

1. Install Modal CLI:
   ```bash
   pip install modal
   ```

2. Configure Modal account:
   ```bash
   modal token new
   ```

3. Deploy Modal app:
   ```bash
   modal deploy modal_api.py
   ```

4. Get the Modal endpoint URL after deployment

#### Vercel Deployment

1. Push code to GitHub

2. Connect repository in Vercel dashboard

3. Configure environment variables:
   - `NEXT_PUBLIC_API_URL`: Your Modal endpoint URL

4. Deploy the application

## Performance Considerations

1. **Image Size Limits**: 
   - Implement client-side validation for maximum image dimensions
   - Add resizing option for large images to reduce processing time

2. **Modal.com Optimizations**:
   - Use T4 GPUs for standard workloads, A10G for larger images
   - Implement `keep_warm=1` for faster response times
   - Use persistent volume for model weights to avoid redownloading

3. **Frontend Optimizations**:
   - Implement progressive loading for large images
   - Add processing status indicators
   - Use WebP format for previews to reduce bandwidth

## Cost Optimization

1. **Modal.com Costs**:
   - T4 GPU: ~$0.60/hour
   - Implement auto-shutdown of idle containers
   - Use smaller models for simple images

2. **Vercel Costs**:
   - Basic tier should be sufficient for frontend hosting
   - Implement caching for static assets

## Monitoring and Analytics

1. Add Sentry for error tracking
2. Implement server-side logging in Modal functions
3. Add client-side analytics for feature usage

## Security Considerations

1. Implement rate limiting on Modal endpoints
2. Add authentication for production use
3. Validate image formats and sizes
4. Set appropriate CORS policies

## Future Enhancements

1. Progressive model loading based on image complexity
2. User accounts for saving processing history
3. Batch processing capabilities
4. Advanced editing features integration

This implementation plan provides a comprehensive roadmap for migrating your background removal application to a Vercel + Modal architecture, leveraging the strengths of both platforms for optimal performance and user experience.

Similar code found with 2 license types