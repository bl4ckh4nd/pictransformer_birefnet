import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Box,
  Typography,
  Chip,
  Paper,
  useTheme,
  Zoom,
  Tooltip,
} from '@mui/material';
import { Check, HelpCircle, Zap } from 'lucide-react';
import { ModelsResponse } from '../services/api';

interface ModelSelectorProps {
  models: ModelsResponse;
  selectedModel: string;
  enableRefinement: boolean;
  onModelChange: (model: string) => void;
  onRefinementChange: (enabled: boolean) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  enableRefinement,
  onModelChange,
  onRefinementChange,
}) => {
  const theme = useTheme();
  const currentModel = models[selectedModel];
  const supportsRefinement = currentModel?.metadata?.supports_refinement || false;

  return (
    <Paper 
      elevation={2} 
      sx={{ 
        p: 2, 
        mb: 3, 
        borderRadius: 2,
        background: theme.palette.mode === 'dark' 
          ? 'linear-gradient(145deg, rgba(30,30,30,0.8) 0%, rgba(40,40,40,0.4) 100%)' 
          : 'linear-gradient(145deg, rgba(250,250,250,0.8) 0%, rgba(255,255,255,0.4) 100%)'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Zap 
          size={20} 
          color={theme.palette.primary.main} 
          strokeWidth={2} 
          style={{ marginRight: 8 }}
        />
        <Typography variant="h6" fontWeight={500} fontSize={18}>
          Model Selection
        </Typography>
      </Box>
      
      <FormControl 
        fullWidth 
        variant="outlined" 
        sx={{ 
          mb: 2,
          '& .MuiOutlinedInput-root': {
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            },
            '&.Mui-focused': {
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
            }
          }
        }}
      >
        <InputLabel id="model-select-label" sx={{ background: theme.palette.background.paper, px: 1 }}>
          Model
        </InputLabel>
        <Select
          labelId="model-select-label"
          id="model-select"
          value={selectedModel}
          label="Model"
          onChange={(e) => onModelChange(e.target.value)}
        >
          {Object.entries(models).map(([key, model]) => (
            <MenuItem 
              key={key} 
              value={key}
              sx={{
                py: 1.5,
                transition: 'all 0.2s ease',
                borderLeft: selectedModel === key ? `4px solid ${theme.palette.primary.main}` : '4px solid transparent',
                '&:hover': {
                  backgroundColor: theme.palette.action.hover,
                }
              }}
            >
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between', 
                width: '100%',
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {selectedModel === key && (
                    <Zoom in={true} style={{ transitionDelay: '150ms' }}>
                      <Check size={18} color={theme.palette.primary.main} />
                    </Zoom>
                  )}
                  <Typography fontWeight={selectedModel === key ? 500 : 400}>
                    {model.metadata?.name || key}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {model.metadata?.supports_refinement && (
                    <Tooltip title="Supports image refinement">
                      <Chip 
                        label="Refinement" 
                        size="small" 
                        variant="outlined" 
                        color="info"
                      />
                    </Tooltip>
                  )}
                  
                  {model.loaded && (
                    <Tooltip title="Model is loaded and ready to use">
                      <Chip
                        label="Loaded"
                        color="success"
                        size="small"
                        sx={{ 
                          fontWeight: 500,
                          animation: model.loaded ? 'fadeIn 0.5s' : 'none',
                          '@keyframes fadeIn': {
                            '0%': { opacity: 0 },
                            '100%': { opacity: 1 }
                          }
                        }}
                      />
                    </Tooltip>
                  )}
                </Box>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {supportsRefinement && (
        <Box 
          sx={{
            display: 'flex',
            alignItems: 'center',
            p: 1.5,
            borderRadius: 1.5,
            backgroundColor: theme.palette.mode === 'dark' 
              ? 'rgba(255,255,255,0.05)' 
              : 'rgba(0,0,0,0.02)',
          }}
        >
          <FormControlLabel
            control={
              <Switch
                checked={enableRefinement}
                onChange={(e) => onRefinementChange(e.target.checked)}
                color="primary"
                sx={{
                  '& .MuiSwitch-switchBase.Mui-checked': {
                    color: theme.palette.primary.main
                  },
                  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                    backgroundColor: theme.palette.primary.main
                  }
                }}
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography sx={{ mr: 1 }}>Enable refinement</Typography>
                <Tooltip title="Apply additional processing to improve edge quality">
                  <HelpCircle size={16} color={theme.palette.text.secondary} />
                </Tooltip>
              </Box>
            }
          />
        </Box>
      )}
    </Paper>
  );
};

export default ModelSelector;