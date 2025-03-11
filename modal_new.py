import modal
import base64
import io
from PIL import Image
import torch
from pydantic import BaseModel
from typing import Dict, Any
from models.rmbg import RMBG2Model
from models.ben2 import BEN2Model
from models.birefnet import BiRefNetModel

# Define image with dependencies
image = (modal.Image.debian_slim()
    .apt_install("git")
    .pip_install(
        "torch>=2.2.0",
        "torchvision>=0.17.0",
        "transformers>=4.38.2",
        "safetensors>=0.4.2",
        "Pillow>=10.2.0",
        "fastapi>=0.68.0"
    )
    .run_commands("pip install -e 'git+https://github.com/PramaLLC/BEN2.git#egg=ben2'")
    .add_local_dir("models", "/root/models")
)

app = modal.App("background-removal", image=image)
model_cache = modal.Volume.from_name("model-cache-volume", create_if_missing=True)

# Define the request model
class ImageRequest(BaseModel):
    image: str  # base64 encoded image
    model: str = "rmbg2"
    enable_refinement: bool = False

# GPU-accelerated service for background removal
@app.cls(gpu="T4", volumes={"/model_cache": model_cache})
class GPUBackgroundRemovalService:
    AVAILABLE_MODELS = {
        "rmbg2": RMBG2Model,
        "ben2": BEN2Model,
        "birefnet": BiRefNetModel
    }
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_instances: Dict[str, Any] = {}
        if self.device != "cuda":
            raise RuntimeError("GPU is required for background removal!")
    
    @modal.method()
    def process_image(self, image_bytes: bytes, model_name: str, enable_refinement: bool = False) -> bytes:
        """GPU-accelerated background removal processing"""
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        bg_model = self._get_model(model_name)
        if bg_model is None:
            raise ValueError(f"Model {model_name} not available")
        
        result_image = bg_model(img, enable_refinement=enable_refinement)
        buffer = io.BytesIO()
        result_image.save(buffer, format="PNG")
        return buffer.getvalue()
        
    def _get_model(self, model_name: str, load: bool = True):
        """Get or create a model instance"""
        if model_name not in self.AVAILABLE_MODELS:
            return None
        if model_name not in self._model_instances:
            try:
                model_class = self.AVAILABLE_MODELS[model_name]
                model = model_class(device=self.device)
                if load:
                    model.load_model()
                self._model_instances[model_name] = model
            except Exception as e:
                print(f"Failed to create model {model_name}: {str(e)}")
                return None
        return self._model_instances[model_name]

# CPU service for other endpoints
@app.cls(volumes={"/model_cache": model_cache})
class CPUService:
    def __init__(self):
        self._models_status = {
            "rmbg2": {"loaded": False},
            "ben2": {"loaded": False},
            "birefnet": {"loaded": False}
        }
    
    @modal.method()
    def health(self) -> Dict[str, str]:
        return {"status": "healthy"}
    
    @modal.method()
    def list_models(self) -> Dict[str, Any]:
        return {"models": self._models_status, "status": "success"}
    
    @modal.method()
    def load_model(self, model_name: str) -> Dict[str, Any]:
        if model_name not in self._models_status:
            return {"error": f"Model {model_name} not found", "status": "failed"}
        self._models_status[model_name]["loaded"] = True
        return {"status": "success", "model": model_name}

# Create a unified FastAPI app that mounts both services
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, APIRouter, HTTPException
    app = FastAPI()
    
    # Lookup service instances
    cpu_service = CPUService.lookup()
    gpu_service = GPUBackgroundRemovalService.lookup()

    # CPU endpoints router
    cpu_router = APIRouter()
    
    @cpu_router.get("/health")
    async def health():
        return await cpu_service.health.remote()
    
    @cpu_router.get("/models")
    async def list_models():
        return await cpu_service.list_models.remote()
    
    @cpu_router.post("/models/{model_name}/load")
    async def load_model(model_name: str):
        return await cpu_service.load_model.remote(model_name)
    
    # GPU endpoint router for background removal
    gpu_router = APIRouter()
    
    @gpu_router.post("/remove-background")
    async def remove_background(request: ImageRequest):
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(request.image)
            # Process image using GPU-accelerated function and await the result
            result_bytes = await gpu_service.process_image.remote(
                image_bytes, 
                request.model, 
                request.enable_refinement
            )
            # Encode result
            img_str = base64.b64encode(result_bytes).decode('utf-8')
            return {"status": "success", "processed_image": img_str}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    app.include_router(cpu_router)
    app.include_router(gpu_router)
    
    return app
