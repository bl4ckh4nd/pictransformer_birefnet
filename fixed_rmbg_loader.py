import os
import torch
import logging
from PIL import Image
from transformers import AutoConfig, AutoModelForImageSegmentation
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_model_from_path():
    """Load the RMBG model using explicit path after manual download"""
    try:
        # Create a local directory for the model
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "custom")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Model ID
        model_id = "briaai/RMBG-1.4"
        
        # Download model files manually
        logger.info(f"Downloading model files for {model_id}")
        config_file = hf_hub_download(repo_id=model_id, filename="config.json", cache_dir=cache_dir)
        model_file = hf_hub_download(repo_id=model_id, filename="pytorch_model.bin", cache_dir=cache_dir)
        
        # Also download any needed custom modeling files
        try:
            modeling_file = hf_hub_download(repo_id=model_id, filename="modeling.py", cache_dir=cache_dir)
            logger.info(f"Downloaded custom modeling file: {modeling_file}")
        except Exception as e:
            logger.info(f"No custom modeling file found or needed: {e}")
        
        logger.info(f"Downloaded config: {config_file}")
        logger.info(f"Downloaded model: {model_file}")
        
        # Get model directory
        model_dir = os.path.dirname(config_file)
        logger.info(f"Loading from directory: {model_dir}")
        
        # Load model with trust_remote_code=True
        model = AutoModelForImageSegmentation.from_pretrained(
            model_dir,
            trust_remote_code=True,  # Critical for models with custom code
            local_files_only=True    # Don't try to download again
        )
        
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)
        model.eval()
        
        logger.info(f"Model successfully loaded and moved to {device}")
        return model
    
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        return None

def test_inference(model):
    """Test inference with a simple image"""
    if model is None:
        logger.error("No model available for testing")
        return
    
    try:
        # Create a test image
        logger.info("Creating test image")
        test_img = Image.new('RGB', (512, 512), color=(255, 0, 0))
        
        # Basic preprocessing (you might need to adjust this based on model requirements)
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.Resize((1024, 1024)),  # RMBG likely expects 1024x1024
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        img_tensor = transform(test_img).unsqueeze(0)
        device = next(model.parameters()).device
        img_tensor = img_tensor.to(device)
        
        # Run inference
        logger.info("Running inference")
        with torch.no_grad():
            output = model(img_tensor)
        
        # Check output
        logger.info(f"Output has logits: {'logits' in output}")
        if hasattr(output, 'logits'):
            logger.info(f"Output logits shape: {output.logits.shape}")
        
        logger.info("Inference test completed successfully")
    
    except Exception as e:
        logger.error(f"Inference error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("=== RMBG Model Loader ===")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    # Import and show transformers version
    import transformers
    logger.info(f"Transformers version: {transformers.__version__}")
    
    # Load the model
    logger.info("Loading model...")
    model = load_model_from_path()
    
    if model is not None:
        logger.info("Model loaded, testing inference...")
        test_inference(model)
        logger.info("Using this model with your application:")
        logger.info("1. First download the model files as done in this script")
        logger.info("2. Load from the local path with trust_remote_code=True")
        logger.info("3. Use the model as usual")
    else:
        logger.error("Failed to load model")