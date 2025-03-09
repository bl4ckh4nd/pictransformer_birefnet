from abc import ABC, abstractmethod
import torch
from PIL import Image
from typing import Optional, Dict, Any

class BackgroundRemovalModel(ABC):
    """Base class for all background removal models"""
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.model = None
        self.half_precision = device == 'cuda'

    @abstractmethod
    def load_model(self, **kwargs):
        """Load the model with given parameters"""
        pass

    @abstractmethod
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess the image for model input"""
        pass

    @abstractmethod
    def predict(self, image: torch.Tensor) -> torch.Tensor:
        """Run model prediction"""
        pass

    @abstractmethod
    def postprocess(self, pred: torch.Tensor, original_image: Image.Image) -> Image.Image:
        """Convert model output to final image with alpha channel"""
        pass

    def clear_gpu_memory(self):
        """Clear GPU memory if using CUDA"""
        if self.device == 'cuda':
            torch.cuda.empty_cache()

    def __call__(self, image: Image.Image, **kwargs) -> Image.Image:
        """Process an image end-to-end"""
        try:
            input_tensor = self.preprocess(image)
            if self.half_precision:
                input_tensor = input_tensor.half()
            prediction = self.predict(input_tensor)
            result = self.postprocess(prediction, image)
            self.clear_gpu_memory()
            return result
        except Exception as e:
            raise RuntimeError(f"Error processing image: {str(e)}")

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return model metadata"""
        return {
            "device": self.device,
            "half_precision": self.half_precision,
            "model_loaded": self.model is not None
        }