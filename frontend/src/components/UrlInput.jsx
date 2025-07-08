import React, { useState } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import InputAdornment from '@mui/material/InputAdornment';
import LinkIcon from '@mui/icons-material/Link';

const UrlInput = ({ onAddUrl }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validateUrl = (value) => {
    try {
      // Basic URL validation
      const parsed = new URL(value);
      return parsed.protocol.startsWith('http');
    } catch (e) {
      return false;
    }
  };

  const handleChange = (e) => {
    setUrl(e.target.value);
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validateUrl(url)) {
      setError('Enter a valid URL (http/https)');
      return;
    }
    onAddUrl(url.trim());
    setUrl('');
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2, mb: 4 }}>
      <TextField
        label="Paste product URL"
        value={url}
        onChange={handleChange}
        error={!!error}
        helperText={error}
        fullWidth
        size="small"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <LinkIcon />
            </InputAdornment>
          ),
        }}
        autoFocus
      />
      <Button type="submit" variant="contained" sx={{ minWidth: 120 }}>
        Add
      </Button>
    </Box>
  );
};

export default UrlInput;
