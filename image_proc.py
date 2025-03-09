from PIL import Image
import numpy as np

def refine_foreground(image, mask):
    """Refine the foreground using the mask."""
    # Convert images to numpy arrays
    img_array = np.array(image)
    mask_array = np.array(mask)
    
    # Ensure mask is the same size as image
    if mask_array.shape[:2] != img_array.shape[:2]:
        mask = mask.resize((img_array.shape[1], img_array.shape[0]))
        mask_array = np.array(mask)
    
    # Create alpha channel
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    if img_array.shape[2] == 3:
        img_array = np.concatenate([img_array, np.ones((*img_array.shape[:2], 1)) * 255], axis=2)
    
    # Convert to RGBA if needed
    result = Image.fromarray(img_array.astype('uint8')).convert('RGBA')
    return result