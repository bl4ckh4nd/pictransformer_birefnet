import io
from PIL import Image
import torch
from models.rmbg import RMBG2Model
from models.ben2 import BEN2Model
from models.birefnet import BiRefNetModel

# Define available models and a cache for model instances.
AVAILABLE_MODELS = {
    "rmbg2": RMBG2Model,
    "ben2": BEN2Model,
    "birefnet": BiRefNetModel
}
_model_instances = {}

def get_model(model_name: str, device: str, load: bool = True):
    """Get or create a model instance from the cache."""
    if model_name not in AVAILABLE_MODELS:
        return None
    if model_name not in _model_instances:
        try:
            model_class = AVAILABLE_MODELS[model_name]
            model = model_class(device=device)
            if load:
                model.load_model()
            _model_instances[model_name] = model
        except Exception as e:
            print(f"Failed to create model {model_name}: {str(e)}")
            return None
    return _model_instances[model_name]

def remove_background(image_bytes: bytes, model_name: str, enable_refinement: bool = False) -> bytes:
    """Perform background removal using the specified model."""
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGB')
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        raise RuntimeError("GPU is required for background removal!")
    
    model = get_model(model_name, device=device)
    if model is None:
        raise ValueError(f"Model {model_name} not available")
    
    result_image = model(image, enable_refinement=enable_refinement)
    buffer = io.BytesIO()
    result_image.save(buffer, format="PNG")
    return buffer.getvalue()
