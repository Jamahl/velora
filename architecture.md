This document outlines the technical architecture for a full-stack web application designed to allow users to save product links, track price changes, and discover similar or cheaper products using AI-powered agents.

📁 File + Folder Structure
bashwishlist-app/
├── frontend/
│   ├── public/
│   └── src/
│       ├── assets/
│       ├── components/
│       │   ├── common/              # Navbar, Modal, LoadingSpinner
│       │   ├── product/             # ProductCard, ProductModal, PriceChart
│       │   ├── notification/        # NotificationBell, NotificationList
│       │   └── admin/               # AdminConfigForm, AdminStats
│       ├── context/
│       │   ├── AuthContext.jsx
│       │   ├── ProductContext.jsx
│       │   └── NotificationContext.jsx
│       ├── hooks/
│       │   ├── useAuth.js
│       │   ├── useProducts.js
│       │   ├── useRealtimeNotifications.js
│       │   └── useAdminConfig.js
│       ├── pages/
│       │   ├── dashboard/
│       │   │   ├── Dashboard.jsx
│       │   │   └── PriceAlerts.jsx
│       │   ├── wishlist/
│       │   │   ├── WishlistPage.jsx
│       │   │   └── AddProduct.jsx
│       │   ├── settings/
│       │   │   ├── SettingsPage.jsx
│       │   │   └── NotificationSettings.jsx
│       │   └── admin/
│       │       ├── AdminPanel.jsx
│       │       ├── ConfigManager.jsx
│       │       └── SystemStats.jsx
│       ├── services/
│       │   ├── api.js               # Base API configuration
│       │   ├── authService.js       # Supabase auth wrapper
│       │   ├── productService.js    # Product CRUD operations
│       │   ├── notificationService.js # Notification management
│       │   └── adminService.js      # Admin configuration
│       ├── styles/
│       │   └── globals.css
│       └── App.jsx
├── backend/
│   ├── wishlist/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── agents/
│   │       ├── __init__.py
│   │       ├── crew_config.py       # CrewAI agent configurations
│   │       ├── product_analyzer.py  # Agent for product data extraction
│   │       └── price_comparator.py  # Agent for price comparison & similar products
│   ├── manage.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
├── scripts/
│   ├── price_checker.py
│   ├── similar_product_finder.py
│   └── data_extractor.py            # Firecrawl + CrewAI integration
├── supabase/
│   ├── schema.sql
│   └── migrations/
├── .env
├── requirements.txt
├── README.md
└── docker-compose.yml

🧠 Architecture Components
Frontend (React + DaisyUI)
Components Structure

common/: Reusable UI components (Navbar, Modal, LoadingSpinner, ErrorBoundary)
product/: Product-specific components (ProductCard, ProductModal, PriceChart, SimilarProductsList)
notification/: Real-time notification components (NotificationBell, NotificationList, NotificationToast)
admin/: Admin-only components (AdminConfigForm, AdminStats, UserManagement)

Context & State Management

AuthContext: User authentication state, role-based access
ProductContext: Wishlist products, price history, AI suggestions
NotificationContext: Real-time notifications, read/unread state

Hooks

useAuth: Authentication logic, user profile management
useProducts: Product CRUD operations, price tracking
useRealtimeNotifications: Supabase realtime subscription for notifications
useAdminConfig: Admin configuration management

Pages & Routing

/dashboard: Overview of saved items, price alerts, and AI recommendations
/wishlist: Full product management interface with search and filters
/settings: User preferences, notification settings, account management
/admin: Admin-only panel for system configuration (role-protected)

Services

authService: Supabase auth integration (email/phone login)
productService: Product API calls, data transformation
notificationService: Notification management and real-time updates
adminService: Admin configuration and system statistics

Backend (Django + DRF)
Models (models.py)

Product: Core product data with price history and AI results
Notification: User notifications with real-time capabilities
Settings: User preferences for notifications and alerts
AdminConfig: System-wide configuration for intervals and caching

Views & API Endpoints (views.py)

Product ViewSet: CRUD operations, bulk operations, search
Notification ViewSet: Real-time notification management
Settings ViewSet: User preference management
Admin ViewSet: Configuration management (admin-only)

AI Agent Integration (agents/)

crew_config.py: CrewAI agent setup and configuration
product_analyzer.py: Agent for extracting product data from Firecrawl output
price_comparator.py: Agent for finding similar products and price analysis

Background Tasks (tasks.py)

Celery/Cron integration for scheduled price checks
AI agent orchestration for product analysis
Notification dispatching with real-time updates

Web Scraping & AI Integration
Firecrawl Integration

API Endpoint: https://docs.firecrawl.dev/introduction
Purpose: Extract clean, structured data from product URLs
Features Used:

URL scraping with content extraction
Metadata extraction (title, price, images)
Rate limiting and error handling
Structured data output for AI processing



CrewAI Agent Workflow

Product Analyzer Agent:

Processes Firecrawl output
Extracts product title, price, description, images
Validates and structures data for database storage
Handles multiple e-commerce site formats


Price Comparator Agent:

Analyzes product data for price comparison
Finds similar products across different platforms
Generates recommendations based on price and features
Maintains context for better suggestions




🔗 Data Flow & System Architecture
React Frontend (DaisyUI)
    ↕ Real-time Updates
Supabase (Auth + PostgreSQL + Realtime)
    ↕ API Calls
Django REST API
    ↕ Background Tasks
Celery/Cron Jobs
    ↕ Data Processing
Firecrawl API → CrewAI Agents → OpenAI API
State Management

Frontend: React Context API with useState/useReducer
Authentication: Supabase Auth with persistent sessions
Real-time: Supabase realtime subscriptions for notifications
Caching: Database-level caching with timestamp-based invalidation

Data Processing Pipeline

User adds product URL → Frontend validation
Django receives request → Firecrawl API call
Firecrawl returns structured data → CrewAI product analyzer
Agent processes data → Database storage
Background tasks → Price monitoring & AI analysis
Real-time updates → Frontend notification


🛠️ Database Schema (Supabase PostgreSQL)
sql-- Users managed by Supabase Auth (email/phone authentication)

CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users ON DELETE CASCADE,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  image_url TEXT,
  current_price NUMERIC(10,2),
  original_price NUMERIC(10,2),
  site_name TEXT,
  description TEXT,
  category TEXT,
  last_checked TIMESTAMP,
  similar_found_at TIMESTAMP,
  ai_result JSONB,                    -- Structured AI recommendations
  ai_result_seen BOOLEAN DEFAULT FALSE,
  firecrawl_data JSONB,               -- Raw Firecrawl output
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE price_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  product_id UUID REFERENCES products ON DELETE CASCADE,
  price NUMERIC(10,2) NOT NULL,
  recorded_at TIMESTAMP DEFAULT NOW(),
  source TEXT                         -- Firecrawl, manual, etc.
);

CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users ON DELETE CASCADE,
  product_id UUID REFERENCES products ON DELETE CASCADE,
  message TEXT NOT NULL,
  type TEXT NOT NULL,                 -- 'price_drop', 'similar_found', 'error'
  read BOOLEAN DEFAULT FALSE,
  data JSONB,                         -- Additional notification data
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE settings (
  user_id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  notify_email BOOLEAN DEFAULT TRUE,
  notify_whatsapp BOOLEAN DEFAULT FALSE,
  notify_inapp BOOLEAN DEFAULT TRUE,
  price_threshold_percent NUMERIC(5,2) DEFAULT 10.0,
  check_frequency_hours INTEGER DEFAULT 4,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE admin_config (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  price_check_interval_hours INTEGER DEFAULT 4,
  ai_cache_duration_seen_days INTEGER DEFAULT 1,
  ai_cache_duration_unseen_days INTEGER DEFAULT 7,
  firecrawl_rate_limit_per_hour INTEGER DEFAULT 100,
  max_similar_products INTEGER DEFAULT 5,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_products_user_id ON products(user_id);
CREATE INDEX idx_products_last_checked ON products(last_checked);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_price_history_product_id ON price_history(product_id);

-- Enable realtime for notifications
ALTER publication supabase_realtime ADD TABLE notifications;

🔁 Background Processing & Automation
Scheduled Tasks
1. Price Checker (price_checker.py)
python# Runs every N hours (configurable via admin_config)
def check_prices():
    # Get all products due for checking
    # Call Firecrawl API for updated data
    # Process with CrewAI product analyzer
    # Compare prices and update database
    # Create notifications for price drops
    # Trigger real-time updates
2. Similar Product Finder (similar_product_finder.py)
python# Runs based on cache policy
def find_similar_products():
    # Check cache rules (seen/unseen duration)
    # Use CrewAI price comparator agent
    # Query OpenAI for similar products
    # Update ai_result with recommendations
    # Cache results with timestamp
3. Data Extraction Pipeline (data_extractor.py)
python# Integrates Firecrawl + CrewAI
def extract_product_data(url):
    # Call Firecrawl API
    # Process with CrewAI product analyzer
    # Return structured product data
    # Handle errors and retries
Agent Workflows
CrewAI Agent Configuration

Product Analyzer Agent: Specializes in extracting product information
Price Comparator Agent: Focuses on price analysis and recommendations
Error Handler Agent: Manages failures and retries
Quality Assurance Agent: Validates extracted data

AI Processing Pipeline

Firecrawl extracts raw webpage content
Product Analyzer Agent structures the data
Price Comparator Agent analyzes for similarities
Results stored in database with caching
Real-time notifications sent to users


🔔 Real-time Notifications
Supabase Realtime Integration

Table Subscriptions: Listen to notifications table inserts
React Hook: useRealtimeNotifications manages subscriptions
Notification Types:

price_drop: Price decrease alerts
similar_found: AI-discovered alternatives
error: Scraping or processing errors
system: Admin announcements



Notification Flow

Background task detects price change
Notification created in database
Supabase realtime broadcasts insert
Frontend receives real-time update
UI displays notification toast/badge


👤 User Stories & Features
Core User Features
1. Add Product to Wishlist

User Action: Paste product URL
System Process: Firecrawl scraping → CrewAI analysis → Database storage
User Feedback: Product appears in wishlist with extracted data

2. Price Drop Monitoring

User Action: Enable price alerts in settings
System Process: Scheduled checks → Price comparison → Notification creation
User Feedback: Real-time alerts for price drops

3. AI-Powered Product Recommendations

User Action: View product details
System Process: CrewAI agent analysis → Similar product discovery
User Feedback: Suggestions for cheaper or similar alternatives

4. Price History Tracking

User Action: View product page
System Process: Historical price data retrieval
User Feedback: Price trend charts and statistics

Advanced Features
5. Bulk Operations

User Action: Select multiple products
System Process: Batch processing for checks/updates
User Feedback: Progress indicators and bulk results

6. Custom Alerts

User Action: Set price thresholds
System Process: Personalized monitoring rules
User Feedback: Customized notification triggers

7. Category Management

User Action: Organize products by category
System Process: Auto-categorization via AI
User Feedback: Filtered views and category insights


🔐 Admin Features & Management
Admin Panel (/admin)

Access Control: Supabase role-based authentication
Configuration Management:

Price check intervals
AI cache policies
Firecrawl rate limits
System maintenance modes



Admin Capabilities

System Configuration: Adjust global settings
User Management: View user statistics and activity
Error Monitoring: Track scraping failures and system issues
Performance Metrics: Monitor API usage and response times
Manual Triggers: Force price checks or AI analysis

Future Admin Features

A/B Testing: Feature flag management
Analytics Dashboard: User behavior and system performance
Audit Logs: Track admin actions and system changes
Resource Monitoring: API quota usage and cost tracking


🚀 Technical Implementation Details
API Integration
Firecrawl API Usage
python# Example implementation
import requests

def scrape_product(url):
    response = requests.post(
        "https://api.firecrawl.dev/v0/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
        json={"url": url, "pageOptions": {"onlyMainContent": True}}
    )
    return response.json()
CrewAI Agent Setup
python# Agent configuration
from crewai import Agent, Task, Crew

product_analyzer = Agent(
    role='Product Data Extractor',
    goal='Extract structured product information',
    backstory='Expert in e-commerce data extraction',
    tools=[firecrawl_tool, data_validator]
)

price_comparator = Agent(
    role='Price Analysis Specialist',
    goal='Find similar products and price comparisons',
    backstory='Expert in product comparison and pricing',
    tools=[openai_tool, price_analyzer]
)
Performance Considerations

Database Indexing: Optimized queries for large datasets
Caching Strategy: Multi-level caching for API responses
Rate Limiting: Respect Firecrawl and OpenAI API limits
Error Handling: Comprehensive retry logic and fallbacks
Monitoring: Application performance and error tracking

Security Measures

API Key Management: Secure environment variable handling
Input Validation: URL validation and sanitization
CORS Configuration: Proper cross-origin resource sharing
Rate Limiting: Prevent abuse and ensure fair usage
Data Encryption: Sensitive data protection


📋 Development Roadmap
Phase 1: MVP (Current)

✅ Basic product addition via URL
✅ Firecrawl integration for data extraction
✅ CrewAI agents for data processing
✅ Real-time notifications via Supabase
✅ Admin configuration panel
✅ Price monitoring and alerts

Phase 2: Enhanced Features

🔄 Advanced price history analytics
🔄 Bulk product operations
🔄 Category management and auto-categorization
🔄 Mobile responsive design improvements
🔄 Performance optimizations

Phase 3: Advanced AI Features

🔄 Personalized product recommendations
🔄 Market trend analysis
🔄 Predictive price modeling
🔄 Advanced similarity algorithms

Phase 4: Integrations (Post-MVP)

🔄 WhatsApp notifications
🔄 Browser extension
🔄 Mobile app development
🔄 Third-party e-commerce integrations


🏁 Conclusion
This comprehensive architecture provides a robust foundation for a full-featured wishlist and price tracking application. The integration of Firecrawl for reliable web scraping and CrewAI for intelligent data processing creates a powerful AI-driven system that can adapt to various e-commerce platforms and provide valuable insights to users.
The real-time notification system ensures users stay informed about price changes and new opportunities, while the admin panel provides the necessary tools for system management and optimization. The modular design allows for easy extension and scaling as the application grows.
Key technical strengths:

Scalable Architecture: Django + React with proper separation of concerns
Intelligent Data Processing: CrewAI agents for reliable data extraction
Real-time Capabilities: Supabase realtime for instant notifications
Comprehensive Admin Tools: Full system management and monitoring
Future-ready Design: Modular structure for easy feature additions