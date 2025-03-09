import React, { useState } from 'react';
import { Box, Paper, Typography, Fade, useTheme, useMediaQuery } from '@mui/material';
import ImageTransformControls from './ImageTransformControls';

interface ImageComparisonProps {
  originalImage: string | null;
  processedImage: string | null;
}

const ImageComparison: React.FC<ImageComparisonProps> = ({
  originalImage,
  processedImage,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [rotation, setRotation] = useState(0);
  const [flipH, setFlipH] = useState(false);
  const [flipV, setFlipV] = useState(false);
  const [brightness, setBrightness] = useState(0);
  const [contrast, setContrast] = useState(0);
  const [saturation, setSaturation] = useState(0);

  const imageStyle = {
    maxWidth: '100%',
    transform: `
      rotate(${rotation}deg)
      scaleX(${flipH ? -1 : 1})
      scaleY(${flipV ? -1 : 1})
    `,
    filter: `
      brightness(${100 + brightness}%)
      contrast(${100 + contrast}%)
      saturate(${100 + saturation}%)
    `,
    transition: 'transform 0.3s ease, filter 0.3s ease',
  };

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
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      gap: 3,
      mt: 3
    }}>
      <Box sx={{ 
        display: 'flex', 
        gap: 3, 
        flexDirection: isMobile ? 'column' : 'row',
        width: '100%',
        justifyContent: 'center' 
      }}>
        {originalImage && (
          <Fade in={!!originalImage} timeout={500}>
            <Paper 
              elevation={3} 
              sx={{ 
                p: 0, 
                flex: 1, 
                minWidth: 280,
                overflow: 'hidden',
                borderRadius: 2,
                transition: 'box-shadow 0.3s',
                '&:hover': {
                  boxShadow: theme.shadows[6]
                }
              }}
            >
              <Box sx={{
                p: 2, 
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                borderBottom: `1px solid ${theme.palette.divider}`
              }}>
                <Typography variant="subtitle1" fontWeight="medium">
                  Original
                </Typography>
              </Box>
              <Box sx={{ p: 2 }}>
                <Box
                  component="img"
                  src={originalImage}
                  alt="Original"
                  sx={{
                    width: '100%',
                    height: 'auto',
                    maxHeight: 500,
                    objectFit: 'contain',
                    borderRadius: 1,
                  }}
                />
              </Box>
            </Paper>
          </Fade>
        )}
        {processedImage && (
          <Fade in={!!processedImage} timeout={800}>
            <Paper 
              elevation={3} 
              sx={{ 
                p: 0, 
                flex: 1, 
                minWidth: 280,
                overflow: 'hidden',
                borderRadius: 2,
                transition: 'box-shadow 0.3s',
                '&:hover': {
                  boxShadow: theme.shadows[6]
                }
              }}
            >
              <Box sx={{
                p: 2, 
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                borderBottom: `1px solid ${theme.palette.divider}`
              }}>
                <Typography variant="subtitle1" fontWeight="medium">
                  Background Removed
                </Typography>
              </Box>
              <Box sx={{ p: 2 }}>
                <Box
                  component="img"
                  src={processedImage}
                  alt="Processed"
                  sx={{
                    width: '100%',
                    maxHeight: 500,
                    objectFit: 'contain',
                    borderRadius: 1,
                    background: `
                      repeating-conic-gradient(
                        ${theme.palette.mode === 'dark' ? '#333' : '#f0f0f0'} 0% 25%, 
                        ${theme.palette.mode === 'dark' ? '#444' : '#ffffff'} 0% 50%
                      )
                      50% / 20px 20px
                    `,
                    ...imageStyle,
                  }}
                />
              </Box>
            </Paper>
          </Fade>
        )}
      </Box>
      
      {processedImage && (
        <Fade in={!!processedImage} timeout={1000}>
          <Box sx={{ width: '100%', maxWidth: 800 }}>
            <ImageTransformControls
              onRotate={handleRotate}
              onFlipHorizontal={handleFlipHorizontal}
              onFlipVertical={handleFlipVertical}
              onBrightnessChange={setBrightness}
              onContrastChange={setContrast}
              onSaturationChange={setSaturation}
              onReset={handleReset}
              brightness={brightness}
              contrast={contrast}
              saturation={saturation}
            />
          </Box>
        </Fade>
      )}
    </Box>
  );
};

export default ImageComparison;