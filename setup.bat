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

echo Installing Modal CLI...
pip install -U modal-client

echo.
echo Logging in to Modal (browser will open)...
modal token new

echo.
echo Deploying Modal application...
modal deploy modal_api.py

echo.
echo ========================================
echo Deployment Steps:
echo 1. Copy the Modal deployment URL from above
echo 2. Create .env.production in frontend directory with:
echo NEXT_PUBLIC_API_URL=your-modal-url
echo 3. Deploy frontend to Vercel:
echo    cd frontend ^& vercel
echo ========================================