import React from 'react';
import Box from '@mui/material/Box';
import Masonry from '@mui/lab/Masonry';
import Typography from '@mui/material/Typography';
import ProductCard from './product/ProductCard';

const CanvasBoard = ({ products, onRemoveProduct, loading }) => {
  if (loading) {
    return (
      <Box sx={{ width: '100%', minHeight: 200, py: 4 }}>
        <Typography variant="body1" align="center">Loading...</Typography>
      </Box>
    );
  }
  if (!products.length) {
    return (
      <Box sx={{ width: '100%', minHeight: 200, py: 4 }}>
        <Typography variant="body1" align="center" color="text.secondary">
          No products yet. Paste a URL above to get started!
        </Typography>
      </Box>
    );
  }
  return (
    <Box sx={{ width: '100%', minHeight: 200 }}>
      <Masonry columns={{ xs: 1, sm: 2, md: 3 }} spacing={2}>
        {products.map((product, idx) => (
          <ProductCard key={product.url || `${product.title || 'product'}-${idx}`}
            product={product} />
        ))}
      </Masonry>
    </Box>
  );
};

export default CanvasBoard;
