import modal
import base64
from pydantic import BaseModel
from typing import Dict, Any
from modal_gpu_service import app, BackgroundRemovalService
from models.rmbg import RMBG2Model
from models.ben2 import BEN2Model
from models.birefnet import BiRefNetModel

# CPU-side model registry
AVAILABLE_MODELS = {
    "rmbg2": RMBG2Model,
    "ben2": BEN2Model,
    "birefnet": BiRefNetModel
}

# Request model for the API
class ImageRequest(BaseModel):
    image: str  # base64 encoded image
    model: str = "rmbg2"
    enable_refinement: bool = False

# Create a web endpoint using the fastapi_endpoint decorator (replacing deprecated web_endpoint)
@app.function(timeout=300)
@modal.fastapi_endpoint(method="GET")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.function(timeout=60)
@modal.fastapi_endpoint(method="GET")
def models():
    """List all available models endpoint"""
    try:
        # Get an instance of the GPU service
        gpu_service = BackgroundRemovalService()
        
        # Call the GPU service remotely to get model information
        models_data = gpu_service.list_models.remote()
        return {"models": models_data, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.function(timeout=60)
@modal.fastapi_endpoint(method="GET")
def available_models():
    """CPU-side endpoint that just returns the list of model names"""
    try:
        return {
            "models": list(AVAILABLE_MODELS.keys()),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.function(timeout=300)
@modal.fastapi_endpoint(method="POST")
def load_model(model_name: str):
    """Load a specific model endpoint"""
    try:
        # Get an instance of the GPU service
        gpu_service = BackgroundRemovalService()
        
        # Call the GPU service remotely to load the model
        success = gpu_service.load_model.remote(model_name)
        if not success:
            return {"error": f"Model {model_name} not found", "status": "failed"}
        return {"status": "success", "model": model_name}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.function(timeout=300)
@modal.fastapi_endpoint(method="POST")
def remove_background(request: ImageRequest):
    """Process an image to remove the background endpoint"""
    try:
        # Get an instance of the GPU service
        gpu_service = BackgroundRemovalService()
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.image)
        except Exception:
            return {"error": "Invalid base64 encoded image", "status": "failed"}
        
        # Process image using GPU-accelerated function remotely
        result_bytes = gpu_service.process_image.remote(
            image_bytes, 
            request.model, 
            request.enable_refinement
        )
        
        # Encode result
        img_str = base64.b64encode(result_bytes).decode('utf-8')
        
        return {
            "status": "success",
            "processed_image": img_str
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# Main ASGI wrapper to create a FastAPI-compatible interface (optional)
@app.function(timeout=300)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Background Removal API")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    
    # Import the endpoints defined above
    from modal_api import health, models, available_models, load_model, remove_background
    
    # Define the FastAPI routes that call our Modal endpoints
    @app.get("/health")
    async def api_health():
        return health.remote()
    
    @app.get("/models")
    async def api_models():
        return models.remote()
        
    @app.get("/available-models")
    async def api_available_models():
        return available_models.remote()
    
    @app.post("/models/{model_name}/load")
    async def api_load_model(model_name: str):
        return load_model.remote(model_name)
    
    @app.post("/remove-background")
    async def api_remove_background(request: ImageRequest):
        return remove_background.remote(request)
    
    return app