import modal
import io
from PIL import Image
import torch
import logging
from typing import Dict, Any, Optional
from torchvision import transforms
import sys
import os

# Import models
from models.rmbg import RMBG2Model
from models.ben2 import BEN2Model
from models.birefnet import BiRefNetModel

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define image with dependencies
image = (modal.Image.debian_slim()
    .apt_install("git")
    .pip_install(
        "torch>=2.2.0",
        "torchvision>=0.17.0",
        "transformers>=4.38.2",
        "safetensors>=0.4.2",
        "Pillow>=10.2.0",
        "kornia>=0.6.12",
        "huggingface_hub>=0.4.1",
        "fastapi[standard]>=0.68.0"
    )
    .run_commands(
        # Install BEN2 from GitHub
        "pip install -e 'git+https://github.com/PramaLLC/BEN2.git#egg=ben2'",
        # Create model cache directory
        "mkdir -p /model_cache"
    )
    .add_local_dir("models", "/root/models")
    .add_local_python_source("image_proc", "models", "modal_api", "modal_gpu_service")
)

# Create app and volume for model cache
app = modal.App("background-removal-service", image=image)
model_cache = modal.Volume.from_name("model-cache-volume", create_if_missing=True)

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
        self.logger = logging.getLogger(__name__)
        # Default configurations
        self.default_config = {
            "half_precision": False,
            "enable_logging": True
        }
    
    def _preprocess_image(self, image: Image.Image, model_name: str) -> Image.Image:
        """Preprocess image based on model requirements"""
        self.logger.info(f"Preprocessing image for {model_name}, original size: {image.size}, mode: {image.mode}")
        
        if model_name == "birefnet":
            # Ensure dimensions are multiples of 32 for BiRefNet
            w, h = image.size
            new_w = ((w + 31) // 32) * 32
            new_h = ((h + 31) // 32) * 32
            
            if new_w != w or new_h != h:
                self.logger.info(f"Resizing image from {image.size} to {(new_w, new_h)} for BiRefNet")
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Handle RGBA images consistently
        if image.mode == 'RGBA':
            self.logger.info("Converting RGBA image to RGB with white background")
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            self.logger.info(f"Converting {image.mode} image to RGB")
            image = image.convert('RGB')
        
        return image

    @modal.method()
    def process_image(self, 
                     image_bytes: bytes, 
                     model_name: str, 
                     enable_refinement: bool = False,
                     half_precision: Optional[bool] = None) -> bytes:
        """GPU-accelerated background removal processing with advanced options"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply model-specific preprocessing
            image = self._preprocess_image(image, model_name)
            
            # Get or create model with specific configuration
            config = {
                "half_precision": half_precision if half_precision is not None else self.default_config["half_precision"]
            }
            
            bg_model = self._get_model(model_name, config=config)
            if bg_model is None:
                raise ValueError(f"Model {model_name} not available")
            
            # Process with refinement if supported
            if hasattr(bg_model, '__call__') and 'enable_refinement' in bg_model.__call__.__code__.co_varnames:
                result_image = bg_model(image, enable_refinement=enable_refinement)
            else:
                result_image = bg_model(image)
            
            buffer = io.BytesIO()
            result_image.save(buffer, format="PNG")
            return buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error processing image with {model_name}: {str(e)}")
            raise

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
    
    @modal.method()
    def configure_model(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure specific model parameters"""
        if model_name not in self.AVAILABLE_MODELS:
            return {"error": f"Model {model_name} not available"}
        
        try:
            model = self._get_model(model_name, config=config, load=True)
            if model is None:
                return {"error": "Failed to configure model"}
            return {"success": True, "metadata": model.metadata}
        except Exception as e:
            self.logger.error(f"Error configuring model {model_name}: {str(e)}")
            return {"error": str(e)}
    
    def _get_model(self, model_name: str, config: Dict[str, Any] = None, load: bool = True):
        """Get or create a model instance with specific configuration"""
        if model_name not in self.AVAILABLE_MODELS:
            return None
            
        # Use provided config or defaults
        config = config or {}
        final_config = {**self.default_config, **config}
        
        # Check if we need to recreate the model with new config
        if model_name in self._model_instances:
            current_model = self._model_instances[model_name]
            if hasattr(current_model, 'half_precision') and \
               current_model.half_precision != final_config.get('half_precision'):
                self.logger.info(f"Recreating {model_name} model due to half_precision change")
                del self._model_instances[model_name]
        
        if model_name not in self._model_instances:
            try:
                # Import handling for different models
                if model_name == "ben2":
                    try:
                        from ben2 import BEN_Base
                    except ImportError:
                        raise ImportError("BEN2 model requires ben2 package. Please install it first.")
                elif model_name == "birefnet":
                    try:
                        from transformers import AutoModelForImageSegmentation
                    except ImportError:
                        raise ImportError("BiRefNet model requires transformers package. Please install it first.")
                
                model_class = self.AVAILABLE_MODELS[model_name]
                model = model_class(device=self.device)
                
                # Configure model attributes
                if hasattr(model, 'half_precision'):
                    model.half_precision = final_config.get('half_precision', False)
                    if model.half_precision and model_name == "birefnet":
                        torch.set_float32_matmul_precision('high')
                
                if load:
                    self.logger.info(f"Loading {model_name} model...")
                    model.load_model()
                    self.logger.info(f"{model_name} model loaded successfully")
                
                self._model_instances[model_name] = model
                
            except Exception as e:
                self.logger.error(f"Failed to create model {model_name}: {str(e)}")
                return None
                
        return self._model_instances[model_name]