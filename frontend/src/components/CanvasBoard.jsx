import React from 'react';
import ProductCard from './product/ProductCard';

const CanvasBoard = ({ products, onRemoveProduct, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[200px] py-8">
        <div className="animate-pulse flex space-x-2">
          <div className="w-2 h-8 bg-black rounded-full"></div>
          <div className="w-2 h-8 bg-gray-600 rounded-full animation-delay-200"></div>
          <div className="w-2 h-8 bg-gray-400 rounded-full animation-delay-400"></div>
        </div>
      </div>
    );
  }
  if (!products.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[200px] py-8">
        <div className="text-3xl mb-2">🪄</div>
        <div className="text-lg text-gray-600 font-medium">No products yet. Paste a URL above to get started!</div>
      </div>
    );
  }
  return (
    <div className="w-full min-h-[200px] grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
      {products.map((product, idx) => (
        <div key={product.url} className="transition-transform duration-200 hover:scale-105">
          <ProductCard product={product} />
        </div>
      ))}
    </div>
  );
};

export default CanvasBoard;
