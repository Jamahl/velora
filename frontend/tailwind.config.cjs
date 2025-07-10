/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./node_modules/basecoat-css/**/*.{js,jsx}"
  ],
  theme: {
    extend: {},
  },
  plugins: [require('basecoat-css/plugin')],
};
