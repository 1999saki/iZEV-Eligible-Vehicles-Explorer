import io
import re
import numpy as np
import pandas as pd
from datetime import date
from typing import Dict, List, Tuple
from dateutil import parser as dtparser
import streamlit as st

# ========= CONFIG =========
CSV_PATH = "eligible_vehicles_all_pages.csv"   # change if needed
PAGE_SIZE_DEFAULT = 30
TITLE = "Canada iZEV — Eligible Vehicles Explorer"
SUBTITLE = "Filter models, compare incentives, and download results"
# ==========================

st.set_page_config(page_title=TITLE, layout="wide")

# ---------- helpers ----------
def _col_like(df: pd.DataFrame, *patterns: str) -> str | None:
    """Return first column whose name matches any regex in patterns (case-insensitive)."""
    for pat in patterns:
        m = df.columns[df.columns.str.contains(pat, case=False, regex=True)]
        if len(m):
            return m[0]
    return None

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normalize checkmarks to booleans
    df = df.replace({"✓": True, "✗": False, "Yes": True, "No": False})

    # Clean money-ish columns to numeric
    money_mask = df.columns.str.contains(r"\$|incentive|msrp|price|lease", case=False, regex=True)
    for c in df.columns[money_mask]:
        df[c] = (
            df[c].astype(str)
                 .str.replace(r"[^\d.\-]", "", regex=True)
                 .replace({"": np.nan})
        ).astype(float)

    # Try parse date column
    date_col = _col_like(df, r"eligibility.*date", r"\bdate\b")
    if date_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        except Exception:
            pass

    # Cast model year to numeric if present
    year_col = _col_like(df, r"model\s*year|year\b")
    if year_col:
        df[year_col] = pd.to_numeric(df[year_col].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")

    return df

def kpi_number(x) -> str:
    if pd.isna(x):
        return "—"
    if abs(float(x)) >= 1000:
        return f"{float(x):,.0f}"
    return f"{float(x):,.2f}" if isinstance(x, float) and not float(x).is_integer() else f"{int(x)}"

def download_button(df: pd.DataFrame, label="Download filtered CSV", filename="eligible_vehicles_filtered.csv"):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="text/csv")

# ---------- header ----------
left, right = st.columns([0.8, 0.2])
with left:
    st.markdown(f"## {TITLE}")
    st.caption(SUBTITLE)
with right:
    page_size = st.number_input("Rows per page", min_value=10, max_value=500, value=PAGE_SIZE_DEFAULT, step=10, help="Affects the table below.")

# ---------- data source ----------
src1, src2 = st.columns([1.1, 2])
with src1:
    source = st.radio("Data source", ["Use default CSV", "Upload CSV"], horizontal=True)
with src2:
    pass

if source == "Upload CSV":
    up = st.file_uploader("Upload iZEV CSV", type=["csv"])
    if not up:
        st.stop()
    df_raw = pd.read_csv(up)
else:
    try:
        df_raw = load_data(CSV_PATH)
    except FileNotFoundError:
        st.error(f"CSV not found at '{CSV_PATH}'. Upload a CSV or update CSV_PATH.")
        st.stop()

# Identify relevant columns once
COL_YEAR   = _col_like(df_raw, r"model\s*year|year\b")
COL_MAKE   = _col_like(df_raw, r"^make$")
COL_MODEL  = _col_like(df_raw, r"^model$")
COL_TRIM   = _col_like(df_raw, r"trim")
COL_FUEL   = _col_like(df_raw, r"fuel\s*type")
COL_RANGE50 = _col_like(df_raw, r"electric.*50\s*km|>=\s*50")
COL_DATE   = _col_like(df_raw, r"eligibility.*date", r"\bdate\b")

INC_PUR48  = _col_like(df_raw, r"incentive.*(purchase|48).*lease")
INC_36     = _col_like(df_raw, r"incentive.*36")
INC_24     = _col_like(df_raw, r"incentive.*24")
INC_12     = _col_like(df_raw, r"incentive.*12")

# ---------- sidebar filters (only relevant ones) ----------
st.sidebar.header("Filters")

# Text search
q = st.sidebar.text_input("Search (all columns)")

# Make / Model (dependent)
if COL_MAKE and COL_MODEL:
    makes = sorted(df_raw[COL_MAKE].dropna().astype(str).unique().tolist())
    sel_makes = st.sidebar.multiselect("Make", makes)
    df_tmp = df_raw if not sel_makes else df_raw[df_raw[COL_MAKE].astype(str).isin(sel_makes)]
    models = sorted(df_tmp[COL_MODEL].dropna().astype(str).unique().tolist())
    sel_models = st.sidebar.multiselect("Model", models)
else:
    sel_makes, sel_models = [], []

# Year range
if COL_YEAR and df_raw[COL_YEAR].notna().any():
    y_min, y_max = int(df_raw[COL_YEAR].min()), int(df_raw[COL_YEAR].max())
    yr_lo, yr_hi = st.sidebar.slider("Model year", min_value=y_min, max_value=y_max, value=(y_min, y_max))
else:
    yr_lo = yr_hi = None

# Fuel type
if COL_FUEL:
    fuels = sorted(df_raw[COL_FUEL].dropna().astype(str).unique().tolist())
    sel_fuels = st.sidebar.multiselect("Fuel Type", fuels)
else:
    sel_fuels = []

# Must have >=50km electric range (if that boolean exists)
must_50 = False
if COL_RANGE50 and df_raw[COL_RANGE50].notna().any():
    must_50 = st.sidebar.checkbox("Electric range ≥ 50 km", value=False)

# Date range slider (if we have a date col)
if COL_DATE and df_raw[COL_DATE].notna().any():
    dt_min = df_raw[COL_DATE].min().date()
    dt_max = df_raw[COL_DATE].max().date()
    d_lo, d_hi = st.sidebar.slider("Eligibility date", min_value=dt_min, max_value=dt_max, value=(dt_min, dt_max))
else:
    d_lo = d_hi = None

# Incentive min/max (use purchase/48mo if present, fallback to max among known columns)
money_cols = [c for c in [INC_PUR48, INC_36, INC_24, INC_12] if c]
if money_cols:
    money_stack = df_raw[money_cols].max(axis=1, skipna=True)
    mmin, mmax = float(np.nanmin(money_stack)), float(np.nanmax(money_stack))
    m_lo, m_hi = st.sidebar.slider("Max incentive (any term)", min_value=float(mmin), max_value=float(mmax), value=(float(mmin), float(mmax)))
else:
    m_lo = m_hi = None

# Clear filters
if st.sidebar.button("Clear filters"):
    st.experimental_rerun()

# ---------- apply filters ----------
df = df_raw.copy()

if q:
    mask = pd.Series(False, index=df.index)
    for c in df.columns:
        mask |= df[c].astype(str).str.contains(q, case=False, na=False)
    df = df[mask]

if sel_makes and COL_MAKE:
    df = df[df[COL_MAKE].astype(str).isin(sel_makes)]
if sel_models and COL_MODEL:
    df = df[df[COL_MODEL].astype(str).isin(sel_models)]
if yr_lo is not None and yr_hi is not None and COL_YEAR:
    df = df[(df[COL_YEAR].fillna(yr_lo).astype(float) >= yr_lo) & (df[COL_YEAR].fillna(yr_hi).astype(float) <= yr_hi)]
if sel_fuels and COL_FUEL:
    df = df[df[COL_FUEL].astype(str).isin(sel_fuels)]
if must_50 and COL_RANGE50:
    df = df[df[COL_RANGE50] == True]
if d_lo and d_hi and COL_DATE:
    df = df[(df[COL_DATE] >= pd.to_datetime(d_lo)) & (df[COL_DATE] <= pd.to_datetime(d_hi))]
if m_lo is not None and m_hi is not None and money_cols:
    cap = df[money_cols].max(axis=1, skipna=True)
    df = df[(cap.fillna(m_lo) >= m_lo) & (cap.fillna(m_hi) <= m_hi)]

# ---------- KPIs ----------
kpi1 = len(df[COL_MAKE].unique()) if COL_MAKE else np.nan
kpi2 = len(df[COL_MODEL].unique()) if COL_MODEL else np.nan
kpi3 = df[money_cols].max(axis=1, skipna=True).max() if money_cols else np.nan

k1, k2, k3 = st.columns(3)
k1.metric("Makes", kpi_number(kpi1))
k2.metric("Models", kpi_number(kpi2))
k3.metric("Highest incentive (any term)", f"${kpi_number(kpi3)}" if not pd.isna(kpi3) else "—")

st.success(f"{len(df):,} rows matched (of {len(df_raw):,})")
download_button(df)

# ---------- results table ----------
# Choose nice column order if we recognize them
preferred = [c for c in [COL_YEAR, COL_MAKE, COL_MODEL, COL_TRIM, COL_FUEL, COL_RANGE50, INC_PUR48, INC_36, INC_24, INC_12, COL_DATE] if c]
other = [c for c in df.columns if c not in preferred]
df_display = df[preferred + other] if preferred else df

# paging
page_count = max(1, int(np.ceil(len(df_display) / page_size)))
pg = 1 if page_count == 1 else st.slider("Page", 1, page_count, 1)
start = (pg - 1) * page_size
end = start + page_size
st.dataframe(df_display.iloc[start:end], use_container_width=True)

# ---------- Summary ----------
st.markdown("### Summary")

tab1, tab2, tab3 = st.tabs(["Top makes", "Fuel mix", "Best incentives"])

# Top makes table (count + avg/max incentive)
with tab1:
    if COL_MAKE:
        tmp = df.copy()
        if money_cols:
            tmp["max_incentive_any"] = tmp[money_cols].max(axis=1, skipna=True)
        g = tmp.groupby(COL_MAKE, dropna=False).agg(
            models=(COL_MODEL, "nunique") if COL_MODEL else (COL_MAKE, "size"),
            rows=("__dummy__", "size") if "__dummy__" in tmp else (COL_MAKE, "size"),
            avg_incentive=("max_incentive_any", "mean") if "max_incentive_any" in tmp else (COL_MAKE, "size"),
            max_incentive=("max_incentive_any", "max") if "max_incentive_any" in tmp else (COL_MAKE, "size"),
        )
        # Clean weird agg names
        g = g.rename(columns={"rows": "count"})
        g = g.sort_values("count", ascending=False).head(15)
        g["avg_incentive"] = g["avg_incentive"].map(lambda v: f"${kpi_number(v)}" if not pd.isna(v) else "—")
        g["max_incentive"] = g["max_incentive"].map(lambda v: f"${kpi_number(v)}" if not pd.isna(v) else "—")
        st.dataframe(g, use_container_width=True)
    else:
        st.info("Make column not found.")

# Fuel mix
with tab2:
    if COL_FUEL:
        mix = df[COL_FUEL].fillna("Unknown").value_counts(dropna=False).to_frame("count")
        st.dataframe(mix, use_container_width=True)
        st.bar_chart(mix)  # quick visual
    else:
        st.info("Fuel Type column not found.")

# Best incentives (top 20 rows with highest 'any-term' incentive)
with tab3:
    if money_cols:
        tmp = df.assign(max_incentive_any=df[money_cols].max(axis=1, skipna=True))
        cols_show = [c for c in [COL_MAKE, COL_MODEL, COL_TRIM, COL_YEAR, COL_FUEL, COL_DATE] if c]
        cols_show += money_cols
        cols_show = list(dict.fromkeys(cols_show))  # keep order, unique
        top = tmp.sort_values("max_incentive_any", ascending=False).head(20)
        st.dataframe(top[cols_show], use_container_width=True)
    else:
        st.info("No incentive columns detected.")