import modal
from typing import Dict, Any, Optional
import io
import base64
from PIL import Image
import torch
from models.rmbg import RMBG2Model
from models.ben2 import BEN2Model
from models.birefnet import BiRefNetModel

# Define the Modal image with GPU requirements and dependencies
image = (modal.Image.debian_slim()
    .apt_install("git")  # Install git first
    .pip_install(
        "torch>=2.2.0",
        "torchvision>=0.17.0",
        "transformers>=4.38.2",
        "safetensors>=0.4.2",
        "Pillow>=10.2.0",
        "huggingface_hub>=0.4.1",
        "fastapi>=0.68.0"
    )
    .run_commands("pip install -e 'git+https://github.com/PramaLLC/BEN2.git#egg=ben2'")
    .copy_local_dir("models", "/root/models")
)

# Create the Modal app with GPU support
app = modal.App("background-removal")

# Create a volume for storing model weights
model_cache = modal.Volume.from_name("model-cache-volume", create_if_missing=True)

@app.cls(
    image=image,
    gpu="T4",
    volumes={"/model_cache": model_cache}
)
class BackgroundRemovalFunctions:
    AVAILABLE_MODELS = {
        "rmbg2": RMBG2Model,
        "ben2": BEN2Model,
        "birefnet": BiRefNetModel
    }
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_instances: Dict[str, Any] = {}
        
    @modal.method()
    def initialize(self):
        """Initialize the environment"""
        import os
        os.environ["MODEL_DIR"] = "/model_cache"
        return {"status": "initialized", "device": self.device}
    
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
    
    @modal.method()
    def remove_background(
        self, 
        image_data: str, 
        model: str = "rmbg2", 
        enable_refinement: bool = False
    ) -> Dict[str, Any]:
        """Remove background from an image"""
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            bg_model = self._get_model(model)
            if bg_model is None:
                return {"error": f"Model {model} not available"}
            
            result_image = bg_model(image, enable_refinement=enable_refinement)
            
            buffer = io.BytesIO()
            result_image.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                "status": "success",
                "processed_image": img_str
            }
        
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    @modal.method()
    def list_models(self) -> Dict[str, Any]:
        """List all available background removal models and their status"""
        try:
            models = {
                name: {
                    "loaded": name in self._model_instances,
                    "metadata": self._get_model(name).metadata if name in self._model_instances else None
                }
                for name in self.AVAILABLE_MODELS.keys()
            }
            return {"models": models, "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    @modal.method()
    def load_model(self, model_name: str) -> Dict[str, Any]:
        """Load a specific model into memory"""
        try:
            model = self._get_model(model_name, load=True)
            if model is None:
                return {"error": f"Model {model_name} not found", "status": "failed"}
            return {"status": "success", "model": model_name}
        except Exception as e:
            return {"error": str(e), "status": "failed"}