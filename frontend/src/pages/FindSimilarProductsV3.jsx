import React, { useState } from "react";
import ProductCard from "../components/product/ProductCard";
import { createPortal } from "react-dom";

// Firecrawl API key from firecrawl_test.py
const FIRECRAWL_API_KEY = "fc-610fb046b36f48a4b79d236bbecdefa2";

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
  
  // Boost score for context containing price-related terms
  const priceTerms = ['price', 'cost', 'sale', 'discount', 'now', 'only', 'buy', 'usd', '$', 'dollars'];
  for (const term of priceTerms) {
    if (context.toLowerCase().includes(term)) score += 1;
  }
  
  return score;
};
