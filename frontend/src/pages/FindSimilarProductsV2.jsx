import React, { useState } from "react";
import ProductCard from "../components/product/ProductCard";
import { createPortal } from "react-dom";

// Helper function to extract price from text using robust e-commerce patterns
const extractPrice = (text) => {
  if (!text) return null;
  
  console.log('🔍 Starting price extraction from text length:', text.length);
  
  // Clean and normalize text for better matching
  const cleanText = text.replace(/\s+/g, ' ').trim();
  
  // STEP 1: Look for high-confidence e-commerce price patterns first
  const highConfidencePatterns = [
    // Current/Sale price indicators with strong context
    /(?:now|sale|current|today|special)\s*(?:price)?\s*:?\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    /(?:buy|purchase|get)\s*(?:it|now|for)?\s*(?:only)?\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    /(?:price|cost)\s*:?\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    // JSON-like price structures common in scraped data
    /["']price["']\s*:\s*["']?\$?([0-9,]+(?:\.[0-9]{2})?)["']?/gi,
    /["']current_price["']\s*:\s*["']?\$?([0-9,]+(?:\.[0-9]{2})?)["']?/gi,
  ];
  
  for (const pattern of highConfidencePatterns) {
    const matches = [...cleanText.matchAll(pattern)];
    if (matches.length > 0) {
      for (const match of matches) {
        const priceStr = match[1].replace(/,/g, '');
        const price = parseFloat(priceStr);
        if (isValidPrice(price)) {
          console.log('✅ High confidence price found:', price, 'from pattern:', match[0]);
          return formatPrice(price);
        }
      }
    }
  }
  
  // STEP 2: Look for contextual price sections
  const priceContexts = extractPriceContexts(cleanText);
  for (const context of priceContexts) {
    const contextPrice = extractPriceFromContext(context);
    if (contextPrice) {
      console.log('✅ Context price found:', contextPrice, 'from:', context.substring(0, 50) + '...');
      return contextPrice;
    }
  }
  
  // STEP 3: Look for standard dollar patterns with validation
  const dollarPatterns = [
    /\$([0-9,]+(?:\.[0-9]{2})?)/g,
    /USD\s*([0-9,]+(?:\.[0-9]{2})?)/gi,
    /([0-9,]+(?:\.[0-9]{2})?)\s*(?:USD|dollars?)/gi,
  ];
  
  const allPrices = [];
  for (const pattern of dollarPatterns) {
    const matches = [...cleanText.matchAll(pattern)];
    for (const match of matches) {
      const priceStr = match[1].replace(/,/g, '');
      const price = parseFloat(priceStr);
      if (isValidPrice(price)) {
        allPrices.push({ price, context: getContextAroundMatch(cleanText, match.index, 30) });
      }
    }
  }
  
  if (allPrices.length > 0) {
    // Sort by likelihood - prefer prices in common ranges and with good context
    const sortedPrices = allPrices.sort((a, b) => {
      const aScore = getPriceConfidenceScore(a.price, a.context);
      const bScore = getPriceConfidenceScore(b.price, b.context);
      return bScore - aScore;
    });
    
    const bestPrice = sortedPrices[0];
    console.log('✅ Best dollar pattern price:', bestPrice.price, 'context:', bestPrice.context);
    return formatPrice(bestPrice.price);
  }
  
  console.log('❌ No valid price found in text');
  return null;
};

// Helper function to validate if a number is a reasonable price
const isValidPrice = (price) => {
  return !isNaN(price) && price >= 0.01 && price <= 500000 && 
         // Avoid common false positives like years, IDs, etc.
         !(price >= 1900 && price <= 2030 && price % 1 === 0);
};

// Helper function to format price consistently
const formatPrice = (price) => {
  return price.toFixed(2);
};

// Helper function to get context around a match
const getContextAroundMatch = (text, index, radius) => {
  const start = Math.max(0, index - radius);
  const end = Math.min(text.length, index + radius);
  return text.substring(start, end);
};

// Helper function to score price confidence based on value and context
const getPriceConfidenceScore = (price, context) => {
  let score = 0;
  
  // Prefer common price ranges
  if (price >= 10 && price <= 1000) score += 3;
  else if (price >= 1 && price <= 10000) score += 2;
  else score += 1;
  
  // Boost score for price-related context
  const lowerContext = context.toLowerCase();
  if (lowerContext.includes('price')) score += 2;
  if (lowerContext.includes('cost')) score += 2;
  if (lowerContext.includes('buy')) score += 2;
  if (lowerContext.includes('sale')) score += 1;
  if (lowerContext.includes('now')) score += 1;
  
  return score;
};

// Helper function to extract price-relevant contexts from text
const extractPriceContexts = (text) => {
  const contexts = [];
  const lines = text.split(/[\n\r]+/);
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.length < 5) continue;
    
    // Look for lines that likely contain price information
    if (/(?:price|cost|buy|sale|now|\$[0-9])/i.test(trimmed)) {
      contexts.push(trimmed);
    }
  }
  
  return contexts;
};

// Helper function to extract price from a specific context
const extractPriceFromContext = (context) => {
  const patterns = [
    /\$([0-9,]+(?:\.[0-9]{2})?)/,
    /([0-9,]+(?:\.[0-9]{2})?)\s*(?:USD|dollars?)/i,
    /(?:price|cost)\s*:?\s*([0-9,]+(?:\.[0-9]{2})?)/i,
  ];
  
  for (const pattern of patterns) {
    const match = context.match(pattern);
    if (match) {
      const priceStr = match[1].replace(/,/g, '');
      const price = parseFloat(priceStr);
      if (isValidPrice(price)) {
        return formatPrice(price);
      }
    }
  }
  
  return null;
};



// Helper function to extract original price when there's a discount
const extractOriginalPrice = (text, currentPrice) => {
  if (!text || !currentPrice) return null;
  
  const currentPriceNum = parseFloat(currentPrice);
  if (isNaN(currentPriceNum)) return null;
  
  console.log('🔍 Looking for original price, current:', currentPriceNum);
  
  // Clean and normalize text
  const cleanText = text.replace(/\s+/g, ' ').trim();
  
  // STEP 1: Look for explicit discount/original price patterns
  const discountPatterns = [
    // "Was $X, now $Y" patterns
    /(?:was|originally|before)\s*\$([0-9,]+(?:\.[0-9]{2})?).*?(?:now|sale|today)\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    /(?:now|sale|today)\s*\$([0-9,]+(?:\.[0-9]{2})?).*?(?:was|originally|before)\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    
    // "Regular price $X, sale price $Y" patterns
    /(?:regular|retail|list|msrp)\s*(?:price)?\s*\$([0-9,]+(?:\.[0-9]{2})?).*?(?:sale|now|special)\s*(?:price)?\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    /(?:sale|now|special)\s*(?:price)?\s*\$([0-9,]+(?:\.[0-9]{2})?).*?(?:regular|retail|list|msrp)\s*(?:price)?\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    
    // Strikethrough-like patterns (common in HTML scraping)
    /(?:strike|del|line-through).*?\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    /<del.*?>.*?\$([0-9,]+(?:\.[0-9]{2})?).*?<\/del>/gi,
    
    // "Save $X" patterns - we can infer original price
    /save\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    /(?:discount|off)\s*\$([0-9,]+(?:\.[0-9]{2})?)/gi,
    
    // Percentage discount patterns
    /([0-9]+)%\s*(?:off|discount|save)/gi,
  ];
  
  // Try explicit discount patterns first
  for (const pattern of discountPatterns) {
    const matches = [...cleanText.matchAll(pattern)];
    for (const match of matches) {
      if (pattern.source.includes('save|discount|off')) {
        // Handle "Save $X" patterns
        const savings = parseFloat(match[1].replace(/,/g, ''));
        if (!isNaN(savings) && savings > 0) {
          const originalPrice = currentPriceNum + savings;
          if (originalPrice > currentPriceNum * 1.05) {
            console.log('✅ Found original price from savings:', originalPrice);
            return formatPrice(originalPrice);
          }
        }
      } else if (pattern.source.includes('%')) {
        // Handle percentage discount
        const discountPercent = parseFloat(match[1]);
        if (!isNaN(discountPercent) && discountPercent > 0 && discountPercent < 90) {
          const originalPrice = currentPriceNum / (1 - discountPercent / 100);
          console.log('✅ Found original price from percentage:', originalPrice);
          return formatPrice(originalPrice);
        }
      } else {
        // Handle explicit price pairs
        const price1 = parseFloat(match[1].replace(/,/g, ''));
        const price2 = match[2] ? parseFloat(match[2].replace(/,/g, '')) : null;
        
        if (!isNaN(price1)) {
          // Determine which is original vs current
          let originalPrice = null;
          if (price2 && !isNaN(price2)) {
            // Two prices found - higher one is likely original
            originalPrice = Math.max(price1, price2);
            const lowerPrice = Math.min(price1, price2);
            // Verify the lower price matches our current price (within 10%)
            if (Math.abs(lowerPrice - currentPriceNum) / currentPriceNum < 0.1) {
              console.log('✅ Found original price from pair:', originalPrice);
              return formatPrice(originalPrice);
            }
          } else if (price1 > currentPriceNum * 1.05) {
            // Single higher price found
            console.log('✅ Found original price (single):', price1);
            return formatPrice(price1);
          }
        }
      }
    }
  }
  
  // STEP 2: Look for multiple prices and find the higher one
  const allPrices = findAllPricesInText(cleanText);
  const validOriginalPrices = allPrices.filter(price => 
    price > currentPriceNum * 1.05 && // At least 5% higher
    price < currentPriceNum * 5 && // Not more than 5x higher (unrealistic)
    isValidPrice(price)
  );
  
  if (validOriginalPrices.length > 0) {
    // Sort by proximity to a reasonable discount (10-70% off)
    const sortedPrices = validOriginalPrices.sort((a, b) => {
      const discountA = (a - currentPriceNum) / a;
      const discountB = (b - currentPriceNum) / b;
      
      // Prefer discounts in the 10-70% range
      const scoreA = (discountA >= 0.1 && discountA <= 0.7) ? 1 : 0;
      const scoreB = (discountB >= 0.1 && discountB <= 0.7) ? 1 : 0;
      
      if (scoreA !== scoreB) return scoreB - scoreA;
      
      // If both are in range or both out of range, prefer smaller discount
      return Math.abs(discountA - 0.3) - Math.abs(discountB - 0.3);
    });
    
    console.log('✅ Found original price from multiple prices:', sortedPrices[0]);
    return formatPrice(sortedPrices[0]);
  }
  
  console.log('❌ No original price found');
  return null;
};

// Helper function to find all prices in text
const findAllPricesInText = (text) => {
  const pricePatterns = [
    /\$([0-9,]+(?:\.[0-9]{2})?)/g,
    /([0-9,]+(?:\.[0-9]{2})?)\s*(?:USD|dollars?)/gi,
  ];
  
  const prices = [];
  for (const pattern of pricePatterns) {
    const matches = [...text.matchAll(pattern)];
    for (const match of matches) {
      const price = parseFloat(match[1].replace(/,/g, ''));
      if (isValidPrice(price)) {
        prices.push(price);
      }
    }
  }
  
  // Remove duplicates and sort
  return [...new Set(prices)].sort((a, b) => b - a);
};

// Helper function to calculate discount percentage
const calculateDiscountPercentage = (originalPrice, currentPrice) => {
  if (!originalPrice || !currentPrice) return null;
  
  const original = parseFloat(originalPrice);
  const current = parseFloat(currentPrice);
  
  // Only calculate if original is significantly higher (at least 5%)
  // This helps avoid false discounts due to rounding or minor price differences
  if (original > current && original > current * 1.05) {
    const discount = Math.round(((original - current) / original) * 100);
    
    // Validate the discount is reasonable (between 5% and 90%)
    if (discount >= 5 && discount <= 90) {
      return discount + "%";
    }
  }
  
  return null;
};

// TODO: Replace with your actual Exa API key
const EXA_API_KEY = "24b1e244-275f-4343-bd1d-0578e3ddc020";

// Modal component for product details
const ProductModal = ({ product, onClose }) => {
  // Prevent rendering if document is not available (SSR)
  if (typeof document === 'undefined') return null;
  if (!product) return null;
  
  // Handle click outside to close
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  
  return createPortal(
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Modal header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-200">
          <h3 className="text-xl font-semibold text-gray-900">{product.title}</h3>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Modal content */}
        <div className="p-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Product image */}
            <div className="md:w-1/2">
              {product.image_url ? (
                <img 
                  src={product.image_url} 
                  alt={product.title} 
                  className="w-full h-auto object-contain rounded-md"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://via.placeholder.com/400x400?text=No+Image';
                  }}
                />
              ) : (
                <div className="w-full h-64 flex items-center justify-center bg-gray-200 rounded-md">
                  <span className="text-gray-500">No image available</span>
                </div>
              )}
            </div>
            
            {/* Product details */}
            <div className="md:w-1/2">
              {/* Price section */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  {product.price && (
                    <span className="text-2xl font-bold text-gray-900">{product.price}</span>
                  )}
                  {product.original_price && (
                    <span className="line-through text-base text-gray-500">{product.original_price}</span>
                  )}
                </div>
                {product.discount_percentage && (
                  <span className="bg-red-500 text-white text-sm px-2 py-1 rounded">
                    Save {product.discount_percentage}
                  </span>
                )}
              </div>
              
              {/* Retailer */}
              <div className="mb-4">
                <span className="text-sm text-gray-600">From</span>
                <a 
                  href={product.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="ml-2 inline-flex items-center justify-center rounded text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 px-3 py-1"
                >
                  {product.site_name}
                </a>
              </div>
              
              {/* Description */}
              <div className="mb-6">
                <h4 className="text-lg font-semibold mb-2 text-gray-900">Description</h4>
                <p className="text-gray-700">
                  {product.description || "No description available"}
                </p>
              </div>
              
              {/* Action button */}
              <a 
                href={product.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-full inline-flex items-center justify-center rounded text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 h-10 px-4"
              >
                View on {product.site_name}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

const FindSimilarProductsV2 = ({ wishlistProducts = [] }) => {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [modalProduct, setModalProduct] = useState(null);

  const handleSelect = (e) => {
    const idx = e.target.value;
    setSelectedProduct(wishlistProducts[idx]);
  };

  const handleFindSimilar = async () => {
    if (!selectedProduct) return;
    setLoading(true);
    setError("");
    setSimilarProducts([]);
    try {
      if (!EXA_API_KEY) throw new Error("Missing Exa API key.");
      if (!selectedProduct.url) throw new Error("Selected product must have a URL");
      
      // Step 1: Find similar products using Exa's search API
      const searchResp = await fetch("https://api.exa.ai/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${EXA_API_KEY}`,
        },
        body: JSON.stringify({
          query: `similar:${selectedProduct.url}`,
          numResults: 10,
          highlights: true,
          useAutoprompt: true
        }),
      });
      
      if (!searchResp.ok) throw new Error(`Failed to fetch similar products from Exa API: ${searchResp.status} ${searchResp.statusText}`);
      const searchData = await searchResp.json();
      
      // Extract URLs from search results
      const similarUrls = (searchData.results || []).map(item => item.url).filter(Boolean);
      
      if (similarUrls.length === 0) {
        setSimilarProducts([]);
        setLoading(false);
        return;
      }
      
      // Step 2: Get detailed content for each URL using Exa's contents API
      const contentsResp = await fetch("https://api.exa.ai/contents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${EXA_API_KEY}`,
        },
        body: JSON.stringify({
          urls: similarUrls,
          text: true,
          livecrawl: "preferred",
          summary: {
            query: "Extract product information including price, original price if discounted, and key features"
          },
          extras: {
            imageLinks: 3
          }
        }),
      });
      
      if (!contentsResp.ok) throw new Error(`Failed to fetch content from Exa API: ${contentsResp.status} ${contentsResp.statusText}`);
      const contentsData = await contentsResp.json();
      
      // Log the raw API response for debugging
      console.log('Raw Exa /contents API response:', contentsData);
      
      // Process and transform the data
      const processedProducts = contentsData.results.map((item, index) => {
        console.log(`\n--- Processing Product ${index + 1} ---`);
        console.log(`URL: ${item.url}`);
        console.log(`Title: ${item.title}`);
        
        // Log a sample of the text content for debugging
        if (item.text) {
          const textSample = item.text.substring(0, 300);
          console.log(`Text sample: ${textSample}...`);
        } else {
          console.log('No text content available');
        }
        // Extract domain name for display
        let siteName = "";
        try {
          const url = new URL(item.url);
          siteName = url.hostname.replace(/^www\./, "").split(".")[0].toUpperCase();
        } catch (e) {
          siteName = "RETAILER";
        }
        
        // Extract price from text
        console.log(`Processing item: ${item.url}`);
        console.log('Raw text content:', item.text?.substring(0, 500) + '...');
        

        
        // Extract price using improved logic
        const price = extractPrice(item.text);
        console.log('Extracted price:', price);
        
        // If we found a price, try to find original price
        const originalPrice = price ? extractOriginalPrice(item.text, price) : null;
        console.log('Extracted original price:', originalPrice);
        
        // Calculate discount percentage if both prices are available
        const discountPercentage = calculateDiscountPercentage(originalPrice, price);
        
        // Format prices with $ if they exist
        const formattedPrice = price ? `$${price}` : null;
        const formattedOriginalPrice = originalPrice ? `$${originalPrice}` : null;
        
        console.log('Formatted price:', formattedPrice);
        console.log('Formatted original price:', formattedOriginalPrice);
        
        // Get the first image URL if available
        const imageUrl = item.extras?.imageLinks?.[0] || null;
        
        // Extract title from content or use URL as fallback
        const title = item.title || item.url.split("/").pop() || "Product";
        
        // Extract a short description
        let description = "";
        if (item.summary) {
          description = item.summary;
        } else if (item.text) {
          // Take first 200 characters as description
          description = item.text.substring(0, 200) + (item.text.length > 200 ? "..." : "");
        }
        
        return {
          url: item.url,
          title: title,
          description: description,
          image_url: imageUrl,
          price: formattedPrice,
          original_price: formattedOriginalPrice,
          discount_percentage: discountPercentage,
          site_name: siteName
        };
      });
      
      setSimilarProducts(processedProducts);
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="ml-56 px-0 py-8 min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        {/* Hero Section */}
        <div className="rounded-lg shadow-sm mb-8 p-6 flex flex-col md:flex-row items-center gap-8 bg-white border border-gray-200">
          <div>
            <h1 className="text-3xl font-bold mb-3 tracking-tight text-gray-900">Find Similar Products V2</h1>
            <p className="text-base text-gray-700 mb-4 leading-relaxed">Select a wishlist product and discover beautiful, relevant alternatives from Exa's API. No CrewAI.</p>
          </div>
          <div className="flex-1 flex flex-col md:items-end items-center w-full">
            <div className="w-full max-w-xs">
              {/* Product Selection */}
              <div className="mb-4">
                <label htmlFor="product-select" className="block text-sm font-medium text-gray-700 mb-1">
                  Select a Product
                </label>
                <select
                  id="product-select"
                  className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-10 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  onChange={handleSelect}
                  defaultValue=""
                >
                  <option value="" disabled>Choose a product</option>
                  {wishlistProducts.map((product, idx) => (
                    <option key={idx} value={idx}>
                      {product.name || product.title || `Product ${idx + 1}`}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Find Similar Button */}
              <button
                onClick={handleFindSimilar}
                disabled={!selectedProduct || loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? "Finding Similar Products..." : "Find Similar Products"}
              </button>
            </div>
          </div>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}
        
        {/* Similar Products Grid */}
        <div className="bg-white shadow-sm rounded-lg p-6 border border-gray-200">
          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-square bg-gray-200 rounded-md mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-1/2 mb-1" />
                  <div className="h-5 bg-gray-200 rounded w-1/3" />
                </div>
              ))}
            </div>
          )}
          
          {!loading && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {similarProducts.map((prod) => (
                  <div 
                    key={prod.url} 
                    className="flex flex-col border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300 bg-white cursor-pointer"
                    onClick={() => setModalProduct(prod)}
                  >
                    {/* Product Image */}
                    <div className="relative h-48 overflow-hidden bg-gray-100">
                      {prod.image_url ? (
                        <img 
                          src={prod.image_url} 
                          alt={prod.title} 
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = 'https://via.placeholder.com/300x300?text=No+Image';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-200">
                          <span className="text-gray-500">No image available</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Product Info */}
                    <div className="p-4 flex flex-col flex-grow">
                      {/* Title */}
                      <h3 className="text-lg font-semibold mb-2 line-clamp-2 h-14 text-gray-900">{prod.title}</h3>
                      
                      {/* Price Section */}
                      <div className="mb-2">
                        <div className="flex items-center justify-between">
                          <div>
                            {prod.price && (
                              <span className="text-base font-bold text-gray-900">{prod.price}</span>
                            )}
                            {prod.original_price && (
                              <span className="ml-2 line-through text-xs text-gray-500">{prod.original_price}</span>
                            )}
                          </div>
                          {prod.discount_percentage && (
                            <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded">
                              Save {prod.discount_percentage}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Description */}
                      <p className="text-gray-700 text-sm mb-4 line-clamp-3 flex-grow">
                        {prod.description || "No description available"}
                      </p>
                      
                      {/* Action Buttons */}
                      <div className="mt-auto flex justify-between items-center">
                        {/* Retailer Button - Smaller Basecoat UI style */}
                        <a 
                          href={prod.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center rounded text-xs font-medium bg-blue-500 text-white hover:bg-blue-600 h-6 px-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {prod.site_name}
                        </a>
                        
                        {/* View Button */}
                        <a 
                          href={prod.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center rounded text-xs font-medium border border-gray-300 bg-white text-gray-800 hover:bg-gray-50 h-6 px-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {similarProducts.length === 0 && (
                <p className="text-center text-gray-500 my-8">No similar products found.</p>
              )}
              
              {/* Product Detail Modal */}
              {modalProduct && (
                <ProductModal 
                  product={modalProduct} 
                  onClose={() => setModalProduct(null)} 
                />
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
};

export default FindSimilarProductsV2;
