@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing PyTorch with CUDA support...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

echo Installing other requirements...
pip install -r requirements.txt

echo Testing CUDA availability...
python test_gpu.py

echo Done! You can now run the FastAPI server with: python main.py