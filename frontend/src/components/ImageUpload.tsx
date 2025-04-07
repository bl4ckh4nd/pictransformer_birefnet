import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper, useTheme, Fade } from '@mui/material';
import { UploadCloud, Image } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext'; // Import useLanguage

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ onImageSelect }) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const { t } = useLanguage(); // Get translation function
  
  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp']
    },
    maxFiles: 1,
    onDrop: files => {
      if (files.length > 0) {
        onImageSelect(files[0]);
      }
    }
  });

  const getBorderColor = () => {
    if (isDragAccept) return theme.palette.success.main;
    if (isDragReject) return theme.palette.error.main;
    if (isDragActive || isHovered) return theme.palette.primary.main;
    return theme.palette.divider;
  };

  return (
    <Fade in={true} timeout={800}>
      <Paper
        {...getRootProps()}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        sx={{
          p: 4,
          textAlign: 'center',
          backgroundColor: isDragActive 
            ? theme.palette.mode === 'dark'
              ? 'rgba(255,255,255,0.05)'
              : 'rgba(0,0,0,0.02)'
            : theme.palette.background.paper,
          border: '2px dashed',
          borderColor: getBorderColor(),
          borderRadius: 2,
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            backgroundColor: theme.palette.mode === 'dark'
              ? 'rgba(255,255,255,0.05)'
              : 'rgba(0,0,0,0.02)',
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows[3],
          }
        }}
      >
        <input {...getInputProps()} />
        
        {isDragActive && (
          <Box 
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(0,0,0,0.3)' 
                : 'rgba(255,255,255,0.7)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 2,
              animation: 'pulse 1.5s infinite',
              '@keyframes pulse': {
                '0%': { opacity: 0.7 },
                '50%': { opacity: 0.9 },
                '100%': { opacity: 0.7 }
              }
            }}
          >
            <UploadCloud 
              size={56} 
              color={isDragAccept 
                ? theme.palette.success.main 
                : isDragReject 
                  ? theme.palette.error.main 
                  : theme.palette.primary.main
              } 
              strokeWidth={1.5}
            />
            <Typography variant="h6" sx={{ mt: 2, fontWeight: 500 }}>
              {isDragAccept 
                ? t('dropToUpload')
                : isDragReject
                  ? t('unsupportedFileType')
                  : t('dropFilesHere')
              }
            </Typography>
          </Box>
        )}
        
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Box 
            sx={{ 
              mb: 2, 
              display: 'flex', 
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255,255,255,0.05)' 
                  : 'rgba(0,0,0,0.03)',
                transition: 'all 0.3s ease',
                transform: isHovered ? 'scale(1.1)' : 'scale(1)',
              }}
            >
              <Image 
                size={40} 
                color={theme.palette.primary.main} 
                strokeWidth={1.5}
                style={{ 
                  transition: 'all 0.3s ease', 
                  transform: isHovered ? 'translateY(-5px)' : 'translateY(0)' 
                }}
              />
            </Box>
          </Box>
          <Typography variant="h6" gutterBottom fontWeight={500}>
            {isDragActive ? t('dropImageHere') : t('uploadImage')}
          </Typography>
          <Typography 
            variant="body2" 
            color="textSecondary"
            sx={{
              maxWidth: '80%',
              mx: 'auto',
              opacity: 0.8
            }}
          >
            {t('dragDropOrClick')}
          </Typography>
          <Typography 
            variant="caption" 
            color="textSecondary" 
            sx={{ 
              display: 'block', 
              mt: 1,
              opacity: 0.6 
            }}
          >
            {t('supportedFormats')}
          </Typography>
        </Box>
      </Paper>
    </Fade>
  );
};

export default ImageUpload;