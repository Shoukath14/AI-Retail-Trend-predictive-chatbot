# 🛍️ AI Retail Trend Analyzer Chatbot

A production-ready AI-powered retail trend analysis system with a ChatGPT-style interface, real data analysis engine, and interactive dashboard.

**Live Demo:** *(deploy link here after Render setup)*

---

## 🚀 Quick Start (Local)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/retail-trend-analyzer.git
cd retail-trend-analyzer
```

### 2. Set Up Python Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
copy .env.example .env
```
Edit `.env` and add your API keys:
```
GROQ_API_KEY=your-groq-key-here
SERPER_API_KEY=your-serper-key-here
```
- 🔑 Groq API key (free): https://console.groq.com/keys
- 🔑 Serper API key (free): https://serper.dev/

### 5. Run the Server
```bash
cd backend
python app.py
```

### 6. Open the App
Visit: **http://localhost:5000**

---

## 📁 Project Structure

```
retail-trend-analyzer/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── routes/
│   │   ├── chat.py             # /chat, /history endpoints
│   │   └── analysis.py         # /upload, /analyze, /dashboard, /report endpoints
│   ├── models/
│   │   └── db.py               # SQLite schema & connection
│   └── services/
│       ├── analyzer.py         # Trend analysis engine (pandas/numpy/sklearn)
│       ├── chatbot.py          # Groq API + Serper web search integration
│       └── report.py           # PDF report generation
├── frontend/
│   ├── index.html              # Main app (chat + dashboard + upload)
│   ├── styles.css              # Full UI styles (dark/light theme)
│   └── script.js               # All frontend logic
├── data/
│   ├── sample_retail_data.csv  # 150-row test dataset
│   └── uploads/                # Uploaded datasets stored here
├── database/
│   └── retail_analyzer.db      # SQLite database (auto-created at runtime)
├── .env.example                # Environment config template (copy to .env)
├── render.yaml                 # Render deployment configuration
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message, get AI response |
| GET | `/history` | List all chat sessions |
| GET | `/history/<id>` | Get messages for a session |
| DELETE | `/history/<id>` | Delete a session |
| POST | `/upload` | Upload CSV/JSON dataset |
| POST | `/analyze` | Run trend analysis |
| GET | `/dashboard` | Get dashboard data |
| GET | `/report/download` | Download PDF report |
| GET | `/datasets` | List uploaded datasets |
| GET | `/health` | Health check |

---

## 📊 Analysis Features

- **Frequency Analysis**: Most purchased products by volume
- **Category Demand**: Aggregate sales by category
- **Time-Series Trends**: Monthly sales over time
- **Seasonal Patterns**: Spring / Summer / Autumn / Winter breakdowns
- **Growth/Decline**: Compares first vs second half of dataset
- **Predictions**: Linear extrapolation → next-quarter forecasts
- **Trend Scores**: 0–100 composite score per product
- **Regional Demand**: If region column is present

---

## 🤖 Chatbot Behavior

- Powered by **Groq** (Llama 3.3 70B) — ultra-fast inference
- Real-time web search via **Serper** (Google results injected into context)
- Falls back to **compound-beta** model when Serper is unavailable
- Maintains full conversation context per session
- Answers only **fashion/retail domain** questions
- When a dataset is loaded, answers are grounded in your actual data

---

## 📋 Expected Dataset Format

```csv
date,product,category,quantity,price,region
2024-01-05,Running Sneakers,Footwear,120,89.99,North
2024-01-06,Yoga Pants,Activewear,200,59.99,West
```

**Required columns**: `date`, `product`, `quantity`  
**Optional columns**: `category`, `price`, `region`

The analyzer auto-detects common column name variations (e.g., `qty`, `units_sold`, `item_name`, etc.)

---

## 🎨 UI Features

- **Dark / Light theme** toggle
- **Sidebar** with chat history (persistent via SQLite)
- **Suggestion chips** on welcome screen
- **Typing indicator** while AI responds
- **Interactive charts** (Chart.js): line, bar, doughnut, polar area
- **Trend predictions panel** with confidence levels
- **Trend score bars** with gradient visualization
- **PDF report** download
- **Drag & drop** file upload
- Fully responsive layout

---

## 🔐 Security Notes

- Never commit your `.env` file — it's in `.gitignore`
- API keys are read server-side only, never exposed to the frontend
- File uploads are validated for type and sanitized with `secure_filename`

---

## ☁️ Deploying on Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Deploy**
5. Go to **Environment** tab and add your secrets:
   - `GROQ_API_KEY` = your Groq key
   - `SERPER_API_KEY` = your Serper key
6. Your app will be live at `https://your-app-name.onrender.com`

> **Note:** Render's free tier has an ephemeral disk — uploaded datasets and SQLite data reset on each redeploy. For persistent storage, consider upgrading or using an external database.

---

## 📦 Dependencies

```
flask, flask-cors          # Web framework
groq                       # Llama 3.3 70B via Groq API
requests                   # HTTP client for Serper web search
pandas, numpy              # Data processing
scikit-learn               # ML utilities
statsmodels                # Time-series analysis
reportlab                  # PDF generation
python-dotenv              # Environment config
Werkzeug                   # File security utilities
gunicorn                   # Production WSGI server (for Render)
```

---

## 💡 Sample Questions to Ask

After uploading the sample dataset:

- *"Which products are trending up this quarter?"*
- *"What's the demand forecast for sneakers?"*
- *"Which season has the highest sales overall?"*
- *"Compare activewear vs knitwear demand"*
- *"What should I restock for winter?"*
- *"Which region drives the most revenue?"*

---

Built with ❤️ using Flask + Groq + Chart.js
