#!/usr/bin/env python3
"""
╔==========================================================================╗
║  Tesla (TSLA) — 3-Slide Executive Teaser Deck Generator                ║
║  Bain & Company M&A Readiness Portfolio Project                        ║
╚==========================================================================╝

Generates a self-contained HTML executive presentation with:
  Slide 1 — Situation Overview  (market position + financial trajectory)
  Slide 2 — Valuation Summary   (DCF + Comps + Sensitivity)
  Slide 3 — Strategic Recommendation  (3-bullet Bain-style)

Usage:
    python generate_executive_deck.py

Prerequisite:
    Run ratio_analysis.py first to generate charts in output/charts/

Output:
    output/executive_teaser.html
"""

import json
import base64
from pathlib import Path

ROOT_DIR   = Path(__file__).resolve().parent.parent
DATA_FILE  = ROOT_DIR / "data" / "tesla_financials.json"
SUMMARY_FILE = ROOT_DIR / "output" / "analysis_summary.json"
CHARTS_DIR = ROOT_DIR / "output" / "charts"
OUTPUT_DIR = ROOT_DIR / "output"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def img_to_base64(path: Path) -> str:
    """Embed a chart image as base64 for self-contained HTML."""
    if path.exists():
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    return ""


def generate_html(data: dict, summary: dict) -> str:
    """Build the full HTML executive deck."""
    inc   = data["income_statement"]
    mkt   = data["market_data"]
    comp  = data["comparable_companies"]
    wacc  = data["wacc_inputs"]
    years = data["fiscal_years"]

    implied  = summary["implied_price"]
    current  = summary["current_price"]
    upside   = summary["upside"]
    ev_val   = summary["enterprise_value"]
    eq_val   = summary["equity_value"]
    pv_fcf   = summary["pv_fcf_total"]
    pv_tv    = summary["pv_terminal"]
    cagr     = summary["cagr"] * 100

    verdict  = "Undervalued" if upside > 0 else "Overvalued"
    v_color  = "#2E7D32" if upside > 0 else "#CC0000"
    v_bg     = "#E8F5E9" if upside > 0 else "#FFEBEE"

    # Embed charts
    chart_rev   = img_to_base64(CHARTS_DIR / "revenue_growth.png")
    chart_margin = img_to_base64(CHARTS_DIR / "margin_analysis.png")
    chart_fcf   = img_to_base64(CHARTS_DIR / "fcf_trend.png")
    chart_comps = img_to_base64(CHARTS_DIR / "comps_ev_ebitda.png")
    chart_sens  = img_to_base64(CHARTS_DIR / "sensitivity_heatmap.png")
    chart_dcf   = img_to_base64(CHARTS_DIR / "dcf_waterfall.png")

    # Revenue data for sparkline table
    rev_rows = ""
    for i, yr in enumerate(years):
        rev = inc["revenue"][i]
        gp  = inc["gross_profit"][i]
        eb  = inc["ebitda"][i]
        ni  = inc["net_income"][i]
        gm  = gp / rev * 100
        em  = eb / rev * 100
        rev_rows += f"""
        <tr>
            <td style="font-weight:600">{yr}</td>
            <td>${rev:,.0f}</td>
            <td>{gm:.1f}%</td>
            <td>{em:.1f}%</td>
            <td>${ni:,.0f}</td>
        </tr>"""

    # Comps table
    comps_rows = ""
    for i, name in enumerate(comp["names"]):
        ev_eb = comp["ev_ebitda"][i]
        pe    = comp["pe_ratio"][i]
        ev_r  = comp["ev_revenue"][i]
        is_t  = name == "Tesla"
        style = 'style="background:#DCE6F1; font-weight:700"' if is_t else ""
        ev_eb_str = f"{ev_eb:.1f}x" if ev_eb is not None and ev_eb > 0 else "N/M"
        pe_str    = f"{pe:.1f}x" if pe is not None and pe > 0 else "N/M"
        ev_r_str  = f"{ev_r:.1f}x" if ev_r is not None and ev_r > 0 else "N/M"
        comps_rows += f"""
        <tr {style}>
            <td>{name}</td>
            <td>{ev_r_str}</td>
            <td>{ev_eb_str}</td>
            <td>{pe_str}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tesla (TSLA) — Executive Valuation Teaser | Bain M&A Portfolio</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --bain-red: #CC0000;
        --bain-navy: #003366;
        --bain-blue: #0066CC;
        --bain-grey: #666666;
        --bain-light: #F5F5F5;
        --bain-green: #2E7D32;
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', 'Calibri', Arial, sans-serif; background: #f0f0f0; color: #1a1a2e; }}

    .slide {{
        width: 1100px; min-height: 780px; margin: 40px auto;
        background: white; border-radius: 4px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        padding: 48px 56px;
        page-break-after: always;
        position: relative;
    }}

    .slide-header {{
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 3px solid var(--bain-red); padding-bottom: 16px;
        margin-bottom: 32px;
    }}
    .slide-header h1 {{ font-size: 26px; color: var(--bain-navy); font-weight: 800; letter-spacing: -0.5px; }}
    .slide-header .tag {{
        font-size: 11px; font-weight: 700; color: white; background: var(--bain-red);
        padding: 5px 14px; border-radius: 3px; text-transform: uppercase; letter-spacing: 1px;
    }}

    .slide-number {{
        position: absolute; bottom: 24px; right: 40px;
        font-size: 11px; color: var(--bain-grey); font-weight: 600;
    }}
    .slide-footer {{
        position: absolute; bottom: 24px; left: 56px;
        font-size: 10px; color: #999; font-style: italic;
    }}

    h2 {{ font-size: 18px; color: var(--bain-navy); margin: 24px 0 12px; font-weight: 700; }}
    h3 {{ font-size: 14px; color: var(--bain-red); margin: 18px 0 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}

    p {{ font-size: 13px; line-height: 1.65; color: #333; margin-bottom: 10px; }}

    .kpi-grid {{
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
        margin: 20px 0;
    }}
    .kpi-card {{
        background: var(--bain-light); border-radius: 6px; padding: 16px 18px;
        border-left: 4px solid var(--bain-navy); text-align: center;
    }}
    .kpi-card.red {{ border-left-color: var(--bain-red); }}
    .kpi-card.green {{ border-left-color: var(--bain-green); }}
    .kpi-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--bain-grey); font-weight: 600; }}
    .kpi-value {{ font-size: 24px; font-weight: 800; color: var(--bain-navy); margin-top: 4px; }}
    .kpi-card.red .kpi-value {{ color: var(--bain-red); }}
    .kpi-card.green .kpi-value {{ color: var(--bain-green); }}

    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 12px 0; }}
    th {{ background: var(--bain-navy); color: white; padding: 8px 12px; text-align: right; font-weight: 600; font-size: 11px; }}
    th:first-child {{ text-align: left; }}
    td {{ padding: 7px 12px; text-align: right; border-bottom: 1px solid #eee; }}
    td:first-child {{ text-align: left; font-weight: 500; }}
    tr:hover {{ background: #f8f9fa; }}

    .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 16px 0; }}
    .chart-full {{ margin: 16px 0; text-align: center; }}
    .chart-row img, .chart-full img {{ width: 100%; border-radius: 4px; border: 1px solid #e0e0e0; }}

    .verdict-box {{
        background: {v_bg}; border: 2px solid {v_color}; border-radius: 8px;
        padding: 20px 24px; margin: 20px 0; text-align: center;
    }}
    .verdict-box h2 {{ color: {v_color}; margin: 0 0 6px; font-size: 22px; }}
    .verdict-box p {{ color: {v_color}; font-size: 16px; font-weight: 600; margin: 0; }}

    .rec-box {{
        background: var(--bain-light); border-radius: 8px; padding: 20px 24px;
        margin: 16px 0; border-left: 5px solid var(--bain-red);
    }}
    .rec-box h3 {{ color: var(--bain-navy); margin: 0 0 8px; }}
    .rec-box p {{ margin: 0; font-size: 13px; }}

    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}

    @media print {{
        body {{ background: white; }}
        .slide {{ box-shadow: none; margin: 0; page-break-after: always; }}
    }}
</style>
</head>
<body>

<!-- ======================================================= -->
<!-- SLIDE 1 — SITUATION OVERVIEW                          -->
<!-- ======================================================= -->
<div class="slide">
    <div class="slide-header">
        <h1>Tesla, Inc. (TSLA) — Situation Overview</h1>
        <span class="tag">Confidential</span>
    </div>

    <p>Tesla is the world's leading electric vehicle manufacturer and integrated clean energy company,
    operating across automotive, energy generation/storage, and AI/autonomy verticals. This analysis
    evaluates Tesla's financial trajectory and intrinsic valuation as of {data['analysis_date']}.</p>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Market Cap</div>
            <div class="kpi-value">${mkt['market_capitalization']/1000:,.0f}B</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-label">Revenue CAGR (4Y)</div>
            <div class="kpi-value">{cagr:.1f}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">FY2025E Revenue</div>
            <div class="kpi-value">${inc['revenue'][-1]/1000:,.1f}B</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-label">Gross Margin (Latest)</div>
            <div class="kpi-value">{summary['gross_margin_latest']:.1f}%</div>
        </div>
    </div>

    <h2>5-Year Financial Trajectory</h2>
    <table>
        <thead>
            <tr><th>Metric</th><th>Revenue ($M)</th><th>Gross Margin</th>
            <th>EBITDA Margin</th><th>Net Income ($M)</th></tr>
        </thead>
        <tbody>{rev_rows}</tbody>
    </table>

    <div class="chart-row">
        <div><img src="{chart_rev}" alt="Revenue Growth"></div>
        <div><img src="{chart_margin}" alt="Margin Analysis"></div>
    </div>

    <h3>Key Operational Insight</h3>
    <p><strong>Margin Recovery:</strong> After the FY2023 EV price war compressed gross margins to 18.2%,
    Tesla has demonstrated recovery to {summary['gross_margin_latest']:.1f}% through manufacturing
    efficiencies (4680 cell ramp, Austin/Berlin scale), reduced raw material costs, and
    growing high-margin energy storage and services revenue.</p>

    <div class="slide-footer">Tesla (TSLA) — M&A Valuation Analysis  |  {data['analysis_date']}</div>
    <div class="slide-number">1 / 3</div>
</div>

<!-- ======================================================= -->
<!-- SLIDE 2 — VALUATION SUMMARY                           -->
<!-- ======================================================= -->
<div class="slide">
    <div class="slide-header">
        <h1>Valuation Summary — DCF & Comparable Analysis</h1>
        <span class="tag">Confidential</span>
    </div>

    <div class="verdict-box">
        <h2>DCF Implied Price: ${implied:,.0f} per share</h2>
        <p>Tesla appears <strong>{verdict.upper()}</strong> by {abs(upside):.1f}% vs market price of ${current:,.0f}</p>
    </div>

    <div class="two-col">
        <div>
            <h3>DCF Model Summary</h3>
            <table>
                <tr><td>WACC</td><td>{wacc['wacc']*100:.2f}%</td></tr>
                <tr><td>Terminal Growth Rate</td><td>2.5%</td></tr>
                <tr><td>PV of Projected FCFs</td><td>${pv_fcf/1000:,.1f}B</td></tr>
                <tr><td>PV of Terminal Value</td><td>${pv_tv/1000:,.1f}B</td></tr>
                <tr><td><strong>Enterprise Value</strong></td><td><strong>${ev_val/1000:,.1f}B</strong></td></tr>
                <tr><td>Net Cash Position</td><td>${abs(summary['net_debt'])/1000:,.1f}B</td></tr>
                <tr><td><strong>Equity Value</strong></td><td><strong>${eq_val/1000:,.1f}B</strong></td></tr>
            </table>
        </div>
        <div>
            <h3>Peer Multiples Comparison</h3>
            <table>
                <thead><tr><th style="text-align:left">Company</th><th>EV/Rev</th><th>EV/EBITDA</th><th>P/E</th></tr></thead>
                <tbody>{comps_rows}</tbody>
            </table>
        </div>
    </div>

    <div class="chart-row">
        <div><img src="{chart_dcf}" alt="DCF Waterfall"></div>
        <div><img src="{chart_sens}" alt="Sensitivity Analysis"></div>
    </div>

    <div class="slide-footer">Tesla (TSLA) — M&A Valuation Analysis  |  {data['analysis_date']}</div>
    <div class="slide-number">2 / 3</div>
</div>

<!-- ======================================================= -->
<!-- SLIDE 3 — STRATEGIC RECOMMENDATION                    -->
<!-- ======================================================= -->
<div class="slide">
    <div class="slide-header">
        <h1>Strategic Recommendation</h1>
        <span class="tag">Confidential</span>
    </div>

    <div class="rec-box">
        <h3>1. Valuation Outcome</h3>
        <p>Our DCF analysis indicates Tesla is <strong>{verdict.lower()} by {abs(upside):.1f}%</strong>,
        with an implied intrinsic value of <strong>${implied:,.0f}/share</strong> versus the current
        market price of ${current:,.0f}. The base case enterprise value of ${ev_val/1000:,.0f}B
        reflects a {summary['cagr']*100:.1f}% historical revenue CAGR and projected margin expansion
        from {summary['ebitda_margin_latest']:.1f}% to 20.5% by FY2030E.</p>
    </div>

    <div class="rec-box">
        <h3>2. Growth Catalysts</h3>
        <p><strong>Energy Storage & Generation:</strong> Tesla Energy (Megapack + Powerwall + Solar)
        is the fastest-growing segment at >60% YoY, with gross margins exceeding automotive.
        The energy business is transforming Tesla from a pure automaker into an integrated
        energy company with a $200B+ TAM — a thesis that current multiples only partially reflect.</p>
        <p style="margin-top:10px"><strong>Full Self-Driving (FSD) & Robotaxi:</strong> FSD v13+
        supervised autonomy generates high-margin recurring software revenue ($99/month subscriptions).
        The forthcoming robotaxi network represents an asset-light platform opportunity with
        80%+ gross margins — a paradigm shift from hardware to software-defined revenue.</p>
    </div>

    <div class="rec-box">
        <h3>3. Key Risk & Mitigation</h3>
        <p><strong>Risk:</strong> Intensifying price competition from Chinese EV OEMs (BYD, NIO,
        XPeng) in both domestic China and emerging export markets could sustain pressure on
        automotive gross margins, which declined from 25.6% (FY2022) to 18.2% (FY2023).
        A protracted price war scenario compresses our base case valuation by 15-20%.</p>
        <p style="margin-top:10px"><strong>Mitigation:</strong> Tesla's strategic hedge is
        revenue diversification — energy storage, services, FSD software, and the Optimus
        humanoid robotics program collectively reduce automotive revenue dependency from ~85%
        to a projected ~65% by FY2030. This multi-vertical platform strategy creates an
        earnings base increasingly decoupled from EV pricing dynamics.</p>
    </div>

    <div class="chart-full">
        <img src="{chart_fcf}" alt="FCF Trend" style="max-width: 80%">
    </div>

    <div class="slide-footer">Tesla (TSLA) — M&A Valuation Analysis  |  {data['analysis_date']}  |  Prepared for Bain & Company Portfolio Review</div>
    <div class="slide-number">3 / 3</div>
</div>

</body>
</html>"""

    return html


def main():
    print("\n" + "=" * 72)
    print("  EXECUTIVE TEASER DECK GENERATOR")
    print("=" * 72 + "\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(DATA_FILE)
    print(f"  + Loaded financial data")

    if not SUMMARY_FILE.exists():
        print("  ! analysis_summary.json not found — run ratio_analysis.py first")
        print("    Generating summary data inline...")
        # Inline DCF for standalone execution
        from ratio_analysis import run_dcf, compute_ratios
        ratios = compute_ratios(data)
        dcf = run_dcf(data)
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
        }
    else:
        summary = load_json(SUMMARY_FILE)
        print(f"  + Loaded analysis summary")

    # Check for chart images
    chart_count = len(list(CHARTS_DIR.glob("*.png"))) if CHARTS_DIR.exists() else 0
    if chart_count == 0:
        print("  ! No chart images found — run ratio_analysis.py first for embedded visuals")
    else:
        print(f"  + Found {chart_count} chart images to embed")

    html = generate_html(data, summary)

    out_path = OUTPUT_DIR / "executive_teaser.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  + Executive teaser deck saved to {out_path.relative_to(ROOT_DIR)}")
    print(f"    Open in browser to view the 3-slide presentation")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
