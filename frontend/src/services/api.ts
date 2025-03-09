import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ModelInfo {
  loaded: boolean;
  metadata?: {
    device: string;
    half_precision: boolean;
    model_loaded: boolean;
    name: string;
    model_type: string;
    supports_refinement: boolean;
  };
}

export interface ModelsResponse {
  [key: string]: ModelInfo;
}

const api = {
  async removeBackground(file: File, model: string = 'rmbg2', enableRefinement: boolean = false) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(
      `${API_BASE_URL}/remove-background/?model=${model}&enable_refinement=${enableRefinement}`,
      formData,
      {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
  },

  async getModels(): Promise<ModelsResponse> {
    const response = await axios.get(`${API_BASE_URL}/models`);
    return response.data;
  },

  async loadModel(modelName: string) {
    const response = await axios.post(`${API_BASE_URL}/models/${modelName}/load`);
    return response.data;
  },

  async unloadModel(modelName: string) {
    const response = await axios.post(`${API_BASE_URL}/models/${modelName}/unload`);
    return response.data;
  },

  async checkHealth() {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  }
};

export default api;