import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { saveToSession, loadFromSession, removeFromSession } from '../utils/sessionStorage';

const SESSION_KEY = 'sampleFormData';

const SampleForm = () => {
  const [form, setForm] = useState({ name: '', email: '' });
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const saved = loadFromSession(SESSION_KEY);
    if (saved) setForm(saved);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const updated = { ...form, [name]: value };
    setForm(updated);
    saveToSession(SESSION_KEY, updated);
    setSubmitted(false);
  };

  const handleClear = () => {
    setForm({ name: '', email: '' });
    removeFromSession(SESSION_KEY);
    setSubmitted(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    saveToSession(SESSION_KEY, form);
    setSubmitted(true);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 400 }}>
      <Typography variant="h6">Sample Form (Session Storage)</Typography>
      <TextField
        label="Name"
        name="name"
        value={form.name}
        onChange={handleChange}
        autoComplete="off"
        required
      />
      <TextField
        label="Email"
        name="email"
        value={form.email}
        onChange={handleChange}
        autoComplete="off"
        type="email"
        required
      />
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button type="submit" variant="contained">Save</Button>
        <Button variant="outlined" onClick={handleClear}>Clear</Button>
      </Box>
      {submitted && (
        <Typography variant="body2" color="success.main">Saved to session storage!</Typography>
      )}
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle2">Current Data:</Typography>
        <Typography variant="body2">Name: {form.name || '-'}</Typography>
        <Typography variant="body2">Email: {form.email || '-'}</Typography>
      </Box>
    </Box>
  );
};

export default SampleForm;
