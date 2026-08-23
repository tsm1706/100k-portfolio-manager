# $100k Medium-Term Innovation Portfolio Manager

Interactive Streamlit web app for managing a balanced ~$100k portfolio focused on biotech / mRNA oncology, gene editing, quantum computing and healthspan themes.

**Features**
- Live prices via yfinance
- USD allocation editor (target $100k) with automatic weights & shares
- 5-year risk metrics: Ann. Return, Vol, Sharpe, Sortino, Calmar, Max DD, 12-month momentum
- Interactive Plotly charts (normalized prices + relative strength vs XBI)
- Editable catalysts table (next ~6 months)
- Macro & sector notes workspace
- "Talk to Grok" tab that generates a ready-to-copy prompt with your current portfolio snapshot

---

## Deploy to Streamlit Community Cloud (Public URL) – Recommended

This is the easiest way to get a permanent public web address.

### 1. Create a GitHub repository

1. Go to [github.com](https://github.com) and sign in (or create a free account).
2. Click the **+** button (top right) → **New repository**.
3. Repository name example: `100k-portfolio-manager`
4. Set visibility to **Public** (required for free Streamlit Cloud).
5. **Do not** initialize with README, .gitignore or license (we already have them).
6. Click **Create repository**.

### 2. Upload the files

**Option A – GitHub website (easiest for beginners)**

1. On the new empty repo page click **uploading an existing file**.
2. Drag and drop (or select) these files/folders from the `portfolio_app` folder:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
   - the whole `.streamlit` folder (containing `config.toml`)
3. Commit the changes.

**Option B – Git command line**

```bash
git clone https://github.com/YOUR_USERNAME/100k-portfolio-manager.git
cd 100k-portfolio-manager
# copy all files from the portfolio_app folder into this directory
git add .
git commit -m "Initial commit - portfolio manager"
git push origin main
```

### 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with the **same GitHub account**.
2. Click **New app**.
3. Fill in:
   - **Repository**: `YOUR_USERNAME/100k-portfolio-manager`
   - **Branch**: `main` (or `master`)
   - **Main file path**: `app.py`
4. Click **Deploy**.

After 1–3 minutes you will receive a public URL that looks like:

```
https://YOUR_USERNAME-100k-portfolio-manager-xxxxx.streamlit.app
```

You can share this link with anyone. The app will automatically update whenever you push changes to the GitHub repository.

---

## Local development

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Notes

- Data comes from Yahoo Finance via `yfinance`. Occasional rate limits can occur.
- Catalysts, notes and allocations are stored in the browser session only. Use the "Talk to Grok" tab to export a prompt and continue the conversation with Grok for permanent analysis and updates.
- This is a research / portfolio-management tool, **not investment advice**. Clinical catalysts are binary and timelines can change.

---

## File structure

```
portfolio_app/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .gitignore
└── .streamlit/
    └── config.toml        # Theme & server settings
```
