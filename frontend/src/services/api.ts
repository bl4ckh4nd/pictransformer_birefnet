import axios from 'axios';

export interface ModelsResponse {
  [key: string]: {
    loaded: boolean;
    metadata?: any;
  };
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = {
  async getModels(): Promise<ModelsResponse> {
    try {
      const response = await axios.get(`${API_BASE_URL}/models`);
      return response.data.models || {};
    } catch (error) {
      console.error('Error fetching models:', error);
      throw error;
    }
  },

  async loadModel(modelName: string): Promise<void> {
    try {
      await axios.post(`${API_BASE_URL}/models/${modelName}/load`);
    } catch (error) {
      console.error(`Error loading model ${modelName}:`, error);
      throw error;
    }
  },

  async removeBackground(
    file: File, 
    modelName: string = 'rmbg2',
    enableRefinement: boolean = false
  ): Promise<Blob> {
    try {
      const base64 = await fileToBase64(file);
      const base64Data = base64.split(',')[1];
      
      const response = await axios.post(
        `${API_BASE_URL}/remove-background`,
        {
          image: base64Data,
          model: modelName,
          enable_refinement: enableRefinement
        },
        {
          timeout: 120000,
        }
      );
      
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      const imgBlob = base64ToBlob(
        response.data.processed_image,
        'image/png'
      );
      
      return imgBlob;
    } catch (error) {
      console.error('Error removing background:', error);
      throw error;
    }
  }
};

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = error => reject(error);
  });
}

function base64ToBlob(base64: string, mimeType: string): Blob {
  const byteCharacters = atob(base64);
  const byteArrays = [];
  
  for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
    const slice = byteCharacters.slice(offset, offset + 1024);
    const byteNumbers = new Array(slice.length);
    
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }
  
  return new Blob(byteArrays, { type: mimeType });
}

export default api;