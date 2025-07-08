import React from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import CssBaseline from '@mui/material/CssBaseline';
import UrlInput from './components/UrlInput';
import CanvasBoard from './components/CanvasBoard';
import { saveToSession, loadFromSession } from './utils/sessionStorage';

import './App.css';

function App() {
  const SESSION_KEY = 'wishlistProducts';
  const [products, setProducts] = React.useState([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    const saved = loadFromSession(SESSION_KEY);
    if (Array.isArray(saved)) setProducts(saved);
  }, []);

  // Fetch real product data from FastAPI backend
  const fetchProductData = async (url) => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8001/api/product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (!resp.ok) throw new Error('Failed to fetch product data');
      const data = await resp.json();
      return data;
    } catch (err) {
      alert('Error: ' + err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };


  const handleAddUrl = async (url) => {
    if (products.some((p) => p.url === url)) {
      alert("This product is already on your board.");
      return;
    }
    
    const newProduct = await fetchProductData(url);
    
    if (newProduct) {
      const updatedProducts = [newProduct, ...products];
      setProducts(updatedProducts);
      saveToSession(SESSION_KEY, updatedProducts);
    }
  };


  const handleRemoveProduct = (url) => {
    const updated = products.filter((p) => p.url !== url);
    setProducts(updated);
    saveToSession(SESSION_KEY, updated);
  };


  return (
    <>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Velora2 MVP
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 4 }}>
        {/* Main content area */}
        <Box sx={{ p: 2, minHeight: '60vh' }}>
          <Typography variant="h4" gutterBottom>
            Velora2 Canvas
          </Typography>
          <Typography variant="body1" sx={{ mb: 4 }}>
            Paste a product URL below. Your wishlist will appear in a Pinterest-style board. Data is saved in session storage.
          </Typography>
          <UrlInput onAddUrl={handleAddUrl} />
          <CanvasBoard products={products} onRemoveProduct={handleRemoveProduct} loading={loading} />
        </Box>
      </Container>
    </>
  );
}

export default App
