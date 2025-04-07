import React from 'react';
import {
  Box,
  Slider,
  IconButton,
  Typography,
  Stack,
  Button,
  Paper,
  Divider,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  RotateCcw,
  RotateCw,
  FlipHorizontal,
  FlipVertical,
  Sun,
  Contrast,
  Palette,
  RefreshCcw,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext'; // Import useLanguage

interface ImageTransformControlsProps {
  onRotate: (degrees: number) => void;
  onFlipHorizontal: () => void;
  onFlipVertical: () => void;
  onBrightnessChange: (value: number) => void;
  onContrastChange: (value: number) => void;
  onSaturationChange: (value: number) => void;
  onReset: () => void;
  brightness: number;
  contrast: number;
  saturation: number;
}

const ImageTransformControls: React.FC<ImageTransformControlsProps> = ({
  onRotate,
  onFlipHorizontal,
  onFlipVertical,
  onBrightnessChange,
  onContrastChange,
  onSaturationChange,
  onReset,
  brightness,
  contrast,
  saturation,
}) => {
  const theme = useTheme();
  const { t } = useLanguage(); // Get translation function
  
  return (
    <Paper 
      elevation={2} 
      sx={{ 
        width: '100%', 
        overflow: 'hidden',
        borderRadius: 2,
        transition: 'all 0.2s ease-in-out',
      }}
    >
      <Box 
        sx={{ 
          p: 2, 
          backgroundColor: theme.palette.mode === 'dark' 
            ? 'rgba(255,255,255,0.05)' 
            : 'rgba(0,0,0,0.02)',
          borderBottom: `1px solid ${theme.palette.divider}`
        }}
      >
        <Typography variant="subtitle1" fontWeight="medium">
          {t('imageAdjustments')}
        </Typography>
      </Box>
      
      <Box sx={{ p: 2 }}>
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            gap: 1, 
            alignItems: 'center',
            mb: 2,
            flexWrap: 'wrap'
          }}
        >
          <Tooltip title={t('rotateLeft')}>
            <IconButton 
              onClick={() => onRotate(-90)} 
              sx={{ 
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                borderRadius: 1.5,
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                }
              }}
            >
              <RotateCcw size={22} />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('rotateRight')}>
            <IconButton 
              onClick={() => onRotate(90)} 
              sx={{ 
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                borderRadius: 1.5,
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                }
              }}
            >
              <RotateCw size={22} />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('flipHorizontal')}>
            <IconButton 
              onClick={onFlipHorizontal} 
              sx={{ 
                backgroundColor: flipH => flipH ? theme.palette.primary.main + '20' : 
                  theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                borderRadius: 1.5,
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                }
              }}
            >
              <FlipHorizontal size={22} />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('flipVertical')}>
            <IconButton 
              onClick={onFlipVertical} 
              sx={{ 
                backgroundColor: flipV => flipV ? theme.palette.primary.main + '20' : 
                  theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                borderRadius: 1.5,
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                }
              }}
            >
              <FlipVertical size={22} />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('resetAllAdjustments')}>
            <Button 
              startIcon={<RefreshCcw size={18} />}
              onClick={onReset}
              variant="outlined"
              size="small"
              sx={{ 
                ml: { xs: 0, sm: 2 },
                mt: { xs: 1, sm: 0 },
                width: { xs: '100%', sm: 'auto' }
              }}
            >
              {t('resetAll')}
            </Button>
          </Tooltip>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Stack spacing={3} sx={{ px: { xs: 1, sm: 2 } }}>
          <Box>
            <Typography 
              gutterBottom 
              display="flex" 
              alignItems="center" 
              gap={1} 
              sx={{ color: brightness !== 0 ? theme.palette.primary.main : 'inherit', fontWeight: brightness !== 0 ? 500 : 400 }}
            >
              <Sun size={18} /> {t('brightness')} {brightness !== 0 && `(${brightness > 0 ? '+' : ''}${brightness}%)`}
            </Typography>
            <Slider
              value={brightness}
              min={-100}
              max={100}
              onChange={(_: Event, value: number | number[]) => onBrightnessChange(value as number)}
              valueLabelDisplay="auto"
              sx={{
                '& .MuiSlider-thumb': {
                  transition: 'transform 0.2s',
                  '&:hover, &.Mui-active': {
                    transform: 'scale(1.2)',
                  }
                }
              }}
            />
          </Box>
          
          <Box>
            <Typography 
              gutterBottom 
              display="flex" 
              alignItems="center" 
              gap={1}
              sx={{ color: contrast !== 0 ? theme.palette.primary.main : 'inherit', fontWeight: contrast !== 0 ? 500 : 400 }}
            >
              <Contrast size={18} /> {t('contrast')} {contrast !== 0 && `(${contrast > 0 ? '+' : ''}${contrast}%)`}
            </Typography>
            <Slider
              value={contrast}
              min={-100}
              max={100}
              onChange={(_: Event, value: number | number[]) => onContrastChange(value as number)}
              valueLabelDisplay="auto"
              sx={{
                '& .MuiSlider-thumb': {
                  transition: 'transform 0.2s',
                  '&:hover, &.Mui-active': {
                    transform: 'scale(1.2)',
                  }
                }
              }}
            />
          </Box>

          <Box>
            <Typography 
              gutterBottom 
              display="flex" 
              alignItems="center" 
              gap={1}
              sx={{ color: saturation !== 0 ? theme.palette.primary.main : 'inherit', fontWeight: saturation !== 0 ? 500 : 400 }}
            >
              <Palette size={18} /> {t('saturation')} {saturation !== 0 && `(${saturation > 0 ? '+' : ''}${saturation}%)`}
            </Typography>
            <Slider
              value={saturation}
              min={-100}
              max={100}
              onChange={(_: Event, value: number | number[]) => onSaturationChange(value as number)}
              valueLabelDisplay="auto"
              sx={{
                '& .MuiSlider-thumb': {
                  transition: 'transform 0.2s',
                  '&:hover, &.Mui-active': {
                    transform: 'scale(1.2)',
                  }
                }
              }}
            />
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
};

export default ImageTransformControls;