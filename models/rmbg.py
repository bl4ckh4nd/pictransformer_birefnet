from .base import BackgroundRemovalModel
import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation
from typing import Dict, Any

class RMBG2Model(BackgroundRemovalModel):
    """RMBG 2.0 model implementation"""
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        super().__init__(device)
        self.image_size = (1024, 1024)
        self.transform = None
        self.setup_transforms()

    def setup_transforms(self):
        """Setup image transformation pipeline"""
        self.transform = transforms.Compose([
            transforms.Resize(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def load_model(self, **kwargs):
        """Load RMBG 2.0 model"""
        self.model = AutoModelForImageSegmentation.from_pretrained(
            'briaai/RMBG-2.0',
            trust_remote_code=True
        )
        self.model.to(self.device)
        self.model.eval()
        
        if self.half_precision:
            self.model.half()
            torch.set_float32_matmul_precision('high')

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess the image for RMBG 2.0"""
        if image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        input_tensor = self.transform(image).unsqueeze(0)
        return input_tensor.to(self.device)

    def predict(self, image: torch.Tensor) -> torch.Tensor:
        """Run RMBG 2.0 prediction"""
        with torch.no_grad():
            pred = self.model(image)[-1].sigmoid().cpu()
        return pred[0].squeeze()

    def postprocess(self, pred: torch.Tensor, original_image: Image.Image) -> Image.Image:
        """Convert RMBG 2.0 output to final image"""
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(original_image.size)
        
        # Create copy of original image and set alpha
        result = original_image.copy()
        result.putalpha(mask)
        return result

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return RMBG 2.0 specific metadata"""
        base_metadata = super().metadata
        base_metadata.update({
            "name": "RMBG 2.0",
            "model_type": "segmentation",
            "image_size": self.image_size,
            "supports_refinement": False
        })
        return base_metadata