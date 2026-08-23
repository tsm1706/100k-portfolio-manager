"""
$100k Medium-Term Innovation Portfolio Manager
Interactive Streamlit web app with live yfinance data, metrics, charts,
catalysts, and Grok collaboration workspace.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="$100k Portfolio Manager",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Default universe & allocations (from prior strategy)
# ---------------------------------------------------------------------------
DEFAULT_TICKERS = {
    "XBI": {"name": "SPDR S&P Biotech ETF", "category": "Core Biotech ETF", "usd": 30000},
    "MRK": {"name": "Merck & Co", "category": "Core Quality Pharma", "usd": 15000},
    "LLY": {"name": "Eli Lilly", "category": "Healthspan / Metabolic", "usd": 12000},
    "MRNA": {"name": "Moderna", "category": "mRNA Oncology", "usd": 8000},
    "BNTX": {"name": "BioNTech", "category": "mRNA Oncology", "usd": 7000},
    "CRSP": {"name": "CRISPR Therapeutics", "category": "Gene Editing", "usd": 5000},
    "NTLA": {"name": "Intellia Therapeutics", "category": "Gene Editing", "usd": 5000},
    "BEAM": {"name": "Beam Therapeutics", "category": "Gene Editing", "usd": 3000},
    "IONQ": {"name": "IonQ", "category": "Quantum Computing", "usd": 5000},
    "RGTI": {"name": "Rigetti Computing", "category": "Quantum Computing", "usd": 3000},
    "CASH": {"name": "Cash / Money Market", "category": "Buffer", "usd": 7000},
}

BENCHMARKS = ["XBI", "SPY"]

DEFAULT_CATALYSTS = [
    {"Ticker": "MRNA", "Catalyst": "Full intismeran Phase 3 data + regulatory engagement (melanoma)", "Timing": "H2 2026 / H1 2027", "Importance": "Very High", "Notes": "Hazard ratios & durability key"},
    {"Ticker": "MRNA", "Catalyst": "Additional oncology readouts (RCC, bladder, NSCLC)", "Timing": "Late 2026–2027", "Importance": "High", "Notes": "Platform expansion"},
    {"Ticker": "MRK", "Catalyst": "PDUFA / label updates (Winrevair, Welireg+Lenvima, I-DXd)", "Timing": "Sep–Oct 2026+", "Importance": "High", "Notes": "Near-term regulatory calendar"},
    {"Ticker": "MRK", "Catalyst": "Pipeline data (tulisokibart UC and others)", "Timing": "H2 2026", "Importance": "Medium-High", "Notes": "Supports $70B growth narrative"},
    {"Ticker": "BNTX", "Catalyst": "Late-stage oncology readouts (pumitamig, gotistobart, BNT113, ADCs)", "Timing": "H2 2026", "Importance": "High", "Notes": "Own data vs sector sympathy"},
    {"Ticker": "BNTX", "Catalyst": "CEO transition to Guido Oelkers", "Timing": "By Feb 2027", "Importance": "Medium", "Notes": "Leadership continuity"},
    {"Ticker": "NTLA", "Catalyst": "lonvo-z (HAE) BLA completion / acceptance; H1 2027 launch prep", "Timing": "H2 2026 / H1 2027", "Importance": "Very High", "Notes": "Potential first in-vivo CRISPR"},
    {"Ticker": "NTLA", "Catalyst": "nex-z (ATTR) Phase 3 enrollment progress", "Timing": "H2 2026", "Importance": "High", "Notes": "Second major program"},
    {"Ticker": "CRSP", "Catalyst": "Casgevy commercial ramp + clinical updates", "Timing": "Ongoing 2026", "Importance": "Medium", "Notes": "Revenue proof of gene editing"},
    {"Ticker": "BEAM", "Catalyst": "Base-editing clinical data updates (BEAM-302 etc.)", "Timing": "2026", "Importance": "Medium-High", "Notes": "Platform validation"},
    {"Ticker": "IONQ", "Catalyst": "256-qubit progress, customer systems, Investor Day", "Timing": "Sep 2026 onward", "Importance": "High", "Notes": "Technical + commercial milestones"},
    {"Ticker": "RGTI", "Catalyst": "Fidelity targets, C-DAC revenue, CHIPS Act progress", "Timing": "Q4 2026 / 2027", "Importance": "Medium-High", "Notes": "Execution on roadmap"},
    {"Ticker": "LLY", "Catalyst": "Retatrutide registration / BLA timing", "Timing": "Toward Q1 2027", "Importance": "High", "Notes": "Next major obesity asset"},
    {"Ticker": "Sector", "Catalyst": "Broader biotech M&A, clinical newsflow, rates", "Timing": "Ongoing", "Importance": "Sector", "Notes": "Sentiment & capital flows"},
]

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "tickers" not in st.session_state:
    st.session_state.tickers = DEFAULT_TICKERS.copy()
if "catalysts" not in st.session_state:
    st.session_state.catalysts = DEFAULT_CATALYSTS.copy()
if "macro_notes" not in st.session_state:
    st.session_state.macro_notes = (
        "Medium-term (1–5y) barbell: core ETFs + quality large-caps + small satellite "
        "speculative positions. Respect post-hype mean reversion (Moderna COVID lesson). "
        "Keep single-name risk ≤ 8–10%. Cash buffer for opportunities / drawdowns."
    )
if "sector_notes" not in st.session_state:
    st.session_state.sector_notes = (
        "mRNA oncology: validated by intismeran Phase 3 → platform re-rating possible but "
        "valuation discipline required.\n"
        "Gene editing: in-vivo (NTLA) approaching first potential approval; still binary.\n"
        "Quantum: revenue growth real (IonQ) but commercial quantum advantage still years away; "
        "high technical & dilution risk.\n"
        "Obesity / healthspan: LLY remains the highest-quality compounder in the group."
    )
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_prices(tickers: list[str]) -> pd.DataFrame:
    """Fetch latest price, previous close, % change."""
    data = []
    for t in tickers:
        if t == "CASH":
            data.append({"Ticker": "CASH", "Price": 1.0, "Prev Close": 1.0, "Change %": 0.0, "Name": "Cash"})
            continue
        try:
            tk = yf.Ticker(t)
            info = tk.fast_info
            price = float(info.get("lastPrice") or info.get("last_price") or np.nan)
            prev = float(info.get("previousClose") or info.get("previous_close") or np.nan)
            chg = ((price - prev) / prev * 100) if prev and prev > 0 else np.nan
            data.append({
                "Ticker": t,
                "Price": price,
                "Prev Close": prev,
                "Change %": chg,
                "Name": tk.info.get("shortName", t) if hasattr(tk, "info") else t,
            })
        except Exception:
            data.append({"Ticker": t, "Price": np.nan, "Prev Close": np.nan, "Change %": np.nan, "Name": t})
        time.sleep(0.15)  # gentle rate limit
    return pd.DataFrame(data)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_history(tickers: list[str], years: int = 5) -> pd.DataFrame:
    """Download adjusted close history."""
    end = datetime.now()
    start = end - timedelta(days=years * 365 + 30)
    clean = [t for t in tickers if t != "CASH"]
    if not clean:
        return pd.DataFrame()
    try:
        df = yf.download(clean, start=start, end=end, progress=False, auto_adjust=True, threads=False)["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.warning(f"History download issue: {e}")
        return pd.DataFrame()


def compute_metrics(prices: pd.Series, rf: float = 0.04) -> dict:
    """Annualized return, vol, Sharpe, Sortino, Calmar, max DD, 12m momentum."""
    if prices is None or len(prices) < 60:
        return {}
    rets = prices.pct_change().dropna()
    if len(rets) < 30:
        return {}
    ann_factor = 252
    total_ret = (prices.iloc[-1] / prices.iloc[0]) - 1
    years = len(rets) / ann_factor
    ann_ret = (1 + total_ret) ** (1 / years) - 1 if years > 0 else np.nan
    ann_vol = rets.std() * np.sqrt(ann_factor)
    sharpe = (ann_ret - rf) / ann_vol if ann_vol > 0 else np.nan
    downside = rets[rets < 0]
    down_vol = downside.std() * np.sqrt(ann_factor) if len(downside) > 5 else np.nan
    sortino = (ann_ret - rf) / down_vol if down_vol and down_vol > 0 else np.nan
    # Max drawdown
    cum = (1 + rets).cumprod()
    peak = cum.cummax()
    dd = (cum - peak) / peak
    max_dd = dd.min()
    calmar = ann_ret / abs(max_dd) if max_dd < 0 else np.nan
    # 12m momentum
    if len(prices) > 252:
        mom = (prices.iloc[-1] / prices.iloc[-252] - 1) * 100
    else:
        mom = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    return {
        "Ann. Return %": round(ann_ret * 100, 1),
        "Ann. Vol %": round(ann_vol * 100, 1),
        "Sharpe": round(sharpe, 2),
        "Sortino": round(sortino, 2) if not np.isnan(sortino) else None,
        "Calmar": round(calmar, 2) if not np.isnan(calmar) else None,
        "Max DD %": round(max_dd * 100, 1),
        "12m Mom %": round(mom, 1),
    }


def build_price_chart(hist: pd.DataFrame, tickers: list[str], benchmarks: list[str]):
    """Normalized price chart + relative performance."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.65, 0.35],
        subplot_titles=("Normalized Price (start = 100)", "Relative vs XBI (if available)"),
    )
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
              "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    # Normalize
    for i, t in enumerate(tickers):
        if t in hist.columns and hist[t].notna().sum() > 10:
            series = hist[t].dropna()
            norm = series / series.iloc[0] * 100
            fig.add_trace(
                go.Scatter(x=norm.index, y=norm, name=t, line=dict(width=1.8, color=colors[i % len(colors)])),
                row=1, col=1,
            )
    # Relative vs XBI
    if "XBI" in hist.columns:
        xbi = hist["XBI"].dropna()
        for i, t in enumerate([x for x in tickers if x != "XBI"]):
            if t in hist.columns:
                common = hist[[t, "XBI"]].dropna()
                if len(common) > 10:
                    rel = (common[t] / common["XBI"]) / (common[t].iloc[0] / common["XBI"].iloc[0]) * 100
                    fig.add_trace(
                        go.Scatter(x=rel.index, y=rel, name=f"{t}/XBI", line=dict(width=1.2, dash="dot")),
                        row=2, col=1,
                    )
    fig.update_layout(
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Normalized", row=1, col=1)
    fig.update_yaxes(title_text="Rel. to XBI", row=2, col=1)
    return fig


# ---------------------------------------------------------------------------
# Sidebar – Portfolio controls
# ---------------------------------------------------------------------------
st.sidebar.title("Portfolio Controls")
st.sidebar.caption(f"Target total exposure: **$100,000**")

# Editable allocations
st.sidebar.subheader("USD Exposure")
total_usd = 0.0
updated = {}
for t, meta in st.session_state.tickers.items():
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        usd = st.number_input(
            f"{t}",
            min_value=0,
            max_value=100000,
            value=int(meta["usd"]),
            step=500,
            key=f"usd_{t}",
        )
    with col2:
        st.caption(meta["category"][:18])
    updated[t] = {**meta, "usd": usd}
    total_usd += usd

st.session_state.tickers = updated

# Status
diff = total_usd - 100000
if abs(diff) < 1:
    st.sidebar.success(f"Total: ${total_usd:,.0f}  ✓ BALANCED")
elif diff > 0:
    st.sidebar.error(f"Total: ${total_usd:,.0f}  (+${diff:,.0f} over)")
else:
    st.sidebar.warning(f"Total: ${total_usd:,.0f}  (${-diff:,.0f} under)")

# Add / remove ticker
st.sidebar.divider()
st.sidebar.subheader("Universe Management")
new_ticker = st.sidebar.text_input("Add ticker (e.g. VRTX)", "").upper().strip()
if st.sidebar.button("Add ticker") and new_ticker:
    if new_ticker not in st.session_state.tickers:
        st.session_state.tickers[new_ticker] = {
            "name": new_ticker, "category": "Custom", "usd": 0
        }
        st.rerun()

remove_list = [t for t in st.session_state.tickers if t != "CASH"]
to_remove = st.sidebar.selectbox("Remove ticker", [""] + remove_list)
if st.sidebar.button("Remove selected") and to_remove:
    del st.session_state.tickers[to_remove]
    st.rerun()

if st.sidebar.button("🔄 Refresh live data"):
    st.cache_data.clear()
    st.session_state.last_refresh = datetime.now()
    st.rerun()

if st.session_state.last_refresh:
    st.sidebar.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

# ---------------------------------------------------------------------------
# Main title
# ---------------------------------------------------------------------------
st.title("📈 $100k Medium-Term Innovation Portfolio")
st.caption(
    "Live yfinance prices • 5-year risk metrics • Catalysts • Charts • Grok collaboration workspace.  "
    "Strategy: balanced barbell maximizing medium-term returns while respecting post-hype drawdown risk."
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_alloc, tab_perf, tab_charts, tab_cat, tab_notes, tab_grok = st.tabs(
    ["Allocator & Live Prices", "Performance Metrics", "Charts", "Catalysts", "Macro & Sector Notes", "Talk to Grok"]
)

# ===== TAB 1: Allocator & Live Prices =====
with tab_alloc:
    st.subheader("Current Allocation & Live Prices")
    tickers_list = [t for t in st.session_state.tickers if t != "CASH"]
    live_df = fetch_live_prices(tickers_list + ["SPY"])

    rows = []
    for t, meta in st.session_state.tickers.items():
        usd = meta["usd"]
        weight = usd / total_usd * 100 if total_usd > 0 else 0
        if t == "CASH":
            price = 1.0
            chg = 0.0
            shares = usd
        else:
            row = live_df[live_df["Ticker"] == t]
            price = float(row["Price"].iloc[0]) if not row.empty and pd.notna(row["Price"].iloc[0]) else np.nan
            chg = float(row["Change %"].iloc[0]) if not row.empty and pd.notna(row["Change %"].iloc[0]) else np.nan
            shares = usd / price if price and price > 0 else np.nan
        rows.append({
            "Ticker": t,
            "Name / Category": f"{meta['name']} · {meta['category']}",
            "USD Exposure": usd,
            "Weight %": weight,
            "Live Price": price,
            "Day Change %": chg,
            "Approx Shares": shares,
        })
    alloc_df = pd.DataFrame(rows)

    # Format display
    def color_chg(val):
        if pd.isna(val):
            return ""
        color = "green" if val > 0 else "red" if val < 0 else "gray"
        return f"color: {color}"

    st.dataframe(
        alloc_df.style.format({
            "USD Exposure": "${:,.0f}",
            "Weight %": "{:.1f}%",
            "Live Price": "${:,.2f}",
            "Day Change %": "{:+.2f}%",
            "Approx Shares": "{:,.1f}",
        }).map(color_chg, subset=["Day Change %"]),
        use_container_width=True,
        height=420,
    )
    st.metric("Total Portfolio USD", f"${total_usd:,.0f}", delta=f"{diff:+,.0f} vs $100k target")

# ===== TAB 2: Performance Metrics =====
with tab_perf:
    st.subheader("5-Year Risk & Return Metrics (vs Benchmarks)")
    st.caption("Computed from daily adjusted closes. rf = 4%. Higher Sharpe / Sortino / Calmar = better risk-adjusted.")
    all_tickers = list(set(tickers_list + BENCHMARKS))
    hist = fetch_history(all_tickers, years=5)
    if hist.empty:
        st.warning("Could not load historical data. Try refreshing or check ticker symbols.")
    else:
        metrics_rows = []
        for t in all_tickers:
            if t in hist.columns:
                m = compute_metrics(hist[t].dropna())
                if m:
                    m["Ticker"] = t
                    metrics_rows.append(m)
        if metrics_rows:
            mdf = pd.DataFrame(metrics_rows).set_index("Ticker")
            # Reorder columns
            cols = ["Ann. Return %", "Ann. Vol %", "Sharpe", "Sortino", "Calmar", "Max DD %", "12m Mom %"]
            mdf = mdf[[c for c in cols if c in mdf.columns]]
            st.dataframe(
                mdf.style.format("{:.2f}", na_rep="–").background_gradient(
                    subset=["Sharpe", "Sortino", "Calmar"], cmap="RdYlGn"
                ),
                use_container_width=True,
            )
            st.markdown(
                """
                **Definitions**  
                - **Ann. Vol** = std(daily returns) × √252  
                - **Sharpe** = (Ann Return − rf) / Ann Vol  
                - **Sortino** = (Ann Return − rf) / downside deviation  
                - **Calmar** = Ann Return / |Max Drawdown|  
                - **12m Mom** = trailing 12-month price change  
                """
            )
        else:
            st.info("Insufficient history for metrics.")

# ===== TAB 3: Charts =====
with tab_charts:
    st.subheader("Price Action & Relative Performance")
    if not hist.empty:
        chart_tickers = [t for t in tickers_list if t in hist.columns]
        fig = build_price_chart(hist, chart_tickers, BENCHMARKS)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Top: prices normalized to 100 at the start of the window. Bottom: relative strength vs XBI.")
    else:
        st.warning("No history available for charts.")

# ===== TAB 4: Catalysts =====
with tab_cat:
    st.subheader("Key Catalysts — Next ~6 Months")
    st.caption("Edit the table below. Changes stay in session until you refresh the browser. Bring important updates back to Grok chat for deeper analysis.")
    cat_df = pd.DataFrame(st.session_state.catalysts)
    edited = st.data_editor(
        cat_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Importance": st.column_config.SelectboxColumn(
                options=["Very High", "High", "Medium-High", "Medium", "Sector", "Low"]
            )
        },
        key="catalyst_editor",
    )
    if st.button("Save catalyst changes"):
        st.session_state.catalysts = edited.to_dict("records")
        st.success("Catalysts updated in session.")

# ===== TAB 5: Macro & Sector Notes =====
with tab_notes:
    st.subheader("Macro & Portfolio Philosophy")
    st.session_state.macro_notes = st.text_area(
        "Macro / strategy notes (editable)",
        value=st.session_state.macro_notes,
        height=150,
    )
    st.subheader("Sector Analysis Snapshot")
    st.session_state.sector_notes = st.text_area(
        "Sector thoughts (editable)",
        value=st.session_state.sector_notes,
        height=200,
    )
    st.info(
        "These notes are stored only in the current browser session. "
        "Copy important insights into the Grok chat so they can be refined and versioned."
    )

# ===== TAB 6: Talk to Grok =====
with tab_grok:
    st.subheader("Collaborate with Grok (xAI)")
    st.markdown(
        """
        This app runs locally / in your environment. To get live reasoning, updated catalysts, 
        new stock ideas, or macro views from Grok:

        1. Copy the prompt template below (it already includes your current portfolio snapshot).  
        2. Paste it into this chat (or a new Grok conversation).  
        3. Ask for updates, risk checks, rebalancing suggestions, or fresh sector analysis.  
        4. Bring the answers back and paste them into the Catalysts or Notes tabs.
        """
    )
    # Build a ready-to-copy prompt
    snapshot = []
    for t, meta in st.session_state.tickers.items():
        snapshot.append(f"- {t}: ${meta['usd']:,} ({meta['category']})")
    prompt = f"""Current $100k portfolio snapshot (as of {datetime.now().strftime('%Y-%m-%d %H:%M')}):

{chr(10).join(snapshot)}

Total exposure: ${total_usd:,.0f}

Current catalysts (first few):
{chr(10).join([f"- {c['Ticker']}: {c['Catalyst']} ({c['Timing']})" for c in st.session_state.catalysts[:5]])}

Macro notes:
{st.session_state.macro_notes[:300]}...

Please:
1. Review the allocation for medium-term (1-5y) balance and post-hype risk.
2. Update or add any high-priority catalysts for the next 6 months.
3. Suggest any ticker additions or reductions with rationale.
4. Give a short sector / macro view relevant to biotech, gene editing, quantum, and obesity/healthspan.
"""
    st.code(prompt, language="markdown")
    st.button("📋 Prompt ready — copy it and paste into Grok chat")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Data via yfinance (Yahoo Finance). Not investment advice. "
    "Past performance ≠ future results. Clinical catalysts are binary and timelines can slip. "
    "Always verify the latest company guidance and filings."
)
