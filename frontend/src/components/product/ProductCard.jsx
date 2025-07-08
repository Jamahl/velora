import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

// Helper to format price with currency
const formatPrice = (price, currency) => {
  if (price == null) return '';
  const numericPrice = parseFloat(price);
  if (isNaN(numericPrice)) return '';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD', // Default to USD if no currency is provided
  }).format(numericPrice);
};

const ProductCard = ({ product }) => {
  const { title, price, currency, image_url, site_name, url } = product;

  return (
    <Card 
      sx={{
        borderRadius: 4, 
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 20px rgba(0,0,0,0.12)',
        },
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ pt: '100%', position: 'relative', overflow: 'hidden' }}>
        <Box
          component="img"
          src={image_url || 'https://via.placeholder.com/400'}
          alt={title || 'Product Image'}
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover', // Ensures the image covers the box, cropping as needed
          }}
        />
      </Box>
      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2 }}>
        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ textTransform: 'uppercase', letterSpacing: '0.5px', mb: 1 }}
        >
          {site_name || 'Retailer'}
        </Typography>
        <Link href={url} target="_blank" rel="noopener" underline="none" color="inherit">
          <Typography 
            variant="subtitle1" 
            component="h2" 
            sx={{
              fontWeight: 600,
              mb: 1,
              flexGrow: 1,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              minHeight: '2.5em', // Reserve space for two lines
            }}
          >
            {title || 'Untitled Product'}
          </Typography>
        </Link>
        <Box sx={{ mt: 'auto', pt: 1 }}>
          <Typography variant="h6" component="p" sx={{ fontWeight: 700 }}>
            {formatPrice(price, currency)}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ProductCard;
