import React, { useState } from 'react';

const UrlInput = ({ onAddUrl }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validateUrl = (value) => {
    try {
      // Basic URL validation
      const parsed = new URL(value);
      return parsed.protocol.startsWith('http');
    } catch (e) {
      return false;
    }
  };

  const handleChange = (e) => {
    setUrl(e.target.value);
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validateUrl(url)) {
      setError('Enter a valid URL (http/https)');
      return;
    }
    onAddUrl(url.trim());
    setUrl('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-start gap-2 mb-4">
      <div className="w-full">
        <div className="relative flex items-center border border-gray-300 rounded-md focus-within:ring-1 focus-within:ring-black focus-within:border-black">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-4 h-4 opacity-70 ml-3"><path d="M6.75 8.25a.75.75 0 0 0 0 1.5h2.5a.75.75 0 0 0 0-1.5h-2.5Z" /><path d="M2 2.75A2.75 2.75 0 0 1 4.75 0h6.5A2.75 2.75 0 0 1 14 2.75v10.5A2.75 2.75 0 0 1 11.25 16h-6.5A2.75 2.75 0 0 1 2 13.25V2.75Zm2.75-1.25a1.25 1.25 0 0 0-1.25 1.25v10.5c0 .69.56 1.25 1.25 1.25h6.5c.69 0 1.25-.56 1.25-1.25V2.75a1.25 1.25 0 0 0-1.25-1.25h-6.5Z" /></svg>
          <input 
            type="text" 
            className="w-full py-2 px-3 outline-none bg-transparent"
            placeholder="Paste product URL"
            value={url}
            onChange={handleChange}
            autoFocus
          />
        </div>
        {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
      </div>
      <button type="submit" className="px-4 py-2 bg-black hover:bg-gray-800 text-white font-medium rounded-md transition-colors duration-200">
        Add
      </button>
    </form>
  );
};

export default UrlInput;
