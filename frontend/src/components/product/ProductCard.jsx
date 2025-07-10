import React, { useState } from 'react';

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
  const { title, price, discounted_price, discount_percentage, brand, product_description, currency, image_url, site_name, url } = product;

  return (
    <div className="w-full max-w-xs bg-white shadow-md rounded-lg border border-gray-200 flex flex-col p-3 mx-auto">
      <div className="aspect-square bg-gray-100 rounded-md overflow-hidden mb-2 flex items-center justify-center">
        <img
          src={image_url && image_url.startsWith('http') ? image_url : 'https://via.placeholder.com/400'}
          alt={title || 'Product Image'}
          className="object-cover w-full h-full min-h-[120px]"
          loading="lazy"
          onError={e => { e.target.src = 'https://via.placeholder.com/400'; }}
        />
      </div>
      <div className="flex flex-col flex-1 gap-1">
        <span className="text-xs text-gray-500 uppercase font-semibold tracking-wide mb-1">{site_name || 'Retailer'}</span>
        <a href={url} target="_blank" rel="noopener noreferrer" className="hover:underline">
          <h2 className="font-bold text-base line-clamp-2 min-h-[2.5em]">{title || 'Untitled Product'}</h2>
        </a>
        {/* Price Section */}
        <div className="flex items-center gap-2 mt-1">
          {discounted_price ? (
            <>
              <span className="text-lg font-extrabold text-red-600">{formatPrice(discounted_price, currency)}</span>
              <span className="line-through text-sm text-gray-400">{formatPrice(price, currency)}</span>
            </>
          ) : (
            <span className="text-lg font-extrabold text-black">{formatPrice(price, currency)}</span>
          )}
          {discount_percentage && (
            <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded ml-2">Save {discount_percentage}</span>
          )}
        </div>
        {/* Brand */}
        {brand && (
          <span className="text-xs text-gray-600 font-medium mt-1">Brand: {brand}</span>
        )}
        {/* Description */}
        {product_description && (
          <p className="text-gray-700 text-sm mt-2 line-clamp-3">{product_description}</p>
        )}
      </div>
    </div>
  );
};

export default ProductCard;
