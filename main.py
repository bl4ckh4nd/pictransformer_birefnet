import io
import time
import logging
import platform
from fastapi import FastAPI, File, UploadFile, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import torch
from PIL import Image
from models.registry import registry
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Method: {request.method} Path: {request.url.path} "
            f"Status: {response.status_code} Duration: {process_time:.2f}s"
        )
        return response

app = FastAPI(title="Background Removal API")
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CUDA
def setup_cuda():
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"CUDA version: {torch.version.cuda if torch.cuda.is_available() else 'Not available'}")
    
    if not torch.cuda.is_available():
        logger.error("CUDA is not available. This could be due to:")
        logger.error("1. No NVIDIA GPU present")
        logger.error("2. NVIDIA drivers not installed")
        logger.error("3. PyTorch not built with CUDA support")
        logger.error("4. CUDA toolkit not installed")
        return 'cpu'
    
    try:
        n_devices = torch.cuda.device_count()
        logger.info(f"Number of CUDA devices: {n_devices}")
        
        for i in range(n_devices):
            props = torch.cuda.get_device_properties(i)
            logger.info(f"GPU {i}: {props.name}")
            logger.info(f"  Memory: {props.total_memory / 1024**3:.2f}GB")
            logger.info(f"  CUDA Capability: {props.major}.{props.minor}")
        
        device = 'cuda'
        torch.set_float32_matmul_precision('high')
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.enabled = True
        
        # Test CUDA with a small tensor operation
        test_tensor = torch.rand(1).cuda()
        logger.info("CUDA test successful - tensor operation completed")
        
        return device
    except Exception as e:
        logger.error(f"Error initializing CUDA: {str(e)}")
        return 'cpu'

device = setup_cuda()
logger.info(f"Final device selection: {device}")

@app.post("/remove-background/")
async def remove_background(
    file: UploadFile = File(...),
    model: str = Query("rmbg2", description="Model to use for background removal"),
    enable_refinement: bool = Query(False, description="Enable refinement for supported models")
):
    logger.info(f"Processing image: {file.filename} with model: {model}")
    start_time = time.time()
    
    # Validate content type
    if not file.content_type.startswith('image/'):
        logger.error(f"Invalid content type: {file.content_type}")
        return JSONResponse(status_code=400, content={"error": "File must be an image"})
    
    try:
        # Get model
        bg_model = registry.get_model(model)
        if bg_model is None:
            return JSONResponse(
                status_code=400, 
                content={"error": f"Model {model} not available"}
            )
        
        # Read and process the image
        image_data = await file.read()
        if not image_data:
            logger.error("Received empty file")
            return JSONResponse(status_code=400, content={"error": "Empty file received"})
            
        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            return JSONResponse(status_code=400, content={"error": "Invalid image format"})
        
        # Convert to RGB if not already
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Process the image
        result_image = bg_model(image, enable_refinement=enable_refinement)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        process_time = time.time() - start_time
        logger.info(f"Successfully processed {file.filename} in {process_time:.2f}s")
        
        headers = {
            'Content-Type': 'image/png',
            'Content-Disposition': f'attachment; filename="processed_{file.filename}"'
        }
        
        return StreamingResponse(img_byte_arr, media_type="image/png", headers=headers)
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/models")
async def list_models():
    """List all available background removal models and their status"""
    return registry.get_available_models()

@app.post("/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a specific model into memory"""
    model = registry.get_model(model_name, load=True)
    if model is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Model {model_name} not found"}
        )
    return {"status": "success", "model": model_name}

@app.post("/models/{model_name}/unload")
async def unload_model(model_name: str):
    """Unload a specific model from memory"""
    registry.unload_model(model_name)
    return {"status": "success", "model": model_name}

@app.get("/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get detailed information about a model's requirements and configuration"""
    model = registry.get_model(model_name, load=True)
    if model is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Model {model_name} not found"}
        )
    
    # Get model configuration and requirements
    model_info = {
        "metadata": model.metadata,
        "device": model.device
    }
    
    if hasattr(model, 'model') and hasattr(model.model, 'config'):
        model_info["config"] = model.model.config
    
    return model_info

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cuda_available": torch.cuda.is_available(),
        "device": device,
        "models": registry.get_available_models()
    }

@app.get("/")
async def root():
    return {"message": "Background Removal API is running. Send POST request to /remove-background/ with an image file"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Background Removal API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)