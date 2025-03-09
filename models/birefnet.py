from .base import BackgroundRemovalModel
import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation
from typing import Dict, Any
import logging

class BiRefNetModel(BackgroundRemovalModel):
    """BiRefNet model implementation"""
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        super().__init__(device)
        self.transform = None
        self.current_size = None
        self.logger = logging.getLogger(__name__)

    def setup_transforms(self, image_size):
        """Setup image transformation pipeline with dynamic size"""
        self.current_size = image_size
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def load_model(self, **kwargs):
        """Load BiRefNet model"""
        self.model = AutoModelForImageSegmentation.from_pretrained(
            'zhengpeng7/BiRefNet',
            trust_remote_code=True
        )
        self.model.to(self.device)
        self.model.eval()
        
        # Log model configuration for debugging
        self.logger.info(f"Model configuration: {self.model.config}")
        
        if self.half_precision:
            self.model.half()
            torch.set_float32_matmul_precision('high')

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess the image for BiRefNet"""
        self.logger.info(f"Original image size: {image.size}, mode: {image.mode}")
        
        # Ensure image dimensions are multiples of 32 (based on model architecture requirements)
        w, h = image.size
        new_w = ((w + 31) // 32) * 32
        new_h = ((h + 31) // 32) * 32
        
        if new_w != w or new_h != h:
            self.logger.info(f"Resizing image from {image.size} to {(new_w, new_h)} to ensure dimensions are multiples of 32")
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.logger.info(f"Expected patch count: {new_w//32}x{new_h//32}, patch size: 32x32")
            self.logger.info(f"Expected flattened patch dimension: {32*32*3} channels")
        
        if image.mode == 'RGBA':
            self.logger.info("Converting RGBA image to RGB with white background")
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            self.logger.info(f"Converting {image.mode} image to RGB")
            image = image.convert('RGB')
        
        # Setup transforms for this specific image size
        self.setup_transforms(image.size)
        input_tensor = self.transform(image).unsqueeze(0)
        self.logger.info(f"Preprocessed tensor shape: {input_tensor.shape}")
        self.logger.info(f"Tensor device: {input_tensor.device}, dtype: {input_tensor.dtype}")
        return input_tensor.to(self.device)

    def predict(self, image: torch.Tensor) -> torch.Tensor:
        """Run BiRefNet prediction"""
        self.logger.info(f"Input tensor shape before prediction: {image.shape}")
        with torch.no_grad():
            try:
                pred = self.model(image)[-1].sigmoid().cpu()
                self.logger.info(f"Prediction successful, output shape: {pred.shape}")
                return pred[0].squeeze()
            except Exception as e:
                self.logger.error(f"Prediction failed with error: {str(e)}")
                # Access config attributes directly since it's a custom Config object
                if hasattr(self.model, 'config'):
                    self.logger.error(f"Model configuration: size={getattr(self.model.config, 'size', 'Not specified')}")
                raise

    def postprocess(self, pred: torch.Tensor, original_image: Image.Image) -> Image.Image:
        """Convert BiRefNet output to final image"""
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(original_image.size)
        
        # Create copy of original image and set alpha
        result = original_image.copy()
        result.putalpha(mask)
        return result

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return BiRefNet specific metadata"""
        base_metadata = super().metadata
        base_metadata.update({
            "name": "BiRefNet",
            "model_type": "segmentation",
            "image_size": self.current_size,
            "supports_refinement": False
        })
        return base_metadata