#!/usr/bin/env python3
"""
╔==========================================================================╗
║  Tesla (TSLA) — Financial Ratio Analysis & Visualization Engine        ║
║  Bain & Company M&A Readiness Portfolio Project                        ║
║  Date: September 2026                                                  ║
╚==========================================================================╝

Generates publication-quality financial analysis charts from Tesla's
5-year historical data, DCF valuation, and peer comparison.

Usage:
    python ratio_analysis.py

Output:
    output/charts/*.png  — 7 Bain-styled financial charts
    output/analysis_summary.json — Computed valuation data for downstream scripts
    Console executive summary with key insights
"""

import json
import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

# ===========================================================================
# CONFIGURATION
# ===========================================================================

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output" / "charts"
DATA_FILE = ROOT_DIR / "data" / "tesla_financials.json"

# Bain & Company inspired color palette
C = {
    "red":         "#CC0000",
    "dark_red":    "#990000",
    "navy":        "#003366",
    "blue":        "#0066CC",
    "light_blue":  "#4D94DB",
    "grey":        "#666666",
    "light_grey":  "#E0E0E0",
    "dark":        "#1A1A2E",
    "green":       "#2E7D32",
    "light_green": "#66BB6A",
    "amber":       "#EF6C00",
    "white":       "#FFFFFF",
}


def setup_style():
    """Configure Matplotlib for Bain-quality presentation charts."""
    plt.rcParams.update({
        "font.family":        "sans-serif",
        "font.sans-serif":    ["Calibri", "Arial", "Helvetica Neue", "DejaVu Sans"],
        "font.size":          11,
        "axes.titlesize":     15,
        "axes.titleweight":   "bold",
        "axes.titlepad":      20,
        "axes.labelsize":     11,
        "axes.labelweight":   "normal",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.linewidth":     0.8,
        "axes.grid":          True,
        "grid.alpha":         0.25,
        "grid.linewidth":     0.5,
        "grid.linestyle":     "--",
        "xtick.major.size":   0,
        "ytick.major.size":   4,
        "figure.facecolor":   C["white"],
        "axes.facecolor":     C["white"],
        "figure.dpi":         150,
        "savefig.dpi":        200,
        "savefig.bbox":       "tight",
        "savefig.pad_inches": 0.4,
        "legend.frameon":     False,
        "legend.fontsize":    10,
    })


# ===========================================================================
# DATA LOADING & RATIO COMPUTATION
# ===========================================================================

def load_data() -> dict:
    """Load Tesla financial data from JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  + Loaded data for {data['company']} ({data['ticker']})")
    return data


def compute_ratios(data: dict) -> dict:
    """Compute all financial ratios and derived metrics."""
    inc = data["income_statement"]
    bs  = data["balance_sheet"]
    cf  = data["cash_flow_statement"]
    years = data["fiscal_years"]

    revenue   = np.array(inc["revenue"], dtype=float)
    gp        = np.array(inc["gross_profit"], dtype=float)
    ebitda    = np.array(inc["ebitda"], dtype=float)
    op_inc    = np.array(inc["operating_income"], dtype=float)
    net_inc   = np.array(inc["net_income"], dtype=float)
    da        = np.array(inc["depreciation_amortization"], dtype=float)

    equity    = np.array(bs["total_equity"], dtype=float)
    debt      = np.array(bs["total_debt"], dtype=float)
    cash      = np.array(bs["cash_and_equivalents"], dtype=float)
    assets    = np.array(bs["total_assets"], dtype=float)

    fcf       = np.array(cf["free_cash_flow"], dtype=float)
    ocf       = np.array(cf["operating_cash_flow"], dtype=float)
    capex     = np.array(cf["capital_expenditures"], dtype=float)
    shares    = np.array(data["shares_outstanding"], dtype=float)

    # -- Growth Rates --
    rev_growth = np.full(len(revenue), np.nan)
    for i in range(1, len(revenue)):
        rev_growth[i] = (revenue[i] - revenue[i - 1]) / revenue[i - 1] * 100

    cagr = (revenue[-1] / revenue[0]) ** (1.0 / (len(revenue) - 1)) - 1

    # -- Margins --
    gross_margin = gp / revenue * 100
    ebitda_margin = ebitda / revenue * 100
    op_margin = op_inc / revenue * 100
    net_margin = net_inc / revenue * 100

    # -- Returns --
    roe = net_inc / equity * 100
    tax_rate = data["wacc_inputs"]["tax_rate"]
    nopat = op_inc * (1 - tax_rate)
    invested_cap = equity + debt - cash
    roic = nopat / invested_cap * 100

    print(f"  + Computed 8 ratio categories across {len(years)} fiscal years")

    return {
        "years": years, "revenue": revenue, "revenue_growth": rev_growth,
        "cagr": cagr, "gross_profit": gp, "ebitda": ebitda,
        "operating_income": op_inc, "net_income": net_inc, "da": da,
        "gross_margin": gross_margin, "ebitda_margin": ebitda_margin,
        "operating_margin": op_margin, "net_margin": net_margin,
        "roe": roe, "roic": roic, "nopat": nopat,
        "invested_capital": invested_cap, "fcf": fcf, "ocf": ocf,
        "capex": capex, "equity": equity, "debt": debt,
        "cash": cash, "shares": shares,
    }


# ===========================================================================
# DCF VALUATION MODEL
# ===========================================================================

def run_dcf(data: dict) -> dict:
    """Execute a 5-year Discounted Cash Flow valuation."""
    a    = data["dcf_assumptions"]
    wacc = data["wacc_inputs"]["wacc"]
    tax  = data["wacc_inputs"]["tax_rate"]
    mkt  = data["market_data"]

    base_rev = float(data["income_statement"]["revenue"][-1])
    base_nwc = base_rev * 0.248  # FY2025E NWC / Revenue

    # -- Project 5-year free cash flows --
    proj_rev = []
    rev = base_rev
    for g in a["revenue_growth_rates"]:
        rev *= (1 + g)
        proj_rev.append(rev)
    proj_rev = np.array(proj_rev)

    proj_ebitda = proj_rev * np.array(a["ebitda_margin_targets"])
    proj_da     = proj_rev * np.array(a["da_pct_revenue"])
    proj_ebit   = proj_ebitda - proj_da
    proj_capex  = proj_rev * np.array(a["capex_pct_revenue"])
    proj_nwc    = proj_rev * np.array(a["nwc_pct_revenue"])

    delta_nwc = np.zeros(len(proj_nwc))
    delta_nwc[0] = proj_nwc[0] - base_nwc
    for i in range(1, len(proj_nwc)):
        delta_nwc[i] = proj_nwc[i] - proj_nwc[i - 1]

    # FCF = EBIT(1-t) + D&A − CapEx − ΔNWC
    proj_fcf = proj_ebit * (1 - tax) + proj_da - proj_capex - delta_nwc

    # -- Discount factors & PV --
    disc = np.array([(1 + wacc) ** (-t) for t in range(1, len(proj_fcf) + 1)])
    pv_fcfs     = proj_fcf * disc
    pv_fcf_sum  = float(np.sum(pv_fcfs))

    # -- Terminal Value (Gordon Growth Model) --
    tg = a["terminal_growth_rate"]
    tv = proj_fcf[-1] * (1 + tg) / (wacc - tg)
    pv_tv = float(tv * disc[-1])

    # -- Enterprise → Equity bridge --
    ev = pv_fcf_sum + pv_tv
    net_debt = float(data["balance_sheet"]["total_debt"][-1]) - \
               float(data["balance_sheet"]["cash_and_equivalents"][-1])
    eq_val = ev - net_debt
    implied = eq_val / mkt["shares_outstanding_current"]
    current = mkt["current_stock_price"]
    upside  = (implied - current) / current * 100

    proj_years = [f"FY{2026 + i}E" for i in range(len(proj_fcf))]

    print(f"  + DCF complete: implied ${implied:.2f} vs market ${current:.2f} ({upside:+.1f}%)")

    return {
        "projection_years": proj_years,
        "proj_revenue": proj_rev, "proj_ebitda": proj_ebitda,
        "proj_ebit": proj_ebit, "proj_da": proj_da,
        "proj_capex": proj_capex, "proj_nwc": proj_nwc,
        "delta_nwc": delta_nwc, "proj_fcf": proj_fcf,
        "discount_factors": disc, "pv_fcfs": pv_fcfs,
        "pv_fcf_total": pv_fcf_sum, "terminal_value": float(tv),
        "pv_terminal": pv_tv, "enterprise_value": ev,
        "net_debt": net_debt, "equity_value": eq_val,
        "implied_price": implied, "current_price": current,
        "upside": upside, "wacc": wacc, "terminal_g": tg,
    }


# ===========================================================================
# SENSITIVITY ANALYSIS
# ===========================================================================

def build_sensitivity(dcf: dict, data: dict) -> pd.DataFrame:
    """Sensitivity matrix: Revenue Growth Δ vs WACC."""
    base_wacc = dcf["wacc"]
    a   = data["dcf_assumptions"]
    mkt = data["market_data"]
    tax = data["wacc_inputs"]["tax_rate"]

    base_rev   = float(data["income_statement"]["revenue"][-1])
    base_nwc_r = 0.248
    base_growth = a["revenue_growth_rates"]
    tg = a["terminal_growth_rate"]

    rev_deltas  = [-0.02, -0.01, 0.0, 0.01, 0.02]
    wacc_deltas = [-0.015, -0.010, -0.005, 0.0, 0.005, 0.010, 0.015]

    net_debt = dcf["net_debt"]
    shares   = mkt["shares_outstanding_current"]

    grid = np.zeros((len(rev_deltas), len(wacc_deltas)))

    for i, rd in enumerate(rev_deltas):
        for j, wd in enumerate(wacc_deltas):
            adj_wacc = base_wacc + wd
            if adj_wacc <= tg:
                grid[i, j] = np.nan
                continue

            # Re-project revenues with adjusted growth
            rev = base_rev
            proj_rev = []
            for g in base_growth:
                rev *= (1 + g + rd)
                proj_rev.append(rev)
            proj_rev = np.array(proj_rev)

            ebitda = proj_rev * np.array(a["ebitda_margin_targets"])
            da     = proj_rev * np.array(a["da_pct_revenue"])
            ebit   = ebitda - da
            capex  = proj_rev * np.array(a["capex_pct_revenue"])
            nwc    = proj_rev * np.array(a["nwc_pct_revenue"])

            dnwc = np.zeros(len(nwc))
            dnwc[0] = nwc[0] - base_rev * base_nwc_r
            for k in range(1, len(nwc)):
                dnwc[k] = nwc[k] - nwc[k - 1]

            fcf = ebit * (1 - tax) + da - capex - dnwc
            disc = np.array([(1 + adj_wacc) ** (-t) for t in range(1, len(fcf) + 1)])
            pv_f = float(np.sum(fcf * disc))
            tv   = fcf[-1] * (1 + tg) / (adj_wacc - tg)
            pv_t = float(tv * disc[-1])
            eq   = pv_f + pv_t - net_debt
            grid[i, j] = eq / shares

    row_labels = [f"{d * 100:+.0f}%" for d in rev_deltas]
    col_labels = [f"{(base_wacc + d) * 100:.1f}%" for d in wacc_deltas]

    df = pd.DataFrame(grid, index=row_labels, columns=col_labels)
    df.index.name   = "Revenue Growth Δ"
    df.columns.name = "WACC"
    return df


# ===========================================================================
# CHART HELPERS
# ===========================================================================

def _source(ax, text="Source: Tesla 10-K filings, analyst estimates"):
    ax.annotate(text, xy=(1, -0.13), xycoords="axes fraction",
                ha="right", va="top", fontsize=7.5, color=C["grey"], style="italic")


def _subtitle(ax, text, y=1.02):
    ax.text(0.0, y, text, transform=ax.transAxes,
            fontsize=9.5, color=C["grey"], style="italic", va="bottom")


# ===========================================================================
# CHART 1 — REVENUE & YOY GROWTH (dual-axis)
# ===========================================================================

def chart_revenue_growth(r):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    years = r["years"]; rev_b = r["revenue"] / 1000; g = r["revenue_growth"]
    x = np.arange(len(years))

    bars = ax1.bar(x, rev_b, width=0.55, color=C["navy"], alpha=0.85,
                   zorder=3, edgecolor="white", linewidth=0.5)
    ax1.set_ylabel("Revenue ($B)", color=C["navy"], fontweight="bold")
    ax1.set_xticks(x); ax1.set_xticklabels(years, fontsize=10)
    ax1.tick_params(axis="y", colors=C["navy"])
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))

    for b, v in zip(bars, rev_b):
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2,
                 f"${v:.1f}B", ha="center", va="bottom", fontsize=9,
                 fontweight="bold", color=C["navy"])

    ax2 = ax1.twinx()
    vi = ~np.isnan(g)
    ax2.plot(x[vi], g[vi], color=C["red"], linewidth=2.5, marker="o",
             markersize=8, markerfacecolor=C["red"], markeredgecolor="white",
             markeredgewidth=2, zorder=5)
    ax2.set_ylabel("YoY Growth (%)", color=C["red"], fontweight="bold")
    ax2.tick_params(axis="y", colors=C["red"])
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

    for i in range(len(g)):
        if not np.isnan(g[i]):
            ax2.annotate(f"{g[i]:.1f}%", xy=(x[i], g[i]),
                         xytext=(0, 14), textcoords="offset points",
                         ha="center", fontsize=9, fontweight="bold", color=C["red"])

    cagr = r["cagr"] * 100
    ax1.annotate(f"4-Year CAGR: {cagr:.1f}%", xy=(0.98, 0.95),
                 xycoords="axes fraction", ha="right", va="top", fontsize=10,
                 bbox=dict(boxstyle="round,pad=0.4", fc=C["light_grey"],
                           ec=C["navy"], alpha=0.9),
                 fontweight="bold", color=C["navy"])

    ax1.set_title("Tesla Revenue & Year-over-Year Growth")
    _subtitle(ax1, "FY2021 – FY2025E  |  Accelerating top-line via energy storage & services")
    _source(ax1); ax1.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(OUTPUT_DIR / "revenue_growth.png"); plt.close(fig)
    print("  + Chart 1: Revenue & Growth")


# ===========================================================================
# CHART 2 — MARGIN ANALYSIS (multi-line)
# ===========================================================================

def chart_margin_analysis(r):
    fig, ax = plt.subplots(figsize=(10, 6))
    years = r["years"]; x = np.arange(len(years))

    series = [
        ("Gross Margin",  r["gross_margin"],  C["navy"], "s"),
        ("EBITDA Margin", r["ebitda_margin"], C["red"],  "D"),
        ("Net Margin",    r["net_margin"],    C["blue"], "o"),
    ]
    for label, vals, color, mk in series:
        ax.plot(x, vals, color=color, linewidth=2.5, marker=mk, markersize=8,
                markerfacecolor="white", markeredgecolor=color,
                markeredgewidth=2, label=label, zorder=5)
        ax.annotate(f"{vals[-1]:.1f}%", xy=(x[-1], vals[-1]),
                    xytext=(10, 0), textcoords="offset points",
                    fontsize=9, fontweight="bold", color=color, va="center")

    # Highlight 2023 margin compression
    ax.axvspan(1.5, 2.5, alpha=0.08, color=C["red"], zorder=0)
    ax.annotate("Price war\nmargin\ncompression", xy=(2, r["gross_margin"][2] - 2),
                fontsize=8, color=C["red"], ha="center", va="top", style="italic", alpha=0.7)

    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylabel("Margin (%)")
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor=C["light_grey"])
    ax.set_title("Tesla Profitability Margin Analysis")
    _subtitle(ax, "Gross margin recovery post-2023 price war signals improving unit economics")
    _source(ax)
    fig.tight_layout(); fig.savefig(OUTPUT_DIR / "margin_analysis.png"); plt.close(fig)
    print("  + Chart 2: Margin Analysis")


# ===========================================================================
# CHART 3 — FREE CASH FLOW TREND
# ===========================================================================

def chart_fcf_trend(r):
    fig, ax = plt.subplots(figsize=(10, 6))
    years = r["years"]; fcf_b = r["fcf"] / 1000; x = np.arange(len(years))

    colors = [C["green"] if v > 2 else C["amber"] if v > 0 else C["red"] for v in fcf_b]
    bars = ax.bar(x, fcf_b, width=0.55, color=colors, alpha=0.85,
                  zorder=3, edgecolor="white", linewidth=0.5)

    for b, v in zip(bars, fcf_b):
        y_off = 0.15 if v >= 0 else -0.35
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + y_off,
                f"${v:.1f}B", ha="center", va="bottom" if v >= 0 else "top",
                fontsize=10, fontweight="bold", color=C["dark"])

    ax.annotate("Heavy CapEx cycle\n(Cybertruck + Megapack)",
                xy=(3, fcf_b[3]), xytext=(3.6, 5),
                arrowprops=dict(arrowstyle="->", color=C["grey"], lw=1.5),
                fontsize=8.5, color=C["grey"], ha="center",
                bbox=dict(boxstyle="round,pad=0.3", fc="#FFF9C4", ec=C["amber"]))

    ax.axhline(y=0, color=C["grey"], linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.1fB"))
    ax.set_ylabel("Free Cash Flow ($B)")
    ax.set_title("Tesla Free Cash Flow Trajectory")
    _subtitle(ax, "FCF recovery expected as CapEx intensity normalizes in FY2025E+")
    _source(ax)
    fig.tight_layout(); fig.savefig(OUTPUT_DIR / "fcf_trend.png"); plt.close(fig)
    print("  + Chart 3: FCF Trend")


# ===========================================================================
# CHART 4 — ROE vs ROIC
# ===========================================================================

def chart_roe_roic(r):
    fig, ax = plt.subplots(figsize=(10, 6))
    years = r["years"]; x = np.arange(len(years)); w = 0.30

    b1 = ax.bar(x - w / 2, r["roe"],  w, color=C["navy"], alpha=0.85, label="ROE", zorder=3)
    b2 = ax.bar(x + w / 2, r["roic"], w, color=C["red"],  alpha=0.85, label="ROIC", zorder=3)

    for bars, vals in [(b1, r["roe"]), (b2, r["roic"])]:
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                    f"{v:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.axhline(y=18, color=C["grey"], linewidth=1, linestyle="--", alpha=0.7)
    ax.annotate("S&P 500 Avg ROE (~18%)", xy=(len(years) - 1, 18.5),
                fontsize=8, color=C["grey"], ha="right")

    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylabel("Return (%)")
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor=C["light_grey"])
    ax.set_title("Tesla Return on Equity vs Return on Invested Capital")
    _subtitle(ax, "Consistently above S&P 500 benchmarks — efficient capital deployment")
    _source(ax)
    fig.tight_layout(); fig.savefig(OUTPUT_DIR / "roe_roic.png"); plt.close(fig)
    print("  + Chart 4: ROE vs ROIC")


# ===========================================================================
# CHART 5 — COMPARABLE COMPANY MULTIPLES
# ===========================================================================

def chart_comps(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6),
                                    gridspec_kw={"width_ratios": [1, 1]})
    comp = data["comparable_companies"]
    names = comp["names"]

    # Filter for positive multiples
    valid_ev = [(n, v) for n, v in zip(names, comp["ev_ebitda"]) if v is not None and v > 0]
    valid_pe = [(n, v) for n, v in zip(names, comp["pe_ratio"])  if v is not None and v > 0]
    valid_ev.sort(key=lambda x: x[1])
    valid_pe.sort(key=lambda x: x[1])

    # -- EV/EBITDA --
    ev_n, ev_v = zip(*valid_ev)
    c_ev = [C["red"] if n == "Tesla" else C["navy"] for n in ev_n]
    bars1 = ax1.barh(range(len(ev_n)), ev_v, color=c_ev, alpha=0.85, height=0.50)
    ax1.set_yticks(range(len(ev_n))); ax1.set_yticklabels(ev_n, fontsize=10)
    ax1.set_xlabel("EV / EBITDA (x)"); ax1.set_title("EV / EBITDA", fontsize=13, fontweight="bold")
    for b, v in zip(bars1, ev_v):
        ax1.text(v + 0.5, b.get_y() + b.get_height() / 2,
                 f"{v:.1f}x", va="center", fontsize=10, fontweight="bold")

    # -- P/E --
    pe_n, pe_v = zip(*valid_pe)
    c_pe = [C["red"] if n == "Tesla" else C["navy"] for n in pe_n]
    bars2 = ax2.barh(range(len(pe_n)), pe_v, color=c_pe, alpha=0.85, height=0.50)
    ax2.set_yticks(range(len(pe_n))); ax2.set_yticklabels(pe_n, fontsize=10)
    ax2.set_xlabel("P / E Ratio (x)"); ax2.set_title("Price / Earnings", fontsize=13, fontweight="bold")
    for b, v in zip(bars2, pe_v):
        ax2.text(v + 0.5, b.get_y() + b.get_height() / 2,
                 f"{v:.1f}x", va="center", fontsize=10, fontweight="bold")

    fig.suptitle("Tesla vs Peers — Valuation Multiples Comparison",
                 fontsize=15, fontweight="bold", y=1.02)
    _source(ax2, "Source: Market data Sept 2026  |  Rivian & Lucid excluded (negative EBITDA)")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "comps_ev_ebitda.png"); plt.close(fig)
    print("  + Chart 5: Comparable Multiples")


# ===========================================================================
# CHART 6 — SENSITIVITY HEATMAP
# ===========================================================================

def chart_sensitivity(sens_df, dcf):
    fig, ax = plt.subplots(figsize=(12, 6.5))
    current = dcf["current_price"]

    cmap = sns.diverging_palette(10, 130, s=80, l=55, as_cmap=True)
    annot = sens_df.map(lambda v: f"${v:.0f}" if not np.isnan(v) else "N/A")

    sns.heatmap(sens_df, annot=annot, fmt="", cmap=cmap, center=current,
                linewidths=1.5, linecolor="white", ax=ax,
                cbar_kws={"label": "Implied Share Price ($)", "shrink": 0.8},
                annot_kws={"size": 11, "fontweight": "bold"})

    ax.set_xlabel("WACC", fontsize=12, fontweight="bold")
    ax.set_ylabel("Revenue Growth Δ", fontsize=12, fontweight="bold")
    ax.set_title("DCF Sensitivity Analysis — Implied Share Price")
    _subtitle(ax, f"Current price: ${current:.0f}  |  Green = undervalued, Red = overvalued", y=1.01)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "sensitivity_heatmap.png"); plt.close(fig)
    print("  + Chart 6: Sensitivity Heatmap")


# ===========================================================================
# CHART 7 — DCF WATERFALL / VALUATION BRIDGE
# ===========================================================================

def chart_dcf_waterfall(dcf):
    fig, ax = plt.subplots(figsize=(11, 6.5))

    pv_f = dcf["pv_fcf_total"] / 1000
    pv_t = dcf["pv_terminal"] / 1000
    ev   = dcf["enterprise_value"] / 1000
    nd   = dcf["net_debt"] / 1000       # negative means net cash
    eq   = dcf["equity_value"] / 1000

    is_net_cash = nd < 0
    bridge_label = "Plus:\nNet Cash" if is_net_cash else "Less:\nNet Debt"
    bridge_amt   = abs(nd)

    labels = ["PV of\nProjected FCFs", "PV of\nTerminal Value",
              "Enterprise\nValue", bridge_label, "Equity\nValue"]

    # Waterfall geometry
    bottoms = [0,  pv_f,  0,  0,  0]
    heights = [pv_f, pv_t, ev, 0,  eq]

    if is_net_cash:
        bottoms[3] = ev
        heights[3] = bridge_amt          # bar rises above EV
    else:
        bottoms[3] = ev - bridge_amt     # bar descends from EV
        heights[3] = bridge_amt

    bar_colors = [C["blue"], C["blue"], C["navy"],
                  C["green"] if is_net_cash else C["red"],
                  C["green"]]

    x = np.arange(len(labels))
    bars = ax.bar(x, heights, bottom=bottoms, width=0.55, color=bar_colors,
                  alpha=0.85, zorder=3, edgecolor="white", linewidth=0.5)

    # Connector lines
    for i in [0, 1]:
        top = bottoms[i] + heights[i]
        ax.plot([x[i] + 0.275, x[i + 1] - 0.275], [top, top],
                color=C["grey"], linewidth=1, linestyle="--", alpha=0.5)
    # EV → Bridge connector
    ax.plot([x[2] + 0.275, x[3] - 0.275], [ev, ev],
            color=C["grey"], linewidth=1, linestyle="--", alpha=0.5)
    # Bridge → Equity connector
    eq_top = bottoms[3] + heights[3] if is_net_cash else bottoms[3]
    ax.plot([x[3] + 0.275, x[4] - 0.275], [eq, eq],
            color=C["grey"], linewidth=1, linestyle="--", alpha=0.5)

    # Data labels
    display_vals = [pv_f, pv_t, ev, bridge_amt, eq]
    signs        = ["",   "",   "",  "+" if is_net_cash else "−", ""]
    for b, dv, s, bot, h in zip(bars, display_vals, signs, bottoms, heights):
        y_pos = bot + h + max(ev * 0.02, 3)
        ax.text(b.get_x() + b.get_width() / 2, y_pos,
                f"{s}${dv:,.0f}B", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color=C["dark"])

    # Verdict box
    implied = dcf["implied_price"]; current = dcf["current_price"]
    upside  = dcf["upside"]
    vc = C["green"] if upside > 0 else C["red"]
    vt = "UNDERVALUED" if upside > 0 else "OVERVALUED"
    ax.annotate(
        f"Implied Price: ${implied:,.0f}/share\n"
        f"Current Price: ${current:,.0f}/share\n"
        f"{vt} by {abs(upside):.1f}%",
        xy=(0.98, 0.95), xycoords="axes fraction", ha="right", va="top",
        fontsize=10, fontweight="bold", color=vc,
        bbox=dict(boxstyle="round,pad=0.5",
                  fc="#E8F5E9" if upside > 0 else "#FFEBEE",
                  ec=vc, alpha=0.95))

    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}B"))
    ax.set_ylabel("Value ($B)"); ax.set_axisbelow(True)
    ax.set_title("DCF Valuation Bridge — Tesla Inc.")
    _subtitle(ax, f"WACC: {dcf['wacc']*100:.1f}%  |  Terminal Growth: {dcf['terminal_g']*100:.1f}%  |  Gordon Growth Model")
    _source(ax)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "dcf_waterfall.png"); plt.close(fig)
    print("  + Chart 7: DCF Waterfall")


# ===========================================================================
# EXECUTIVE CONSOLE SUMMARY
# ===========================================================================

def print_summary(r, dcf, data):
    """Print a formatted executive summary to the console."""
    sep = "=" * 72

    print(f"\n{sep}")
    print(f"  TESLA (TSLA) — FINANCIAL ANALYSIS EXECUTIVE SUMMARY")
    print(f"  Analysis Date: {data['analysis_date']}")
    print(f"{sep}\n")

    # Build summary DataFrame
    metrics = {
        "Revenue ($M)":       [f"{v:>12,.0f}" for v in r["revenue"]],
        "Rev Growth (%)":     [f"{'N/A':>12}" if np.isnan(v) else f"{v:>12.1f}" for v in r["revenue_growth"]],
        "Gross Margin (%)":   [f"{v:>12.1f}" for v in r["gross_margin"]],
        "EBITDA Margin (%)":  [f"{v:>12.1f}" for v in r["ebitda_margin"]],
        "Net Margin (%)":     [f"{v:>12.1f}" for v in r["net_margin"]],
        "ROE (%)":            [f"{v:>12.1f}" for v in r["roe"]],
        "ROIC (%)":           [f"{v:>12.1f}" for v in r["roic"]],
        "FCF ($M)":           [f"{v:>12,.0f}" for v in r["fcf"]],
    }
    df = pd.DataFrame(metrics, index=r["years"]).T
    print(df.to_string())

    # Key Insights
    gm_d = r["gross_margin"][-1] - r["gross_margin"][2]
    cagr = r["cagr"] * 100
    print(f"\n  {'-' * 60}")
    print(f"  KEY OPERATIONAL INSIGHTS")
    print(f"  {'-' * 60}")
    print(f"\n  1. MARGIN RECOVERY: Gross margin expanded {gm_d:+.1f}pp from the")
    print(f"     FY2023 trough ({r['gross_margin'][2]:.1f}%) to FY2025E ({r['gross_margin'][-1]:.1f}%),")
    print(f"     driven by manufacturing efficiencies and price stabilization.")
    print(f"\n  2. GROWTH TRAJECTORY: {cagr:.1f}% revenue CAGR (FY2021–FY2025E)")
    print(f"     powered by energy storage (Megapack), services revenue,")
    print(f"     and global EV market share expansion.")

    # DCF Summary
    print(f"\n  {'-' * 60}")
    print(f"  DCF VALUATION SUMMARY")
    print(f"  {'-' * 60}")
    print(f"\n  WACC:                  {dcf['wacc']*100:.2f}%")
    print(f"  Terminal Growth:       {dcf['terminal_g']*100:.1f}%")
    print(f"  PV of FCFs:            ${dcf['pv_fcf_total']/1000:,.1f}B")
    print(f"  PV of Terminal Value:  ${dcf['pv_terminal']/1000:,.1f}B")
    print(f"  Enterprise Value:      ${dcf['enterprise_value']/1000:,.1f}B")
    print(f"  Net Debt (Cash):       ${dcf['net_debt']/1000:,.1f}B")
    print(f"  Equity Value:          ${dcf['equity_value']/1000:,.1f}B")
    print(f"  Implied Price/Share:   ${dcf['implied_price']:,.2f}")
    print(f"  Current Market Price:  ${dcf['current_price']:,.2f}")

    up = dcf["upside"]
    vt = "UNDERVALUED" if up > 0 else "OVERVALUED"
    print(f"\n  >> VERDICT: Tesla appears {vt} by {abs(up):.1f}%")

    # Strategic Recommendation
    print(f"\n  {'-' * 60}")
    print(f"  STRATEGIC RECOMMENDATION (THE BAIN TOUCH)")
    print(f"  {'-' * 60}")
    print(f"\n  1. VALUATION: DCF implies Tesla is {vt.lower()} by {abs(up):.1f}%")
    print(f"     (${dcf['implied_price']:,.0f} implied vs ${dcf['current_price']:,.0f} market).")
    print(f"\n  2. GROWTH CATALYSTS:")
    print(f"     • Energy Storage: Megapack & Powerwall revenue growing >60% YoY,")
    print(f"       transforming Tesla into an integrated energy company.")
    print(f"     • Full Self-Driving (FSD): High-margin software revenue with")
    print(f"       potential to unlock recurring subscription income stream.")
    print(f"\n  3. KEY RISK: EV price competition from Chinese OEMs (BYD, NIO)")
    print(f"     could compress automotive gross margins below 18%.")
    print(f"     MITIGATION: Revenue diversification into energy + services")
    print(f"     reduces auto dependency from ~85% to projected ~65% by FY2030.")

    print(f"\n{sep}")
    print(f"  Charts saved to: {OUTPUT_DIR.relative_to(ROOT_DIR)}")
    print(f"{sep}\n")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    """Run the complete Tesla financial analysis pipeline."""
    banner = "=" * 72
    print(f"\n{banner}")
    print("  TESLA FINANCIAL ANALYSIS ENGINE")
    print("  Bain & Company M&A Readiness Portfolio Project")
    print(f"{banner}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_style()

    print(">> Phase 1: Data Loading")
    data = load_data()

    print("\n>> Phase 2: Ratio Computation")
    ratios = compute_ratios(data)

    print("\n>> Phase 3: DCF Valuation Model")
    dcf = run_dcf(data)

    print("\n>> Phase 4: Sensitivity Analysis")
    sens = build_sensitivity(dcf, data)

    print("\n>> Phase 5: Chart Generation (7 charts)")
    chart_revenue_growth(ratios)
    chart_margin_analysis(ratios)
    chart_fcf_trend(ratios)
    chart_roe_roic(ratios)
    chart_comps(data)
    chart_sensitivity(sens, dcf)
    chart_dcf_waterfall(dcf)

    print("\n>> Phase 6: Executive Summary")
    print_summary(ratios, dcf, data)

    # -- Persist summary for downstream scripts --
    summary = {
        "implied_price": dcf["implied_price"],
        "current_price": dcf["current_price"],
        "upside": dcf["upside"],
        "enterprise_value": dcf["enterprise_value"],
        "equity_value": dcf["equity_value"],
        "pv_fcf_total": dcf["pv_fcf_total"],
        "pv_terminal": dcf["pv_terminal"],
        "net_debt": dcf["net_debt"],
        "wacc": dcf["wacc"],
        "terminal_g": dcf["terminal_g"],
        "cagr": ratios["cagr"],
        "gross_margin_latest": float(ratios["gross_margin"][-1]),
        "ebitda_margin_latest": float(ratios["ebitda_margin"][-1]),
        "sensitivity": sens.to_dict(),
        "projected_fcf": dcf["proj_fcf"].tolist(),
        "projected_revenue": dcf["proj_revenue"].tolist(),
        "projection_years": dcf["projection_years"],
    }
    out_path = ROOT_DIR / "output" / "analysis_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  + Summary saved to {out_path.relative_to(ROOT_DIR)}")

    return data, ratios, dcf, sens


if __name__ == "__main__":
    main()
