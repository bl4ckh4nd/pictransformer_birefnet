import torch.cuda
import platform
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_cuda():
    """Test CUDA availability and initialization."""

    logger.info(f"CUDA available: {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        return False


if __name__ == "__main__":
    test_cuda()