import modal
import io
from PIL import Image
import torch
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
        "huggingface_hub>=0.4.1",
        # Add FastAPI with standard extensions (required for web endpoints)
        "fastapi[standard]>=0.68.0"
    )
    .run_commands("pip install -e 'git+https://github.com/PramaLLC/BEN2.git#egg=ben2'")
    # Explicitly add local Python modules
    .add_local_dir("models", "/root/models")
    .add_local_python_source("image_proc", "models", "modal_api", "modal_gpu_service")
)

# Create app and volume for model cache
app = modal.App("background-removal-service", image=image)
model_cache = modal.Volume.from_name("model-cache-volume", create_if_missing=True)

# GPU Service Class - Handles all GPU operations
@app.cls(gpu="T4", volumes={"/model_cache": model_cache})
class BackgroundRemovalService:
    AVAILABLE_MODELS = {
        "rmbg2": RMBG2Model,
        "ben2": BEN2Model,
        "birefnet": BiRefNetModel
    }
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_instances: Dict[str, Any] = {}
    
    @modal.method()
    def process_image(self, image_bytes: bytes, model_name: str, enable_refinement: bool = False) -> bytes:
        """GPU-accelerated background removal processing"""
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        bg_model = self._get_model(model_name)
        if bg_model is None:
            raise ValueError(f"Model {model_name} not available")
        
        result_image = bg_model(image, enable_refinement=enable_refinement)
        
        buffer = io.BytesIO()
        result_image.save(buffer, format="PNG")
        return buffer.getvalue()
    
    @modal.method()
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is already loaded in memory"""
        return model_name in self._model_instances
    
    @modal.method()
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get metadata about a specific model"""
        if model_name not in self.AVAILABLE_MODELS:
            return {"error": f"Model {model_name} not available"}
            
        model = self._get_model(model_name, load=False)
        if model is None:
            return {"error": f"Failed to initialize {model_name}"}
            
        return model.metadata
    
    @modal.method()
    def load_model(self, model_name: str) -> bool:
        """Explicitly load a model into memory"""
        if model_name not in self.AVAILABLE_MODELS:
            return False
            
        try:
            # Force load the model
            _ = self._get_model(model_name, load=True)
            return True
        except Exception:
            return False
        
    @modal.method()
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available models"""
        result = {}
        for name in self.AVAILABLE_MODELS.keys():
            is_loaded = name in self._model_instances
            metadata = None
            
            if is_loaded:
                try:
                    metadata = self._model_instances[name].metadata
                except Exception:
                    pass
                    
            result[name] = {
                "loaded": is_loaded,
                "metadata": metadata
            }
            
        return result
    
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