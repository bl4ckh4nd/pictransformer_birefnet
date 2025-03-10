from .base import BackgroundRemovalModel
from .fix_imports import apply_fixes
import torch
from PIL import Image
from torchvision import transforms
from huggingface_hub import hf_hub_download
from typing import Dict, Any, List
import logging
import os
from safetensors.torch import load_file

logger = logging.getLogger(__name__)

def download_rmbg_files(model_dir: str) -> Dict[str, str]:
    """Download required model files from Hugging Face hub"""
    repo_id = 'briaai/RMBG-2.0'
    files = [
        'BiRefNet_config.py',
        'birefnet.py',
        'config.json',
        'model.safetensors'
    ]
    
    downloaded_files = {}
    for file in files:
        try:
            file_path = hf_hub_download(
                repo_id=repo_id,
                filename=file,
                cache_dir=model_dir
            )
            downloaded_files[file] = file_path
            logger.info(f"Successfully downloaded {file} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to download {file}: {str(e)}")
            raise
    
    return downloaded_files

class RMBG2Model(BackgroundRemovalModel):
    """RMBG 2.0 model implementation"""
    def __init__(self, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        super().__init__(device)
        self.image_size = (1024, 1024)
        self.transform = None
        self.setup_transforms()
        self.model_dir = os.path.join(os.path.dirname(__file__), "..", "downloaded_models", "rmbg2")
        os.makedirs(self.model_dir, exist_ok=True)
        # Explicitly set half_precision to True when using CUDA
        self.half_precision = device.startswith('cuda')

    def setup_transforms(self):
        """Setup image transformation pipeline"""
        self.transform = transforms.Compose([
            transforms.Resize(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def load_model(self, **kwargs):
        """Load RMBG 2.0 model"""
        try:
            logger.info("Starting model download and loading process...")
            
            # Download model files
            model_files = download_rmbg_files(self.model_dir)
            
            # Apply import fixes
            apply_fixes(self.model_dir)
            
            # Import the patched BiRefNet
            birefnet_path = os.path.join(os.path.dirname(model_files['birefnet.py']), 'patched_birefnet.py')
            
            import birefnet
            self.model = birefnet.BiRefNet()
            
            # Load safetensors weights
            try:
                # First try loading with safetensors
                state_dict = load_file(model_files['model.safetensors'])
            except Exception as e:
                logger.warning(f"Failed to load with safetensors: {str(e)}, falling back to torch.load")
                # Fallback to torch.load with weights_only=False
                state_dict = torch.load(model_files['model.safetensors'], 
                                      map_location=self.device,
                                      weights_only=False)
            
            # Convert state_dict to half precision BEFORE loading if using CUDA
            if self.half_precision:
                logger.info("Converting state_dict to half precision before loading")
                for k in state_dict.keys():
                    if state_dict[k].dtype == torch.float32:
                        state_dict[k] = state_dict[k].half()
            
            self.model.load_state_dict(state_dict)
            logger.info("Model loaded successfully")
            
            self.model.to(self.device)
            logger.info(f"Model moved to device: {self.device}")
            
            self.model.eval()
            logger.info("Model set to eval mode")
            
            if self.half_precision:
                # Apply half precision to the entire model
                self.model.half()
                
                # Force convert any remaining float buffers to half precision
                def convert_all_tensors_to_half(module):
                    for name, param in module.named_parameters():
                        if param.dtype == torch.float32:
                            logger.info(f"Converting parameter {name} to half precision")
                            param.data = param.data.half()
                    
                    for name, buf in module.named_buffers():
                        if buf.dtype == torch.float32:
                            logger.info(f"Converting buffer {name} to half precision")
                            module._buffers[name] = buf.half()
                    
                    for child in module.children():
                        convert_all_tensors_to_half(child)
                
                # Apply recursive conversion
                convert_all_tensors_to_half(self.model)
                
                torch.set_float32_matmul_precision('high')
                logger.info("Model converted to half precision with all tensors and buffers checked")

        except Exception as e:
            logger.error(f"Model loading failed with error: {str(e)}", exc_info=True)
            raise

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
        
        # First move to device
        input_tensor = input_tensor.to(self.device)
        
        # Check if model is loaded and in half precision
        if hasattr(self, 'model') and self.model is not None:
            # Match input tensor precision to model precision
            model_dtype = next(self.model.parameters()).dtype
            input_tensor = input_tensor.to(dtype=model_dtype)
        
        return input_tensor

    def predict(self, image: torch.Tensor) -> torch.Tensor:
        """Run RMBG 2.0 prediction"""
        with torch.no_grad(), torch.amp.autocast('cuda', enabled=self.half_precision):  # Fix deprecated autocast
            # Log input tensor details
            logger.info(f"Predict input tensor dtype: {image.dtype}")
            
            if self.half_precision:
                # Ensure input is half precision
                image = image.half()
                logger.info(f"After explicit half conversion dtype: {image.dtype}")
                
                # Verify model is in half precision
                for name, module in self.model.named_modules():
                    if hasattr(module, 'weight') and module.weight is not None:
                        if module.weight.dtype != torch.float16:
                            logger.warning(f"Module {name} weight has dtype {module.weight.dtype}")
                            module.weight.data = module.weight.data.half()
                    
                    # Don't convert integer buffers to half
                    for bname, buf in module.named_buffers():
                        if buf.dtype not in [torch.int64, torch.int32, torch.bool]:
                            if buf.dtype != torch.float16:
                                logger.warning(f"Converting buffer {bname} from {buf.dtype} to half")
                                module._buffers[bname] = buf.half()
            
            # Run prediction inside autocast context
            outputs = self.model(image)
            # Take last element of outputs list and apply sigmoid
            pred = outputs[-1].sigmoid().cpu()
            
        return pred[0].squeeze()

    def postprocess(self, pred: torch.Tensor, original_image: Image.Image) -> Image.Image:
        """Convert RMBG 2.0 output to final image"""
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(original_image.size)
        
        # Create copy of original image and set alpha
        result = original_image.copy()
        result.putalpha(mask)
        return result

    def __call__(self, image: Image.Image, enable_refinement: bool = False) -> Image.Image:
        """Process an image to remove background"""
        try:
            # Ensure model is loaded
            if not hasattr(self, 'model') or self.model is None:
                self.load_model()
            
            # Log model memory format
            logger.info(f"Model memory format: {next(self.model.parameters()).is_contiguous()}")
            
            # Preprocess
            input_tensor = self.preprocess(image)
            logger.info(f"After preprocess - tensor dtype: {input_tensor.dtype}, device: {input_tensor.device}")
            logger.info(f"Tensor requires grad: {input_tensor.requires_grad}")
            logger.info(f"Tensor memory format: {input_tensor.is_contiguous()}")
            
            # Force correct precision again right before prediction
            if self.half_precision and input_tensor.dtype != torch.float16:
                logger.info("Converting tensor to half precision")
                input_tensor = input_tensor.half()
            
            logger.info(f"Final tensor stats - dtype: {input_tensor.dtype}, shape: {input_tensor.shape}, device: {input_tensor.device}")
            
            # Predict
            pred = self.predict(input_tensor)
            
            # Postprocess
            result = self.postprocess(pred, image)
            return result
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            raise

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