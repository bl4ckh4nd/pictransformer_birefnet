# VisionCut - Background Removal Tool

This project provides a web application for removing backgrounds from images using various deep learning models. It features a Python FastAPI backend powered by PyTorch and a React frontend.

## Features

*   **Background Removal:** Upload images and remove their backgrounds automatically.
*   **Multiple Models:** Choose from different background removal models (e.g., RMBG-2.0, BiRefNet).
*   **Model Refinement:** Option to enable post-processing refinement for supported models.
*   **Web Interface:** User-friendly React frontend for easy interaction.
*   **API:** FastAPI backend provides endpoints for background removal and model management.
*   **CUDA Acceleration:** Utilizes NVIDIA GPUs via PyTorch for faster processing if available.

## Technology Stack

*   **Backend:** Python, FastAPI, Uvicorn, PyTorch, Pillow
*   **Frontend:** React, TypeScript, Material UI, Axios

## Project Structure

.
├── downloaded_models/        # Default location for downloaded model files
├── frontend/                 # React frontend application
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── Dockerfile            # Frontend Docker build instructions
│   └── docker-entrypoint.sh  # Frontend container entrypoint script
│   └── ... (other frontend files)
├── models/                   # Model loading and registry logic
│   ├── registry.py
│   └── ... (model-specific files)
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile.backend        # Backend Docker build instructions
├── docker-compose.yml        # Docker Compose configuration
├── README.md                 # This file
├── run_backend.bat           # Windows script to run backend locally
├── run_backend.sh            # macOS/Linux script to run backend locally
├── run_frontend.bat          # Windows script to run frontend locally
├── run_frontend.sh           # macOS/Linux script to run frontend locally
└── ... (other project files)


## Setup

### Prerequisites

*   Python 3.8+ and Pip
*   Node.js and npm (or yarn)
*   (Optional but Recommended) NVIDIA GPU with CUDA drivers installed for GPU acceleration.

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd pictransformer_birefnet
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure your PyTorch version matches your CUDA setup if using GPU. You might need to install a specific PyTorch version from their website.*

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install Node dependencies:**
    ```bash
    npm install
    # or yarn install
    ```
3.  **(Optional) Configure API URLs:**
    Create a `.env.local` file in the `frontend` directory if you need to override the default API endpoint (e.g., if your backend runs on a different address/port). See `.env.development` for examples.

    ```env
    # frontend/.env.local
    REACT_APP_API_BASE_URL=http://localhost:8000
    REACT_APP_API_REMOVE_BG_URL=$REACT_APP_API_BASE_URL/remove-background
    REACT_APP_API_MODELS_URL=$REACT_APP_API_BASE_URL/models
    # ... add other URLs as needed
    ```

## Running the Application

You can run the application locally using the provided scripts/manual steps, or use Docker Compose for a containerized setup.

### Using Docker Compose (Recommended for Containerized Environment)

1.  **Prerequisites:** Docker and Docker Compose installed.
2.  **Build and Run:** From the project root directory, run:
    ```bash
    docker-compose up --build
    ```
    *   This will build the images for both the backend and frontend (if not already built) and start the services.
    *   The frontend will be accessible at [http://localhost:3000](http://localhost:3000).
    *   The backend API will be accessible at [http://localhost:8000](http://localhost:8000) (though the frontend is configured to talk to it via the internal Docker network name `backend`).
3.  **Stopping:** Press `Ctrl+C` in the terminal where `docker-compose up` is running. To remove the containers, run `docker-compose down`.

### Using Local Run Scripts (for Development)
### Using Run Scripts

*   **Windows:**
    *   Run Backend: `run_backend.bat`
    *   Run Frontend: `run_frontend.bat`
*   **macOS/Linux:**
    *   Run Backend: `chmod +x run_backend.sh && ./run_backend.sh`
    *   Run Frontend: `chmod +x run_frontend.sh && ./run_frontend.sh`

### Manual Steps

1.  **Run the Backend Server:**
    *   Make sure you are in the project root directory (`pictransformer_birefnet`) and your virtual environment is activated.
    *   Start the FastAPI server:
        ```bash
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ```
    *   The API will be available at `http://localhost:8000`.

2.  **Run the Frontend Development Server:**
    *   Navigate to the `frontend` directory in a **separate terminal**.
    *   Start the React app:
        ```bash
        npm start
        # or yarn start
        ```
    *   Open [http://localhost:3000](http://localhost:3000) in your browser.

## API Endpoints

*   `POST /remove-background/`: Upload an image file for background removal.
    *   Query Parameters: `model` (string), `enable_refinement` (boolean)
*   `GET /models`: List available models and their status.
*   `POST /models/{model_name}/load`: Load a specific model.
*   `POST /models/{model_name}/unload`: Unload a specific model.
*   `GET /models/{model_name}/info`: Get details about a model.
*   `GET /health`: Health check endpoint.

## Model Management

Models are defined in the `models/` directory and managed by `models/registry.py`. Models are downloaded on demand (or when explicitly loaded via the API) into the `downloaded_models/` directory (by default).



## Deployment


