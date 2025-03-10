import os
import torch
import logging
from PIL import Image
from transformers import AutoModelForImageSegmentation, AutoImageProcessor
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_load_rmbg():
    """Test loading RMBG model directly"""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    
    # Try with different model IDs
    model_ids = [
        "briaai/RMBG-1.4",
        "cerspense/zeroscope_v2_576w",  # Test with a different known working model
    ]
    
    for model_id in model_ids:
        logger.info(f"Attempting to load model: {model_id}")
        try:
            # Method 1: Direct loading
            logger.info(f"Method 1: Loading directly with AutoModelForImageSegmentation")
            model = AutoModelForImageSegmentation.from_pretrained(
                model_id, 
                trust_remote_code=True
            )
            logger.info(f"Successfully loaded {model_id} with Method 1!")
            return model
        except Exception as e:
            logger.error(f"Method 1 failed for {model_id}: {str(e)}")
        
        try:
            # Method 2: Using manual downloads
            logger.info(f"Method 2: Attempting manual file download")
            
            # Create a local directory for the model
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "custom")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Download model files manually
            config_file = hf_hub_download(repo_id=model_id, filename="config.json", cache_dir=cache_dir)
            model_file = hf_hub_download(repo_id=model_id, filename="pytorch_model.bin", cache_dir=cache_dir)
            
            logger.info(f"Downloaded config: {config_file}")
            logger.info(f"Downloaded model: {model_file}")
            
            # Load model from local files
            model_dir = os.path.dirname(config_file)
            logger.info(f"Loading from directory: {model_dir}")
            model = AutoModelForImageSegmentation.from_pretrained(model_dir)
            logger.info(f"Successfully loaded {model_id} with Method 2!")
            return model
        except Exception as e:
            logger.error(f"Method 2 failed for {model_id}: {str(e)}")
            
    logger.error("All loading attempts failed")
    return None

def process_sample_image(model):
    """Process a sample image if model loaded successfully"""
    if model is None:
        logger.error("No model available for inference")
        return
    
    try:
        # Try to load an image processor for the model
        processor = AutoImageProcessor.from_pretrained("briaai/RMBG-1.4", trust_remote_code=True)
        
        # Create a test image (alternatively, load one from disk)
        test_image = Image.new('RGB', (512, 512), color=(255, 255, 255))
        
        # Process image
        inputs = processor(test_image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        
        logger.info(f"Successfully ran inference! Output shape: {outputs.logits.shape}")
    except Exception as e:
        logger.error(f"Error processing sample image: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting RMBG model test")
    
    # Print Python and PyTorch versions for diagnostics
    import sys
    logger.info(f"Python version: {sys.version}")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    # Try to load the transformers module to check its version
    try:
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
    except ImportError:
        logger.error("Transformers library not found")
    
    # Try loading the model
    model = test_load_rmbg()
    
    # If model loaded, try processing an image
    if model:
        process_sample_image(model)
    
    logger.info("Test complete")