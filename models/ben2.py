from .base import BackgroundRemovalModel
import torch
from PIL import Image
from typing import Dict, Any
import sys
import os
from image_proc import refine_foreground

class BEN2Model(BackgroundRemovalModel):
    """BEN2 model implementation"""
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        super().__init__(device)
        self.refine_enabled = False
        # Disable half precision by default as it's causing issues
        self.half_precision = False

    def load_model(self, **kwargs):
        """Load BEN2 model"""
        try:
            from ben2 import BEN_Base
            self.model = BEN_Base.from_pretrained("PramaLLC/BEN2")
            self.model.to(self.device)
            self.model.eval()
            
            # Only apply half precision to the model, not to input images
            if self.half_precision:
                self.model = self.model.half()
        except ImportError:
            raise ImportError("BEN2 model requires ben2 package. Please install it first.")

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """BEN2 handles preprocessing internally"""
        return image

    def predict(self, image: Image.Image) -> Image.Image:
        """Run BEN2 prediction"""
        with torch.no_grad():
            try:
                result = self.model.inference(
                    image,
                    refine_foreground=self.refine_enabled
                )
            except Exception as e:
                # If there's an error, try with half precision disabled
                if self.half_precision:
                    self.model = self.model.float()
                    result = self.model.inference(
                        image,
                        refine_foreground=self.refine_enabled
                    )
                else:
                    raise e
        return result

    def postprocess(self, pred: Image.Image, original_image: Image.Image) -> Image.Image:
        """BEN2 already provides the final image"""
        return pred

    def __call__(self, image: Image.Image, enable_refinement: bool = False) -> Image.Image:
        """Override to handle refinement parameter"""
        self.refine_enabled = enable_refinement
        return super().__call__(image)

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return BEN2 specific metadata"""
        base_metadata = super().metadata
        base_metadata.update({
            "name": "BEN2",
            "model_type": "matting",
            "supports_refinement": True
        })
        return base_metadata