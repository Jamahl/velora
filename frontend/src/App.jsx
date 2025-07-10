import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import UrlInput from './components/UrlInput';
import CanvasBoard from './components/CanvasBoard';
import SimilarProductsPage from './pages/SimilarProductsPage';
import FindSimilarProductsV2 from './pages/FindSimilarProductsV2';
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
      const resp = await fetch('/api/product', {
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
    <Router>
      <div className="flex min-h-screen bg-black">
        <Sidebar />
        <div className="flex-1">
          <Routes>
            <Route
              path="/"
              element={
                <main className="ml-56 p-4 lg:p-8 flex-1">
                  <div className="rounded-lg bg-white shadow-lg p-8">
                    <div className="text-center p-8 lg:p-12">
                      <div className="max-w-2xl mx-auto">
                        <h1 className="text-4xl lg:text-5xl font-extrabold text-black tracking-tight">Velora2 Canvas</h1>
                        <p className="py-6 text-gray-600">Paste a product URL below. Your wishlist will appear in a clean, organized board.</p>
                        <div className="w-full max-w-lg mx-auto">
                          <UrlInput onAddUrl={handleAddUrl} />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-8">
                    <CanvasBoard products={products} onRemoveProduct={handleRemoveProduct} loading={loading} />
                  </div>
                </main>
              }
            />
            <Route
              path="/similar-products"
              element={
                <main className="ml-56 p-4 lg:p-8 flex-1">
                  <SimilarProductsPage wishlistProducts={products} />
                </main>
              }
            />
            <Route
              path="/find-similar-products-v2"
              element={
                <main className="ml-56 p-4 lg:p-8 flex-1">
                  <FindSimilarProductsV2 wishlistProducts={products} />
                </main>
              }
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App
