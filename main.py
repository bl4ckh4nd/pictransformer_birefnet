import io
import time
import logging
import platform
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
import torch
from PIL import Image
from models.birefnet import BiRefNet
from image_proc import refine_foreground
from torchvision import transforms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Method: {request.method} Path: {request.url.path} "
            f"Status: {response.status_code} Duration: {process_time:.2f}s"
        )
        return response

app = FastAPI(title="Background Removal API")
app.add_middleware(RequestLoggingMiddleware)

# Initialize CUDA and model
def setup_cuda():
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"CUDA version: {torch.version.cuda if torch.cuda.is_available() else 'Not available'}")
    
    if not torch.cuda.is_available():
        logger.error("CUDA is not available. This could be due to:")
        logger.error("1. No NVIDIA GPU present")
        logger.error("2. NVIDIA drivers not installed")
        logger.error("3. PyTorch not built with CUDA support")
        logger.error("4. CUDA toolkit not installed")
        return 'cpu'
    
    try:
        n_devices = torch.cuda.device_count()
        logger.info(f"Number of CUDA devices: {n_devices}")
        
        for i in range(n_devices):
            props = torch.cuda.get_device_properties(i)
            logger.info(f"GPU {i}: {props.name}")
            logger.info(f"  Memory: {props.total_memory / 1024**3:.2f}GB")
            logger.info(f"  CUDA Capability: {props.major}.{props.minor}")
        
        device = 'cuda'
        torch.set_float32_matmul_precision('high')
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.enabled = True
        
        # Test CUDA with a small tensor operation
        test_tensor = torch.rand(1).cuda()
        logger.info("CUDA test successful - tensor operation completed")
        
        return device
    except Exception as e:
        logger.error(f"Error initializing CUDA: {str(e)}")
        return 'cpu'

device = setup_cuda()
logger.info(f"Final device selection: {device}")

try:
    birefnet = BiRefNet.from_pretrained('zhengpeng7/BiRefNet')
    birefnet.to(device)
    birefnet.eval()
    
    if device == 'cuda':
        birefnet.half()
        torch.cuda.empty_cache()
        logger.info(f"Model loaded on GPU. Memory allocated: {torch.cuda.memory_allocated()/1024**2:.2f}MB")
        logger.info(f"Max memory allocated: {torch.cuda.max_memory_allocated()/1024**2:.2f}MB")
        logger.info(f"Memory cached: {torch.cuda.memory_reserved()/1024**2:.2f}MB")
    
    logger.info("BiRefNet model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load BiRefNet model: {str(e)}")
    logger.error(f"Stack trace:", exc_info=True)
    raise

def extract_object(image: Image.Image):
    try:
        # Ensure image is in RGB mode
        if image.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            # Paste the image using itself as mask
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Data settings
        transform_image = transforms.Compose([
            transforms.Resize((1024, 1024)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        input_images = transform_image(image).unsqueeze(0)
        
        # Ensure GPU usage and half precision
        if device == 'cuda':
            input_images = input_images.cuda().half()
        else:
            input_images = input_images.to(device)

        # Prediction
        with torch.no_grad():
            torch.cuda.empty_cache()  # Clear GPU memory before inference
            preds = birefnet(input_images)[-1].sigmoid().cpu()
            
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        
        # Apply refinement
        image_masked = refine_foreground(image, pred_pil)
        image_masked.putalpha(pred_pil.resize(image.size))
        
        # Clear GPU memory after processing
        if device == 'cuda':
            torch.cuda.empty_cache()
            
        return image_masked
    except Exception as e:
        logger.error(f"Error in extract_object: {str(e)}")
        raise

@app.post("/remove-background/")
async def remove_background(file: UploadFile = File(...)):
    logger.info(f"Processing image: {file.filename}")
    start_time = time.time()
    
    # Validate content type
    if not file.content_type.startswith('image/'):
        logger.error(f"Invalid content type: {file.content_type}")
        return {"error": "File must be an image"}, 400
    
    try:
        # Read and process the image
        image_data = await file.read()
        if not image_data:
            logger.error("Received empty file")
            return {"error": "Empty file received"}, 400
            
        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            return {"error": "Invalid image format"}, 400
        
        # Convert to RGB if not already
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Process the image
        result_image = extract_object(image)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        process_time = time.time() - start_time
        logger.info(f"Successfully processed {file.filename} in {process_time:.2f}s")
        
        headers = {
            'Content-Type': 'image/png',
            'Content-Disposition': f'attachment; filename="processed_{file.filename}"'
        }
        
        return StreamingResponse(img_byte_arr, media_type="image/png", headers=headers)
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {str(e)}")
        return {"error": str(e)}, 500

@app.get("/")
async def root():
    return {"message": "Background Removal API is running. Send POST request to /remove-background/ with an image file"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Background Removal API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)