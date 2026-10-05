from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="ZIPTO | Dark Store Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ROOT = Path(__file__).parent
# DATA_DIR = ROOT / "data"
# if not DATA_DIR.exists():
#     DATA_DIR = ROOT  # supports running beside CSVs too
# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# CSV files are inside analysis_data/
DATA_DIR = BASE_DIR / "analysis_data"


# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#090e17; --panel:#111a28; --panel2:#151f30; --line:#263449; --text:#edf4ff; --muted:#93a4ba; --cyan:#52e0d0; --blue:#7aa8ff; --red:#ff758f; --amber:#ffc66d; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 18% 0%, #17283a 0%, #0b1220 42%, #080d16 100%); color:var(--text); }
[data-testid="stHeader"] { background:rgba(8,13,22,.78); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1725,#0a101b); border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { padding-top:1.7rem; padding-bottom:3rem; max-width:1500px; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em; color:#f2f7ff; }
h1 { font-size:2.4rem !important; }
p, label, .stMarkdown { color:#d7e1ef; }
small, .muted { color:var(--muted) !important; }
.hero {
  background:linear-gradient(115deg,rgba(82,224,208,.13),rgba(122,168,255,.10) 55%,rgba(255,117,143,.08));
  border:1px solid rgba(104,170,194,.28); border-radius:22px; padding:25px 28px; margin:4px 0 22px;
  box-shadow:0 16px 50px rgba(0,0,0,.18);
}
.eyebrow { text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; color:var(--cyan); font-weight:700; }
.hero-title { font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:700; line-height:1.15; margin:.5rem 0; color:#f5f8ff; }
.hero-copy { color:#b9c8dc; font-size:.98rem; max-width:850px; }
.section-label { color:var(--cyan); font-size:.75rem; letter-spacing:.13em; text-transform:uppercase; font-weight:700; margin-bottom:.3rem; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#152235,#101927); border:1px solid #29384d; padding:17px 18px; border-radius:17px; box-shadow:0 10px 24px rgba(0,0,0,.14); }
[data-testid="stMetricLabel"] { color:#9fb0c6 !important; font-size:.82rem !important; }
[data-testid="stMetricValue"] { color:#f4f8ff !important; font-family:'Space Grotesk',sans-serif; }
[data-testid="stMetricDelta"] { font-size:.8rem; }
div[data-testid="stPlotlyChart"] { background:#101927; border:1px solid #263449; border-radius:18px; padding:8px; }
div[data-testid="stDataFrame"] { border:1px solid #263449; border-radius:14px; overflow:hidden; }
.stButton>button { border-radius:11px; border:1px solid #31566b; background:linear-gradient(100deg,#174b54,#1a3a58); color:#f5ffff; font-weight:600; }
.stButton>button:hover { border-color:var(--cyan); color:white; }
.stSelectbox [data-baseweb="select"] > div { background:#111a28; border-color:#2b3b50; }
hr { border-color:#263449; }
div[data-testid="stAlert"] { border-radius:14px; }
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
FILES = {
    "performance": "store_performance.csv",
    "delivery_summary": "store_delivery_summary_powerbi.csv",
    "delivery_detail": "delivery_analysis.csv",
    "cohort": "cohort_summary.csv",
    "return_opportunity": "return_opportunity.csv",
    "product": "product_profitability.csv",
    "category": "category_profitability.csv",
    "promo": "promo_analysis.csv",
    "fresh50": "fresh50_summary.csv",
}


@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        st.warning(f"File not found: {path}")
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.warning(f"Could not read {filename}: {exc}")
        return None


data = {key: load_csv(filename) for key, filename in FILES.items()}

perf = data["performance"]
delivery = data["delivery_summary"]
delivery_detail = data["delivery_detail"]
cohort = data["cohort"]
return_opportunity = data["return_opportunity"]
product = data["product"]
category = data["category"]
promo = data["promo"]
fresh50 = data["fresh50"]

# Detect percent columns stored either as fractions (0.14) or percentages (14.0)
def pct_value(value):
    if pd.isna(value): return "—"
    value = float(value)
    if abs(value) > 1: value /= 100
    return f"{value:.1%}"

def normalize_percent(series):
    s = pd.to_numeric(series, errors="coerce")
    if s.dropna().empty: return s
    if s.dropna().abs().quantile(.75) > 1:
        s = s / 100
    return s

def money(value):
    if pd.isna(value): return "—"
    return f"₹{float(value):,.0f}"

def find_col(df, *needles):
    if df is None: return None
    for col in df.columns:
        c = col.lower().replace(" ", "_")
        if all(n in c for n in needles):
            return col
    return None

def numeric(df, col):
    return pd.to_numeric(df[col], errors="coerce") if df is not None and col in df.columns else pd.Series(dtype=float)

def polish(fig, height=360):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans", color="#dce7f5"),
        title=dict(font=dict(family="Space Grotesk", size=17, color="#f2f7ff")),
        margin=dict(l=18,r=18,t=58,b=20), legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="#243247", zerolinecolor="#34445a"),
        yaxis=dict(gridcolor="#243247", zerolinecolor="#34445a"),
    )
    return fig

def chart_or_empty(fig, key):
    st.plotly_chart(polish(fig), use_container_width=True, config={"displayModeBar": False}, key=key)

missing = [name for name in FILES.values() if not (DATA_DIR / name).exists()]
if perf is None or delivery is None:
    st.error("Core data files not found. Put all CSVs in the project's data/ folder.")
    st.code("zipto_decision_app/data/store_performance.csv\nzipto_decision_app/data/store_delivery_summary_powerbi.csv")
    st.stop()

# Basic schema resilience
for col in ["return_rate", "cancellation_rate"]:
    if col in perf.columns: perf[col] = normalize_percent(perf[col])
for col in ["late_delivery_rate", "return_rate"]:
    if col in delivery.columns: delivery[col] = normalize_percent(delivery[col])
for df in [perf, delivery]:
    if "store_id" in df.columns: df["store_id"] = df["store_id"].astype(str)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="eyebrow">ZIPTO / OPERATIONS INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown("## 📦 Dark Store OS")
    st.caption("COO decision cockpit · May–June 2026")
    page = st.radio("WORKSPACE", [
        "Executive Overview", "Store Performance", "Delivery & Fulfilment",
        "Partner Cohorts", "Product Profitability", "Promotions", "Action Centre"
    ], label_visibility="visible")
    st.divider()
    available = sum(v is not None for v in data.values())
    st.markdown(f"**Data readiness**  \n{available}/{len(FILES)} datasets detected")
    st.progress(available / len(FILES))
    if missing:
        st.caption("Missing files: " + ", ".join(missing))
    else:
        st.caption("All 9 expected datasets are present.")
    st.markdown("---")
    st.caption("Decision support, not automated decision-making. Validate causes before scaling actions.")

# ---------- Header ----------
st.markdown('<div class="eyebrow">QUICK COMMERCE · COO COMMAND CENTRE</div>', unsafe_allow_html=True)
st.title(page)
st.caption("Store economics • fulfilment reliability • product margin • promotion efficiency")

# ---------- Pages ----------
if page == "Executive Overview":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">THE OPERATING PICTURE</div>
      <div class="hero-title">Spot the leaks. Protect contribution. Scale what works.</div>
      <div class="hero-copy">A unified view of store P&L, delivery reliability, returns and promotion economics. Start with the biggest risks, then test changes against measurable outcomes.</div>
    </div>""", unsafe_allow_html=True)
    orders = numeric(perf, "total_orders").sum()
    contribution = numeric(perf, "contribution").sum()
    pnl_col = find_col(perf, "store_pnl")
    worst = perf.loc[numeric(perf, pnl_col).idxmin()] if pnl_col else None
    late_col = find_col(delivery, "late_delivery_rate")
    ret_col = find_col(delivery, "return_rate")
    avg_late = normalize_percent(delivery[late_col]).mean() if late_col else float("nan")
    avg_return = normalize_percent(delivery[ret_col]).mean() if ret_col else float("nan")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("ORDERS IN SCOPE", f"{orders:,.0f}")
    k2.metric("CONTRIBUTION · PRE-RENT", money(contribution))
    k3.metric("WEAKEST STORE P&L", f"{worst['store_id']} · {money(worst[pnl_col])}" if worst is not None else "—")
    k4.metric("AVG STORE LATE RATE", pct_value(avg_late))
    left,right = st.columns([1.15,1])
    with left:
        if pnl_col:
            fig = px.bar(perf.sort_values(pnl_col), x="store_id", y=pnl_col, color=pnl_col,
                         color_continuous_scale=[[0,"#ff758f"],[.5,"#ffc66d"],[1,"#52e0d0"]],
                         title="Store P&L after rent", hover_data=["total_orders"] if "total_orders" in perf.columns else None)
            fig.add_hline(y=0, line_dash="dash", line_color="#8fa3bb")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Dark store", yaxis_title="P&L (₹)")
            chart_or_empty(fig, "overview_pnl")
    with right:
        st.markdown('<div class="section-label">PRIORITY SIGNALS</div>', unsafe_allow_html=True)
        st.markdown("### Where to look first")
        st.markdown("""
        **01 · S07 — stabilize returns and unit economics**  
        Highest-priority diagnostic based on negative P&L, returns and delivery cost.

        **02 · S03 — investigate fulfilment and returns**  
        Elevated late rate, returns and delivery cost merit a focused operational audit.

        **03 · S09 — understand rent and volume**  
        A different pattern: loss-making despite closer-to-benchmark delivery metrics.
        """)
        st.info("These are diagnostic signals, not proof of causation. Validate operational causes before claiming savings.")
    st.markdown('<div class="section-label">NETWORK SCORECARD</div>', unsafe_allow_html=True)
    cols = [c for c in ["store_id","total_orders","contribution","rent_for_period","store_pnl","contribution_per_order","return_rate","delivery_cost_per_order"] if c in perf.columns]
    score = perf[cols].copy()
    if "return_rate" in score: score["return_rate"] = score["return_rate"].map(pct_value)
    for c in ["contribution","rent_for_period","store_pnl","contribution_per_order","delivery_cost_per_order"]:
        if c in score: score[c] = score[c].map(money)
    st.dataframe(score, use_container_width=True, hide_index=True)

elif page == "Store Performance":
    st.markdown('<div class="hero"><div class="eyebrow">LANE 01 / STORE ECONOMICS</div><div class="hero-title">Profitability is more than revenue.</div><div class="hero-copy">Compare contribution after operating costs with rent burden, returns and per-order economics.</div></div>', unsafe_allow_html=True)
    pnl_col = find_col(perf, "store_pnl")
    stores = sorted(perf["store_id"].unique())
    default_idx = stores.index("S07") if "S07" in stores else 0
    chosen = st.selectbox("Inspect a store", stores, index=default_idx)
    row = perf.loc[perf["store_id"] == chosen].iloc[0]
    a,b,c,d = st.columns(4)
    a.metric("P&L AFTER RENT", money(row.get("store_pnl", float("nan"))))
    b.metric("CONTRIBUTION / ORDER", money(row.get("contribution_per_order", float("nan"))))
    c.metric("RETURN RATE", pct_value(row.get("return_rate", float("nan"))))
    d.metric("DELIVERY COST / ORDER", money(row.get("delivery_cost_per_order", float("nan"))))
    left,right = st.columns(2)
    with left:
        fig = px.bar(perf.sort_values(pnl_col), x="store_id", y=pnl_col, color=pnl_col,
                     color_continuous_scale=[[0,"#ff758f"],[.5,"#ffc66d"],[1,"#52e0d0"]], title="P&L by store")
        fig.add_hline(y=0, line_dash="dash", line_color="#8fa3bb")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="P&L (₹)")
        chart_or_empty(fig, "store_pnl")
    with right:
        if "return_rate" in perf.columns and "contribution_per_order" in perf.columns:
            fig = px.scatter(perf, x="return_rate", y="contribution_per_order",
                size="total_orders" if "total_orders" in perf.columns else None,
                color="store_pnl" if "store_pnl" in perf.columns else None,
                hover_name="store_id", color_continuous_scale=[[0,"#ff758f"],[.5,"#ffc66d"],[1,"#52e0d0"]],
                title="Return rate vs contribution per order")
            fig.update_xaxes(tickformat=".0%")
            chart_or_empty(fig, "store_scatter")
    if chosen in ["S07","S03"]:
        st.warning(f"{chosen} is a priority diagnostic store. Review return reasons, partner allocation, trip timestamps and item/order economics before attributing cause.")
    elif row.get("store_pnl", 0) < 0:
        st.info(f"{chosen} is loss-making after rent. Check rent coverage and order volume as well as operational efficiency.")
    else:
        st.success(f"{chosen} is positive after rent in this analysis window. Continue monitoring contribution and service quality.")
    st.dataframe(perf.sort_values(pnl_col), use_container_width=True, hide_index=True)

elif page == "Delivery & Fulfilment":
    st.markdown('<div class="hero"><div class="eyebrow">LANE 02 / LAST-MILE OPERATIONS</div><div class="hero-title">Fast is good. Reliable and economical is better.</div><div class="hero-copy">Locate stores with elevated late deliveries and returns. Treat the patterns as investigation leads, not causal conclusions.</div></div>', unsafe_allow_html=True)
    avg_time = numeric(delivery,"avg_delivery_minutes").mean()
    late_col, ret_col = find_col(delivery,"late_delivery_rate"), find_col(delivery,"return_rate")
    avg_late = normalize_percent(delivery[late_col]).mean() if late_col else float("nan")
    avg_ret = normalize_percent(delivery[ret_col]).mean() if ret_col else float("nan")
    x,y,z = st.columns(3)
    x.metric("AVG DELIVERY TIME", f"{avg_time:.2f} min")
    y.metric("AVG STORE LATE RATE", pct_value(avg_late))
    z.metric("AVG STORE RETURN RATE", pct_value(avg_ret))
    left,right = st.columns(2)
    with left:
        fig = px.bar(delivery.sort_values(late_col,ascending=False), x="store_id", y=late_col,
                     color=late_col, color_continuous_scale=[[0,"#52e0d0"],[.5,"#ffc66d"],[1,"#ff758f"]],
                     title="Late-delivery rate by store")
        fig.update_yaxes(tickformat=".0%")
        fig.update_layout(coloraxis_showscale=False)
        chart_or_empty(fig, "delivery_late")
    with right:
        if "avg_delivery_minutes" in delivery and ret_col:
            fig = px.scatter(delivery, x="avg_delivery_minutes", y=ret_col,
                size="total_orders" if "total_orders" in delivery else None,
                color="avg_delivery_cost" if "avg_delivery_cost" in delivery else None,
                hover_name="store_id", color_continuous_scale="OrRd", title="Delivery time vs return rate")
            fig.update_yaxes(tickformat=".0%")
            chart_or_empty(fig, "delivery_scatter")
    st.markdown('<div class="section-label">STORE COMPARISON</div>', unsafe_allow_html=True)
    focus = delivery[delivery["store_id"].isin(["S03","S07"])].copy()
    st.dataframe(focus, use_container_width=True, hide_index=True)
    st.warning("A store-level relationship does not prove lateness caused returns. Validate return reasons and timestamp quality before blaming a partner or process.")
    if delivery_detail is not None:
        st.markdown('<div class="section-label">ORDER-LEVEL DETAIL</div>', unsafe_allow_html=True)
        st.caption(f"Loaded {len(delivery_detail):,} delivery-analysis rows.")
        st.dataframe(delivery_detail.head(100), use_container_width=True, hide_index=True)
        st.caption("Showing the first 100 rows for responsiveness.")

elif page == "Partner Cohorts":
    st.markdown('<div class="hero"><div class="eyebrow">PARTNER COHORT INVESTIGATION</div><div class="hero-title">Find patterns before assigning blame.</div><div class="hero-copy">Compare return rates and modeled opportunity across partner cohorts when the export contains those fields.</div></div>', unsafe_allow_html=True)
    if cohort is None:
        st.info("cohort_summary.csv is not detected in data/. Check the filename and refresh.")
    else:
        st.metric("COHORT ROWS", f"{len(cohort):,}")
        st.dataframe(cohort, use_container_width=True, hide_index=True)
        rate_col = find_col(cohort,"return_rate") or find_col(cohort,"return","rate")
        label_col = find_col(cohort,"cohort") or find_col(cohort,"partner")
        if rate_col and label_col:
            fig = px.bar(cohort, x=label_col, y=rate_col, color=rate_col,
                         color_continuous_scale="OrRd", title="Return rate by partner/cohort")
            fig.update_layout(coloraxis_showscale=False)
            fig.update_yaxes(tickformat=".0%")
            chart_or_empty(fig, "cohort_rates")
    if return_opportunity is not None:
        st.markdown('<div class="section-label">MODELED RETURN-COST OPPORTUNITY</div>', unsafe_allow_html=True)
        st.dataframe(return_opportunity, use_container_width=True, hide_index=True)
        st.caption("Scenario estimates are not guaranteed savings; validate cohort definitions and timestamp semantics.")

elif page == "Product Profitability":
    st.markdown('<div class="hero"><div class="eyebrow">LANE 03 / ASSORTMENT ECONOMICS</div><div class="hero-title">Not all sales create equal value.</div><div class="hero-copy">Separate item gross profit from full order contribution; discounts, returns and delivery cost may not be allocated to SKU.</div></div>', unsafe_allow_html=True)
    if category is not None:
        st.subheader("Category profitability")
        st.dataframe(category, use_container_width=True, hide_index=True)
        gp_col = find_col(category,"gross_profit") or find_col(category,"gross","profit") or find_col(category,"gp")
        cat_col = find_col(category,"category") or category.columns[0]
        if gp_col:
            fig = px.bar(category.sort_values(gp_col), x=gp_col, y=cat_col, orientation="h",
                         color=gp_col, color_continuous_scale=[[0,"#ff758f"],[.5,"#ffc66d"],[1,"#52e0d0"]],
                         title="Gross profit by category")
            fig.update_layout(coloraxis_showscale=False)
            chart_or_empty(fig, "category_gp")
    if product is not None:
        st.subheader("Product profitability")
        gp_col = find_col(product,"gross_profit") or find_col(product,"gross","profit") or find_col(product,"gp")
        product_col = find_col(product,"product") or find_col(product,"sku") or product.columns[0]
        if gp_col:
            st.dataframe(product.sort_values(gp_col), use_container_width=True, hide_index=True)
            fig = px.bar(product.sort_values(gp_col).head(12), x=gp_col, y=product_col, orientation="h",
                         color=gp_col, color_continuous_scale=[[0,"#ff758f"],[.5,"#ffc66d"],[1,"#52e0d0"]],
                         title="Lowest gross-profit products (first 12)")
            fig.update_layout(coloraxis_showscale=False)
            chart_or_empty(fig, "product_gp")
        else:
            st.dataframe(product, use_container_width=True, hide_index=True)
    if category is None and product is None:
        st.info("Add product_profitability.csv and category_profitability.csv under data/.")

elif page == "Promotions":
    st.markdown('<div class="hero"><div class="eyebrow">PROMOTION EFFICIENCY</div><div class="hero-title">Growth is only useful when the unit economics work.</div><div class="hero-copy">Review discount exposure and contribution before changing eligibility, minimum basket or targeting.</div></div>', unsafe_allow_html=True)
    if fresh50 is not None:
        st.subheader("FRESH50 summary")
        st.dataframe(fresh50, use_container_width=True, hide_index=True)
    if promo is not None:
        st.subheader("Promotion by store")
        st.dataframe(promo, use_container_width=True, hide_index=True)
        cont_col = find_col(promo,"contribution")
        promo_col = find_col(promo,"promo") or find_col(promo,"code") or promo.columns[0]
        if cont_col:
            fig = px.bar(promo, x=promo_col, y=cont_col, color=cont_col,
                         color_continuous_scale=[[0,"#ff758f"],[.5,"#ffc66d"],[1,"#52e0d0"]],
                         title="Contribution by promotion")
            fig.update_layout(coloraxis_showscale=False)
            chart_or_empty(fig, "promo_contribution")
    if fresh50 is None and promo is None:
        st.info("Add promo_analysis.csv and fresh50_summary.csv under data/.")
    st.warning("Promotion-level results are observational. Test changes with a controlled pilot and measure contribution, volume, returns and repeat purchase.")

else:  # Action Centre
    st.markdown('<div class="hero"><div class="eyebrow">FROM ANALYSIS TO ACTION</div><div class="hero-title">Three priorities. One disciplined operating loop.</div><div class="hero-copy">Assign owners, test small, measure cleanly, then scale only if the effect persists.</div></div>', unsafe_allow_html=True)
    st.markdown("### <span style='color:#ff758f'>01</span> · S07 — return and unit-economics audit", unsafe_allow_html=True)
    st.write("Review return reasons, partner allocation, trip timestamps, and item/order economics. Avoid assuming late delivery caused returns.")
    st.markdown("### <span style='color:#ffc66d'>02</span> · S03 — fulfilment and return investigation", unsafe_allow_html=True)
    st.write("Inspect the partner-cohort pattern and timestamp quality with operations before attributing losses to specific partners.")
    st.markdown("### <span style='color:#52e0d0'>03</span> · S09 — rent and volume diagnosis", unsafe_allow_html=True)
    st.write("Review volume, rent burden, staffing and trading-hour utilization; the evidence suggests a different problem from S07.")
    st.divider()
    st.markdown("### Controlled pilot checklist")
    for item in [
        "Record a consistent reason for each return.",
        "Audit a sample of partner trips and timestamp sequences.",
        "Change one process at a time in a limited store/shift cohort.",
        "Compare return rate, contribution/order, delivery cost/order and customer experience.",
        "Roll out only after data checks and sustained results.",
    ]:
        st.checkbox(item, key="action_" + item[:18])
    st.caption("Do not add overlapping financial opportunity scenarios together. Modeled opportunity is not guaranteed savings.")

st.divider()
st.markdown('<div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;color:#8396ad;font-size:.8rem"><span>ZIPTO · DARK STORE INTELLIGENCE</span><span>Evidence first · Validate before scaling</span></div>', unsafe_allow_html=True)
