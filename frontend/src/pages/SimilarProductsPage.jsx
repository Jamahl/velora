import React, { useState, useEffect, useId } from "react";
import ProductCard from "../components/product/ProductCard";
import 'basecoat-css/dropdown-menu';

export default function SimilarProductsPage({ wishlistProducts }) {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSelect = (e) => {
    const idx = e.target.value;
    setSelectedProduct(wishlistProducts[idx]);
    setSimilarProducts([]);
    setError("");
  };

  const handleFindSimilar = async () => {
    if (!selectedProduct) return;
    setLoading(true);
    setError("");
    setSimilarProducts([]);
    try {
      const resp = await fetch("http://localhost:8002/api/similar-products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectedProduct),
      });
      if (!resp.ok) throw new Error("Failed to fetch similar products");
      const data = await resp.json();
      // Ensure we're using the correct key from the API response
      setSimilarProducts(data.similar_products || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="ml-56 px-0 py-8 min-h-screen bg-black">
      <div className="max-w-6xl mx-auto px-4">
        {/* Hero Section */}
        <div className="rounded-xl shadow-xl mb-8 p-8 flex flex-col md:flex-row items-center gap-8 bg-gradient-to-br from-black via-gray-900 to-gray-800 text-white border border-gray-800">
          <div className="flex-1">
            <h1 className="text-5xl font-extrabold mb-3 tracking-tight">Find Similar Products</h1>
            <p className="text-lg text-gray-300 mb-4 leading-relaxed">Select a wishlist product and discover beautiful, relevant alternatives from across the web. Powered by AI and real-time search.</p>
          </div>
          <div className="flex-1 flex flex-col md:items-end items-center w-full">
            <div className="w-full max-w-xs">
              <label className="block text-base font-medium mb-2 text-gray-200" htmlFor="productSelect">
                Select a product:
              </label>
              
              <div id="product-dropdown-menu" className="dropdown-menu w-full">
                <button 
                  type="button" 
                  id="product-dropdown-trigger" 
                  aria-haspopup="menu" 
                  aria-controls="product-dropdown-menu" 
                  aria-expanded="false" 
                  className="w-full flex justify-between items-center px-4 py-3 border border-gray-700 rounded-md bg-gray-800 text-white hover:bg-gray-700 transition-colors duration-200"
                >
                  <span className="truncate max-w-[200px]">
                    {selectedProduct ? selectedProduct.title : "Select product..."}
                  </span>
                  <svg className="h-5 w-5 text-gray-400 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                
                <div id="product-dropdown-popover" data-popover aria-hidden="true" className="min-w-56 max-w-xs">
                  <div role="menu" id="product-dropdown-menu" aria-labelledby="product-dropdown-trigger" className="bg-white border border-gray-200 shadow-lg rounded-md py-1 max-h-60 overflow-y-auto">
                    {wishlistProducts.length === 0 ? (
                      <div role="menuitem" aria-disabled="true" className="px-4 py-2 text-gray-500 text-sm">No products available</div>
                    ) : (
                      wishlistProducts.map((prod, idx) => (
                        <div 
                          key={prod.url} 
                          role="menuitem" 
                          onClick={() => handleSelect({target: {value: idx}})}
                          className="px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 truncate"
                        >
                          {prod.title}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-4 w-full flex flex-row gap-2">
              <button
                className="w-full px-4 py-3 bg-white hover:bg-gray-100 text-black font-medium rounded-md flex items-center justify-center transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleFindSimilar}
                disabled={!selectedProduct || loading}
                tabIndex={0}
                aria-label="Find similar products"
              >
                {loading ? (
                  <div className="animate-spin h-5 w-5 border-2 border-black border-t-transparent rounded-full"></div>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                    Find Similar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
        {/* Info or Error Alerts */}
        {wishlistProducts.length === 0 && (
          <div className="bg-gray-900 border border-gray-800 text-white rounded-lg my-8 p-5 flex items-center gap-3 shadow-lg">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">✨ Add a product to your wishlist first!</span>
          </div>
        )}
        {error && (
          <div className="bg-gray-900 border border-red-900 text-white rounded-lg shadow-lg mb-6 p-5 flex items-center gap-3">
            <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="font-medium">{error}</span>
          </div>
        )}
        {/* Similar Products Grid */}
        <div className="bg-gray-900 shadow-xl rounded-lg p-8 border border-gray-800">
          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse w-full max-w-xs bg-white shadow-md rounded-lg border border-gray-200 flex flex-col p-3 mx-auto">
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
                  <ProductCard key={prod.url} product={prod} />
                ))}
              </div>
              {similarProducts.length === 0 && (
                <div className="text-gray-300 mt-8 text-center">
                  <div className="border border-gray-700 rounded-lg px-8 py-6 inline-block bg-gray-800">
                    <p className="text-lg font-medium mb-1">No similar products found yet</p>
                    <p className="text-gray-400 text-sm">Try another item or broaden your wishlist!</p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
