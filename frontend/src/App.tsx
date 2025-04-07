import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Link,
  Paper,
  Fade,
  Grow,
  useTheme,
  Divider,
  Backdrop,
} from '@mui/material';
import { Download, Image as ImageIcon, AlertTriangle } from 'lucide-react';
import ImageUpload from './components/ImageUpload';
import ModelSelector from './components/ModelSelector';
import ImageComparison from './components/ImageComparison';
import LanguageSwitcher from './components/LanguageSwitcher'; // Import LanguageSwitcher
import { useLanguage } from './contexts/LanguageContext'; // Import useLanguage
import api, { ModelsResponse } from './services/api';

function App() {
  const theme = useTheme();
  const { t } = useLanguage(); // Get translation function
  const [models, setModels] = useState<ModelsResponse>({});
  const [selectedModel, setSelectedModel] = useState('rmbg2');
  const [enableRefinement, setEnableRefinement] = useState(false);
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);

  // Add state for tracking transformations at the App level
  const [rotation, setRotation] = useState(0);
  const [flipH, setFlipH] = useState(false);
  const [flipV, setFlipV] = useState(false);
  const [brightness, setBrightness] = useState(0);
  const [contrast, setContrast] = useState(0);
  const [saturation, setSaturation] = useState(0);

  useEffect(() => {
    loadModels();
    
    // Mark initial loading complete after a short delay
    const timer = setTimeout(() => setInitialLoad(false), 800);
    
    // Cleanup function to revoke object URLs when component unmounts
    return () => {
      clearTimeout(timer);
      if (originalImage) URL.revokeObjectURL(originalImage);
      if (processedImage) URL.revokeObjectURL(processedImage);
    };
  }, []);

  const loadModels = async () => {
    try {
      const availableModels = await api.getModels();
      setModels(availableModels);
    } catch (err) {
      setError('Failed to load models. Please check if the backend server is running.');
    }
  };

  const handleModelChange = async (model: string) => {
    setSelectedModel(model);
    try {
      await api.loadModel(model);
      await loadModels(); // Refresh models to update status
    } catch (err) {
      setError('Failed to load model');
    }
  };

  const handleImageSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
    
    // Cleanup old URLs before creating new ones
    if (originalImage) URL.revokeObjectURL(originalImage);
    if (processedImage) URL.revokeObjectURL(processedImage);
    
    setProcessedImage(null);
    const imageUrl = URL.createObjectURL(file);
    setOriginalImage(imageUrl);

    // Reset all transformation states
    setRotation(0);
    setFlipH(false);
    setFlipV(false);
    setBrightness(0);
    setContrast(0);
    setSaturation(0);
  };

  const handleProcess = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    try {
      // Revoke old processed image URL if it exists
      if (processedImage) {
        URL.revokeObjectURL(processedImage);
      }
      
      const result = await api.removeBackground(selectedFile, selectedModel, enableRefinement);
      const processedImageUrl = URL.createObjectURL(result);
      setProcessedImage(processedImageUrl);
    } catch (err) {
      setError('Failed to process image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Update your handleDownload function to apply transformations
  const handleDownload = () => {
    if (processedImage) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // Set canvas size
        canvas.width = img.width;
        canvas.height = img.height;
        
        if (!ctx) return;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Apply transformations
        ctx.save();
        
        // Move to center point for transformations
        ctx.translate(canvas.width / 2, canvas.height / 2);
        
        // Apply rotation
        ctx.rotate((rotation * Math.PI) / 180);
        
        // Apply flips
        ctx.scale(flipH ? -1 : 1, flipV ? -1 : 1);
        
        // Draw the image (centered)
        ctx.drawImage(img, -img.width / 2, -img.height / 2, img.width, img.height);
        
        // Apply filters
        if (brightness !== 0 || contrast !== 0 || saturation !== 0) {
          // Create a temporary canvas for filter effects
          const tempCanvas = document.createElement('canvas');
          tempCanvas.width = canvas.width;
          tempCanvas.height = canvas.height;
          const tempCtx = tempCanvas.getContext('2d');
          
          if (tempCtx) {
            // Copy from main canvas to temp canvas
            tempCtx.drawImage(canvas, 0, 0);
            
            // Apply filters
            ctx.filter = `brightness(${100 + brightness}%) contrast(${100 + contrast}%) saturate(${100 + saturation}%)`;
            
            // Draw back to main canvas with filters
            ctx.drawImage(tempCanvas, -canvas.width / 2, -canvas.height / 2);
          }
        }
        
        ctx.restore();
        
        // Convert to blob and download
        canvas.toBlob((blob) => {
          if (!blob) return;
          
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = 'processed-image.png';
          document.body.appendChild(link);
          link.click();
          
          // Clean up - ONLY REMOVE ONCE
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }, 'image/png');
      };
      
      img.src = processedImage;
    }
  };

  // Handler functions for image transformations
  const handleRotate = (degrees: number) => {
    setRotation((prev) => (prev + degrees) % 360);
  };

  const handleFlipHorizontal = () => {
    setFlipH((prev) => !prev);
  };

  const handleFlipVertical = () => {
    setFlipV((prev) => !prev);
  };

  const handleReset = () => {
    setRotation(0);
    setFlipH(false);
    setFlipV(false);
    setBrightness(0);
    setContrast(0);
    setSaturation(0);
  };

  return (
    <>
      <Backdrop
        open={initialLoad}
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: theme.palette.background.paper,
          flexDirection: 'column', 
        }}
      >
        <CircularProgress color="primary" size={60} thickness={4} />
        <Typography variant="h6" mt={2}>Loading Background Removal Tool...</Typography>
      </Backdrop>
      
      <Container maxWidth="lg">
        <Fade in={!initialLoad} timeout={800}>
          <Box sx={{ my: 4, pt: 2 }}>
            {/* Add LanguageSwitcher to the top right */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <LanguageSwitcher />
            </Box>
            <Box 
              sx={{ 
                mb: 5, 
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Typography 
                variant="h3" 
                component="h1" 
                gutterBottom 
                fontWeight="bold"
                sx={{ 
                  background: theme.palette.mode === 'dark' 
                    ? 'linear-gradient(45deg, #8099ff 0%, #aecdff 100%)' 
                    : 'linear-gradient(45deg, #3455b5 0%, #5282ff 100%)',
                  backgroundClip: 'text',
                  textFillColor: 'transparent',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  letterSpacing: '-0.5px',
                }}
              >
                VisionCut {/* Set title directly */}
              </Typography>
              <Typography 
                variant="subtitle1" 
                color="textSecondary" 
                sx={{ 
                  maxWidth: '600px', 
                  mb: 2,
                  opacity: 0.8,
                }}
              >
                {t('appSubtitle')} {/* Translate subtitle */}
              </Typography>
              <Divider sx={{ width: '120px', my: 1 }} />
            </Box>
            
            {error && (
              <Grow in={!!error}>
                <Alert 
                  severity="error" 
                  sx={{ 
                    mb: 3,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                  icon={<AlertTriangle size={24} />}
                >
                  <Typography fontWeight={500}>{error}</Typography>
                </Alert>
              </Grow>
            )}

            <ModelSelector
              models={models}
              selectedModel={selectedModel}
              enableRefinement={enableRefinement}
              onModelChange={handleModelChange}
              onRefinementChange={setEnableRefinement}
            />

            <Box sx={{ mb: 3 }}>
              <ImageUpload onImageSelect={handleImageSelect} />
            </Box>

            {originalImage && (
              <Fade in={!!originalImage} timeout={500}>
                <Box 
                  sx={{ 
                    mb: 3, 
                    display: 'flex', 
                    gap: 2, 
                    justifyContent: 'center',
                    flexWrap: 'wrap',
                  }}
                >
                  <Button
                    variant="contained"
                    onClick={handleProcess}
                    disabled={loading}
                    sx={{ 
                      minWidth: 220,
                      py: 1.2,
                      px: 3,
                      borderRadius: 2,
                      fontWeight: 500,
                      fontSize: '1rem',
                      position: 'relative',
                      overflow: 'hidden',
                      transition: 'all 0.3s ease',
                      background: theme.palette.mode === 'dark' 
                        ? 'linear-gradient(45deg, #2845a8 0%, #4070e0 100%)' 
                        : 'linear-gradient(45deg, #3455b5 0%, #5282ff 100%)',
                      '&:hover': {
                        boxShadow: '0 6px 12px rgba(0, 0, 0, 0.2)',
                        transform: 'translateY(-2px)',
                      },
                      '&:active': {
                        transform: 'translateY(1px)',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
                      }
                    }}
                  >
                    {loading ? (
                      <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />
                    ) : (
                      <ImageIcon size={20} style={{ marginRight: '8px' }} />
                    )}
                    {loading ? t('processing') : t('removeBackground')} {/* Translate button */}
                  </Button>
                  
                  {processedImage && (
                    <Fade in={!!processedImage}>
                      <Button
                        variant="outlined"
                        onClick={handleDownload}
                        sx={{ 
                          minWidth: 200,
                          py: 1.2,
                          px: 3,
                          borderRadius: 2,
                          fontWeight: 500,
                          fontSize: '1rem',
                          borderWidth: 2,
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            borderWidth: 2,
                            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
                            transform: 'translateY(-2px)',
                          }
                        }}
                        startIcon={<Download size={20} />}
                      >
                        {t('downloadResult')} {/* Translate button */}
                      </Button>
                    </Fade>
                  )}
                </Box>
              </Fade>
            )}

            <ImageComparison
              originalImage={originalImage}
              processedImage={processedImage}
              // Pass transformation values and handlers
              rotation={rotation}
              flipH={flipH}
              flipV={flipV}
              brightness={brightness}
              contrast={contrast}
              saturation={saturation}
              onRotate={handleRotate}
              onFlipHorizontal={handleFlipHorizontal}
              onFlipVertical={handleFlipVertical}
              onBrightnessChange={setBrightness}
              onContrastChange={setContrast}
              onSaturationChange={setSaturation}
              onReset={handleReset}
            />
            
            <Box 
              component={Paper} 
              elevation={1} 
              sx={{ 
                mt: 4, 
                p: 2, 
                textAlign: 'center', 
                borderRadius: 2,
                opacity: 0.7,
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255,255,255,0.03)' 
                  : 'rgba(0,0,0,0.02)',
              }}
            >
              <Typography variant="body2" color="textSecondary">
                {t('footerText')} {/* Translate footer */}
              </Typography>
            </Box>
          </Box>
        </Fade>
      </Container>
    </>
  );
}

export default App;
