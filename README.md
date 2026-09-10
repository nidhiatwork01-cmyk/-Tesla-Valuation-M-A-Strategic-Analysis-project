# 🏢 Tesla (TSLA) — Valuation & M&A Strategic Analysis

> **Institutional-grade DCF valuation, comparable company analysis, and strategic recommendation for Tesla Inc.**
> Built to demonstrate MBB-level business acumen, financial modeling, and strategic executive communication.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Excel](https://img.shields.io/badge/Excel-Workbook-217346?logo=microsoftexcel&logoColor=white)](output/valuation_model.xlsx)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📋 Executive Summary

| Metric | Value |
|:---|:---|
| **Target Company** | Tesla, Inc. (NASDAQ: TSLA) |
| **Analysis Date** | September 2026 |
| **Methodology** | DCF (5-year projection) + Comparable Company Analysis |
| **WACC** | 9.53% (CAPM-derived) |
| **Terminal Growth** | 2.5% (Gordon Growth Model) |
| **Revenue CAGR (FY2021–FY2025E)** | ~20.3% |

### 🎯 Key Findings

1. **Valuation**: Our DCF model implies Tesla is trading at a premium/discount to intrinsic value — see the full sensitivity analysis for the range of outcomes across WACC and growth scenarios.

2. **Growth Catalysts**: (a) Energy Storage (Megapack/Powerwall) growing >60% YoY with margins exceeding automotive; (b) FSD software creating a recurring, high-margin revenue stream.

3. **Key Risk**: Chinese EV price competition (BYD, NIO) pressuring automotive gross margins. **Mitigation**: Revenue diversification into energy + services reduces auto dependency to ~65% by FY2030.

---

## 📊 Financial Analysis

### Revenue & Growth Trajectory
![Revenue Growth](output/charts/revenue_growth.png)

Tesla's revenue grew at a ~20% CAGR from FY2021 ($53.8B) to FY2025E ($112.8B), driven by global EV adoption, energy storage expansion, and services revenue growth.

### Profitability Margin Trends
![Margin Analysis](output/charts/margin_analysis.png)

The FY2023 EV price war compressed gross margins from 25.6% to 18.2%. Recovery to 22.5% by FY2025E signals improving unit economics from manufacturing scale and cost optimization.

### Free Cash Flow
![FCF Trend](output/charts/fcf_trend.png)

FCF dipped to $0.7B in FY2024 due to heavy CapEx (Cybertruck ramp, Megapack factory, AI compute). Normalization to $4.5B in FY2025E as CapEx intensity moderates.

### Return Metrics
![ROE vs ROIC](output/charts/roe_roic.png)

Both ROE and ROIC consistently exceed S&P 500 averages, demonstrating efficient capital deployment across Tesla's expanding asset base.

---

## 💰 Valuation Model

### DCF Valuation Bridge
![DCF Waterfall](output/charts/dcf_waterfall.png)

**Methodology**: 5-year FCF projection using EBIT(1−t) + D&A − CapEx − ΔNWC, discounted at WACC of 9.53%. Terminal value via Gordon Growth Model at 2.5% perpetual growth.

### Comparable Company Analysis
![Comps](output/charts/comps_ev_ebitda.png)

Tesla trades at a significant premium to traditional auto peers (Ford: 6.2x EV/EBITDA) and even ahead of high-growth BYD (12.4x), reflecting the market's pricing of Tesla's technology platform optionality.

### Sensitivity Analysis
![Sensitivity Heatmap](output/charts/sensitivity_heatmap.png)

The sensitivity matrix shows implied share price across Revenue Growth (±2%) and WACC (±1.5%) scenarios, providing a range-bound view of intrinsic value.

---

## 🗂️ Repository Structure

```
bain-valuation-mna-model/
├── ratio_analysis.py              # Financial analysis engine (ratios + 7 charts + DCF)
├── generate_valuation_model.py    # Excel workbook generator (4 tabs)
├── generate_executive_deck.py     # 3-slide HTML executive teaser
├── requirements.txt               # Python dependencies
├── data/
│   └── tesla_financials.json      # 5-year financial data (reproducible)
├── output/
│   ├── valuation_model.xlsx       # ← DCF & Comps Excel Model
│   ├── executive_teaser.html      # ← 3-Slide Executive Deck
│   ├── analysis_summary.json      # Computed valuation data
│   └── charts/                    # 7 publication-quality PNG charts
│       ├── revenue_growth.png
│       ├── margin_analysis.png
│       ├── fcf_trend.png
│       ├── roe_roic.png
│       ├── comps_ev_ebitda.png
│       ├── sensitivity_heatmap.png
│       └── dcf_waterfall.png
└── README.md                      # ← You are here
```

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/bain-valuation-mna-model.git
cd bain-valuation-mna-model

# Install dependencies
pip install -r requirements.txt

# Run the full analysis pipeline
python ratio_analysis.py               # Generate charts + DCF + sensitivity
python generate_valuation_model.py      # Generate Excel workbook
python generate_executive_deck.py       # Generate HTML executive deck
```

### Output
- **7 financial charts** → `output/charts/`
- **Excel valuation model** → `output/valuation_model.xlsx`
- **Executive teaser deck** → `output/executive_teaser.html` (open in browser)

---

## 🔧 Methodology Deep Dive

### DCF Model
| Component | Approach |
|:---|:---|
| **Revenue Projections** | 5-year forecast: 12% → 7% declining growth (market maturation) |
| **FCF Build** | EBIT(1−t) + D&A − CapEx − ΔNWC |
| **WACC** | CAPM: Rf (3.8%) + β (1.25) × ERP (5.0%) = Ke (10.05%); weighted 92/8 E/D |
| **Terminal Value** | Gordon Growth: FCF₅ × (1+g) / (WACC−g), g = 2.5% |
| **EV → Equity** | Enterprise Value − Net Debt = Equity Value ÷ Shares |

### Comparable Analysis
| Peer | EV/EBITDA | P/E | EV/Revenue |
|:---|:---:|:---:|:---:|
| Tesla (TSLA) | 42.3x | 93.1x | 8.14x |
| BYD (BYDDY) | 12.4x | 18.5x | 1.51x |
| Ford (F) | 6.2x | 8.3x | 0.60x |
| Rivian (RIVN) | N/M | N/M | 3.47x |
| Lucid (LCID) | N/M | N/M | 3.90x |

---

## 📝 Data Sources

- **Tesla 10-K Annual Reports** (FY2021–FY2024) via SEC EDGAR
- **FY2025E**: Analyst consensus estimates
- **Market Data**: As of September 2026
- **WACC Inputs**: US 10-Year Treasury, Damodaran ERP dataset

---

## 🎯 Why This Matters for Consulting

> *"I built a full DCF and Comparable Valuation model for Tesla, evaluating 5-year cash flow projections and sensitivity matrices to deliver an M&A growth recommendation. The model identifies key value drivers in energy storage expansion and FSD software revenue, with a risk-adjusted view of competitive dynamics from Chinese EV OEMs."*

This project demonstrates:
- **Financial Modeling**: DCF with WACC derivation, terminal value, sensitivity analysis
- **Strategic Thinking**: Growth catalyst identification + risk mitigation framework
- **Data Engineering**: Automated Python pipeline generating institutional-quality outputs
- **Executive Communication**: 3-slide teaser deck format used in PE/M&A deal processes

---

*Built as a Bain & Company M&A readiness portfolio project.*
