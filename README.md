# Velora

Velora is a modern web application that allows you to save products from any e-commerce site and organize them on a beautiful, Pinterest-style canvas. Simply paste a product URL, and Velora will automatically fetch the product's details, including its title, price, and image, using a powerful backend powered by Firecrawl and CrewAI.

## Features

- **Universal Product Scraping:** Paste any product URL and watch it appear on your board.
- **AI-Powered Data Cleaning:** Uses CrewAI to intelligently extract and clean product information.
- **Modern UI:** A clean, responsive, and beautiful interface built with React and Material-UI.
- **Persistent Wishlist:** Your product board is saved in your browser's session storage.

## Tech Stack

- **Frontend:** React, Vite, Material-UI
- **Backend:** Python, FastAPI
- **Data Scraping:** [Firecrawl](https://firecrawl.dev/)
- **AI Data Cleaning:** [CrewAI](https://www.crewai.com/)

## Installation and Setup

Follow these steps to get Velora running on your local machine.

### Prerequisites

- [Node.js](https://nodejs.org/en/) (v18 or newer)
- [Python](https://www.python.org/downloads/) (v3.9 or newer)

### 1. Clone the Repository

```bash
git clone https://github.com/Jamahl/velora.git
cd velora
```

### 2. Backend Setup

The backend is responsible for scraping product data and processing it with AI.

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    -   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and add your API keys for Firecrawl and OpenAI:
        ```
        FIRECRAWL_API_KEY="your_firecrawl_api_key"
        OPENAI_API_KEY="your_openai_api_key"
        ```

4.  **Run the backend server:**
    ```bash
    uvicorn main:app --reload --port 8001
    ```
    The backend will be running at `http://localhost:8001`.

### 3. Frontend Setup

The frontend provides the user interface for your canvas.

1.  **Navigate to the frontend directory (from the root):**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Run the frontend development server:**
    ```bash
    npm run dev
    ```
    The application will be accessible at `http://localhost:5173` (or another port if 5173 is in use).
