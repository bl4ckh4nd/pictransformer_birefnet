import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, Box, Typography, useTheme, SelectChangeEvent } from '@mui/material';
import { Languages } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { translations, Language } from '../translations';

const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage, t } = useLanguage();
  const theme = useTheme();

  const handleLanguageChange = (event: SelectChangeEvent) => {
    setLanguage(event.target.value as Language);
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
       <Languages size={20} color={theme.palette.text.secondary} />
      <FormControl variant="standard" sx={{ minWidth: 120 }}>
        <InputLabel id="language-select-label">{t('language')}</InputLabel>
        <Select
          labelId="language-select-label"
          id="language-select"
          value={language}
          onChange={handleLanguageChange}
          label={t('language')}
        >
          {Object.keys(translations).map((langCode) => (
            <MenuItem key={langCode} value={langCode}>
              {/* Use the specific key for the language name ('english', 'german') */}
              {langCode === 'en' ? translations.en.english : langCode === 'de' ? translations.de.german : langCode}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default LanguageSwitcher;