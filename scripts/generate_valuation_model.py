#!/usr/bin/env python3
"""
╔==========================================================================╗
║  Tesla (TSLA) — DCF & Comparable Valuation Excel Workbook Generator    ║
║  Bain & Company M&A Readiness Portfolio Project                        ║
╚==========================================================================╝

Generates a professionally formatted Excel workbook with four tabs:
  1. Historical Financials  — 5-year P&L, Balance Sheet, Cash Flow
  2. DCF Model              — Revenue projections, FCF build, WACC, Terminal Value
  3. Comparable Analysis    — Tesla vs peers (EV/EBITDA, P/E, EV/Revenue)
  4. Sensitivity Analysis   — Revenue Growth Δ × WACC implied price grid

Usage:
    python generate_valuation_model.py

Output:
    output/valuation_model.xlsx
"""

import json
import argparse
import numpy as np
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule

ROOT_DIR   = Path(__file__).resolve().parent.parent
DATA_FILE  = ROOT_DIR / "data" / "tesla_financials.json"
COMPANIES_FILE = ROOT_DIR / "data" / "companies.json"
OUTPUT_DIR = ROOT_DIR / "output"

# -- Bain-inspired styling constants --
NAVY_FILL    = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
RED_FILL     = PatternFill(start_color="CC0000", end_color="CC0000", fill_type="solid")
LIGHT_GREY   = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
LIGHT_BLUE   = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
LIGHT_GREEN  = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
LIGHT_RED    = PatternFill(start_color="FCE4EC", end_color="FCE4EC", fill_type="solid")
LIGHT_YELLOW = PatternFill(start_color="FFF9C4", end_color="FFF9C4", fill_type="solid")

WHITE_BOLD   = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
NAVY_BOLD    = Font(name="Calibri", bold=True, color="003366", size=11)
RED_BOLD     = Font(name="Calibri", bold=True, color="CC0000", size=11)
NORMAL       = Font(name="Calibri", size=11)
HEADER_FONT  = Font(name="Calibri", bold=True, color="FFFFFF", size=12)
TITLE_FONT   = Font(name="Calibri", bold=True, color="003366", size=14)
SMALL_ITALIC = Font(name="Calibri", italic=True, color="666666", size=9)

THIN_BORDER  = Border(
    bottom=Side(style="thin", color="D0D0D0"),
)
BOTTOM_BORDER = Border(
    bottom=Side(style="medium", color="003366"),
)

CENTER = Alignment(horizontal="center", vertical="center")
RIGHT  = Alignment(horizontal="right", vertical="center")
LEFT   = Alignment(horizontal="left", vertical="center")
WRAP   = Alignment(horizontal="left", vertical="center", wrap_text=True)

NUM_FMT_INT  = '#,##0'
NUM_FMT_DEC1 = '#,##0.0'
NUM_FMT_PCT  = '0.0%'
NUM_FMT_PCT2 = '0.00%'
NUM_FMT_USD  = '$#,##0.00'
NUM_FMT_MULT = '0.0"x"'


def load_data(ticker: str = "TSLA"):
    if COMPANIES_FILE.exists():
        with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
            all_comps = json.load(f).get("companies", {})
            if ticker in all_comps:
                return all_comps[ticker]
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_header_row(ws, row, col_start, values, fill=NAVY_FILL, font=WHITE_BOLD):
    """Write a styled header row."""
    for i, val in enumerate(values):
        cell = ws.cell(row=row, column=col_start + i, value=val)
        cell.font = font
        cell.fill = fill
        cell.alignment = CENTER
        cell.border = THIN_BORDER


def _write_data_row(ws, row, col_start, label, values, fmt=NUM_FMT_INT,
                    label_font=NORMAL, value_font=NORMAL, bold_label=False,
                    fill=None, border=THIN_BORDER):
    """Write a labeled data row."""
    lbl = ws.cell(row=row, column=col_start, value=label)
    lbl.font = NAVY_BOLD if bold_label else label_font
    lbl.alignment = LEFT
    lbl.border = border
    if fill:
        lbl.fill = fill

    for i, val in enumerate(values):
        cell = ws.cell(row=row, column=col_start + 1 + i, value=val)
        cell.font = value_font
        cell.number_format = fmt
        cell.alignment = RIGHT
        cell.border = border
        if fill:
            cell.fill = fill


def _section_title(ws, row, col, title, span=6):
    """Write a section title row."""
    cell = ws.cell(row=row, column=col, value=title)
    cell.font = TITLE_FONT
    cell.alignment = LEFT
    ws.merge_cells(start_row=row, start_column=col,
                   end_row=row, end_column=col + span - 1)


# ===========================================================================
# TAB 1 — HISTORICAL FINANCIALS
# ===========================================================================

def build_historical_tab(wb, data):
    ws = wb.active
    ws.title = "Historical Financials"
    ws.sheet_properties.tabColor = "003366"

    years = data["fiscal_years"]
    inc = data["income_statement"]
    bs  = data["balance_sheet"]
    cf  = data["cash_flow_statement"]
    shares = data.get("shares_outstanding", [data["market_data"]["shares_outstanding_current"]] * len(years))

    col_w = {"A": 32, "B": 15, "C": 15, "D": 15, "E": 15, "F": 15}
    for c, w in col_w.items():
        ws.column_dimensions[c].width = w

    r = 1
    _section_title(ws, r, 1, f"{data['company']} ({data['ticker']}) — Historical Financial Summary"); r += 1
    unit_str = data.get("unit_label", data.get("units", "Financials in Millions"))
    note = ws.cell(row=r, column=1, value=unit_str)
    note.font = SMALL_ITALIC; r += 2

    # -- Income Statement --
    _section_title(ws, r, 1, "Income Statement"); r += 1
    _write_header_row(ws, r, 1, ["Metric"] + years); r += 1

    is_rows = [
        ("Revenue",                    inc["revenue"],                    False, None),
        ("  Cost of Revenue",          inc["cost_of_revenue"],            False, None),
        ("Gross Profit",               inc["gross_profit"],               True,  LIGHT_BLUE),
        ("  R&D Expense",              inc["research_development"],       False, None),
        ("  SG&A Expense",             inc["selling_general_admin"],      False, None),
        ("Operating Income (EBIT)",    inc["operating_income"],           True,  None),
        ("  Depreciation & Amort.",    inc["depreciation_amortization"],  False, None),
        ("EBITDA",                     inc["ebitda"],                     True,  LIGHT_BLUE),
        ("  Interest Expense",         inc["interest_expense"],           False, None),
        ("  Tax Expense",              inc["tax_expense"],                False, None),
        ("Net Income",                 inc["net_income"],                 True,  LIGHT_GREEN),
    ]
    for label, vals, bold, fill in is_rows:
        _write_data_row(ws, r, 1, label, vals, bold_label=bold, fill=fill); r += 1

    # Margins
    r += 1; _section_title(ws, r, 1, "Key Margins"); r += 1
    _write_header_row(ws, r, 1, ["Metric"] + years); r += 1

    revenue = np.array(inc["revenue"], dtype=float)
    gm  = np.array(inc["gross_profit"], dtype=float) / revenue
    em  = np.array(inc["ebitda"], dtype=float) / revenue
    om  = np.array(inc["operating_income"], dtype=float) / revenue
    nm  = np.array(inc["net_income"], dtype=float) / revenue

    for label, vals in [("Gross Margin", gm), ("EBITDA Margin", em),
                        ("Operating Margin", om), ("Net Margin", nm)]:
        _write_data_row(ws, r, 1, label, vals.tolist(), fmt=NUM_FMT_PCT,
                        bold_label=True, fill=LIGHT_YELLOW); r += 1

    # Revenue growth
    rev_g = [None] + [(revenue[i] - revenue[i-1]) / revenue[i-1]
                      for i in range(1, len(revenue))]
    _write_data_row(ws, r, 1, "Revenue Growth YoY", rev_g, fmt=NUM_FMT_PCT,
                    bold_label=True, fill=LIGHT_YELLOW); r += 1

    # -- Balance Sheet --
    r += 1; _section_title(ws, r, 1, "Balance Sheet"); r += 1
    _write_header_row(ws, r, 1, ["Metric"] + years); r += 1

    bs_rows = [
        ("Cash & Equivalents",     bs["cash_and_equivalents"],  False, None),
        ("Current Assets",         bs["current_assets"],        False, None),
        ("Total Assets",           bs["total_assets"],          True,  LIGHT_BLUE),
        ("Current Liabilities",    bs["current_liabilities"],   False, None),
        ("Total Debt",             bs["total_debt"],            False, None),
        ("Total Equity",           bs["total_equity"],          True,  LIGHT_GREEN),
    ]
    for label, vals, bold, fill in bs_rows:
        _write_data_row(ws, r, 1, label, vals, bold_label=bold, fill=fill); r += 1

    # NWC
    nwc = [ca - cl for ca, cl in zip(bs["current_assets"], bs["current_liabilities"])]
    _write_data_row(ws, r, 1, "Net Working Capital", nwc, bold_label=True, fill=LIGHT_YELLOW); r += 1

    # Returns
    eq = np.array(bs["total_equity"], dtype=float)
    ni = np.array(inc["net_income"], dtype=float)
    roe = (ni / eq).tolist()
    _write_data_row(ws, r, 1, "Return on Equity (ROE)", roe, fmt=NUM_FMT_PCT,
                    bold_label=True, fill=LIGHT_YELLOW); r += 1

    # -- Cash Flow Statement --
    r += 1; _section_title(ws, r, 1, "Cash Flow Statement"); r += 1
    _write_header_row(ws, r, 1, ["Metric"] + years); r += 1

    cf_rows = [
        ("Operating Cash Flow",  cf["operating_cash_flow"],  False, None),
        ("Capital Expenditures", [-x for x in cf["capital_expenditures"]], False, None),
        ("Free Cash Flow",       cf["free_cash_flow"],       True,  LIGHT_GREEN),
    ]
    for label, vals, bold, fill in cf_rows:
        _write_data_row(ws, r, 1, label, vals, bold_label=bold, fill=fill); r += 1

    _write_data_row(ws, r, 1, "Shares Outstanding (M)", shares,
                    bold_label=True, fill=LIGHT_YELLOW); r += 1

    print("  + Tab 1: Historical Financials")


# ===========================================================================
# TAB 2 — DCF MODEL
# ===========================================================================

def build_dcf_tab(wb, data):
    ws = wb.create_sheet("DCF Model")
    ws.sheet_properties.tabColor = "CC0000"

    a   = data["dcf_assumptions"]
    w   = data["wacc_inputs"]
    mkt = data["market_data"]
    bs  = data["balance_sheet"]

    col_w = {"A": 30}
    for i in range(2, 9):
        col_w[get_column_letter(i)] = 16
    for c, wd in col_w.items():
        ws.column_dimensions[c].width = wd

    r = 1
    _section_title(ws, r, 1, "Discounted Cash Flow (DCF) Valuation Model", span=7); r += 1
    ws.cell(row=r, column=1, value="5-Year projection with Gordon Growth Terminal Value").font = SMALL_ITALIC
    r += 2

    # -- WACC Calculation --
    _section_title(ws, r, 1, "WACC Calculation", span=3); r += 1
    _write_header_row(ws, r, 1, ["Parameter", "Value", ""], fill=NAVY_FILL); r += 1

    rf  = w["risk_free_rate"]
    beta = w["beta"]
    erp = w["equity_risk_premium"]
    ke  = w.get("cost_of_equity", rf + beta * erp)
    kd_pre = w.get("cost_of_debt_pretax", 0.045)
    tax_r  = w.get("tax_rate", 0.21)
    kd_after = w.get("cost_of_debt_aftertax", kd_pre * (1 - tax_r))
    e_w = w.get("equity_weight", 0.92)
    d_w = w.get("debt_weight", 0.08)

    wacc_rows = [
        ("Risk-Free Rate (Rf)",       rf),
        ("Beta (β)",                   beta),
        ("Equity Risk Premium (ERP)",  erp),
        ("Cost of Equity (Ke)",        ke),
        ("Pre-Tax Cost of Debt (Kd)",  kd_pre),
        ("Tax Rate",                   tax_r),
        ("After-Tax Cost of Debt",     kd_after),
        ("Equity Weight (E/V)",        e_w),
        ("Debt Weight (D/V)",          d_w),
    ]
    for label, val in wacc_rows:
        fmt = NUM_FMT_PCT2 if isinstance(val, float) and val < 1 else NUM_FMT_DEC1
        _write_data_row(ws, r, 1, label, [val], fmt=fmt); r += 1

    _write_data_row(ws, r, 1, "WACC", [w["wacc"]], fmt=NUM_FMT_PCT2,
                    bold_label=True, fill=LIGHT_GREEN); r += 2

    # -- Revenue Projections --
    base_rev = float(data["income_statement"]["revenue"][-1])
    growth_rates = a["revenue_growth_rates"]
    num_years = a.get("projection_years", len(growth_rates))
    proj_years = [f"FY{2026+i}E" for i in range(num_years)]

    _section_title(ws, r, 1, "5-Year Revenue & FCF Projections", span=7); r += 1
    _write_header_row(ws, r, 1, ["Metric", "Base (FY2025E)"] + proj_years); r += 1

    # Compute projections
    proj_rev = []
    rv = base_rev
    for g in growth_rates:
        rv *= (1 + g)
        proj_rev.append(rv)

    tax = w["tax_rate"]
    proj_ebitda = [rv * m for rv, m in zip(proj_rev, a["ebitda_margin_targets"])]
    proj_da     = [rv * d for rv, d in zip(proj_rev, a["da_pct_revenue"])]
    proj_ebit   = [e - d for e, d in zip(proj_ebitda, proj_da)]
    proj_capex  = [rv * c for rv, c in zip(proj_rev, a["capex_pct_revenue"])]
    proj_nwc    = [rv * n for rv, n in zip(proj_rev, a["nwc_pct_revenue"])]

    base_nwc = base_rev * 0.248
    delta_nwc = [proj_nwc[0] - base_nwc]
    for i in range(1, len(proj_nwc)):
        delta_nwc.append(proj_nwc[i] - proj_nwc[i - 1])

    proj_fcf = [ebit * (1 - tax) + da - capex - dnwc
                for ebit, da, capex, dnwc in zip(proj_ebit, proj_da, proj_capex, delta_nwc)]

    rows = [
        ("Revenue Growth",         [None] + growth_rates,                        NUM_FMT_PCT),
        ("Revenue",                [base_rev] + proj_rev,                        NUM_FMT_INT),
        ("EBITDA Margin",          [None] + a["ebitda_margin_targets"],           NUM_FMT_PCT),
        ("EBITDA",                 [None] + proj_ebitda,                          NUM_FMT_INT),
        ("D&A",                    [None] + proj_da,                              NUM_FMT_INT),
        ("EBIT",                   [None] + proj_ebit,                            NUM_FMT_INT),
        ("EBIT × (1 - t)",        [None] + [e * (1-tax) for e in proj_ebit],     NUM_FMT_INT),
        ("+ D&A",                  [None] + proj_da,                              NUM_FMT_INT),
        ("- CapEx",                [None] + [-c for c in proj_capex],              NUM_FMT_INT),
        ("- Δ NWC",                [None] + [-d for d in delta_nwc],               NUM_FMT_INT),
    ]
    for label, vals, fmt in rows:
        _write_data_row(ws, r, 1, label, vals, fmt=fmt); r += 1

    _write_data_row(ws, r, 1, "Free Cash Flow (FCF)", [None] + proj_fcf,
                    fmt=NUM_FMT_INT, bold_label=True, fill=LIGHT_GREEN); r += 2

    # -- Discounting --
    _section_title(ws, r, 1, "Present Value Calculation", span=7); r += 1
    _write_header_row(ws, r, 1, ["Metric", ""] + proj_years); r += 1

    wacc_val = w["wacc"]
    disc = [(1 + wacc_val) ** (-t) for t in range(1, len(proj_fcf) + 1)]
    pv_fcfs = [f * d for f, d in zip(proj_fcf, disc)]

    _write_data_row(ws, r, 1, "Discount Factor", [None] + disc, fmt='0.0000'); r += 1
    _write_data_row(ws, r, 1, "PV of FCF", [None] + pv_fcfs, fmt=NUM_FMT_INT,
                    bold_label=True, fill=LIGHT_BLUE); r += 2

    # -- Terminal Value & EV Bridge --
    _section_title(ws, r, 1, "Terminal Value & Enterprise Value Bridge", span=4); r += 1
    _write_header_row(ws, r, 1, ["Component", "Value ($M)", "", ""], fill=NAVY_FILL); r += 1

    tg = a["terminal_growth_rate"]
    terminal_fcf = proj_fcf[-1] * (1 + tg)
    tv = terminal_fcf / (wacc_val - tg)
    pv_tv = tv * disc[-1]
    pv_fcf_sum = sum(pv_fcfs)
    ev = pv_fcf_sum + pv_tv
    net_debt = float(bs["total_debt"][-1]) - float(bs["cash_and_equivalents"][-1])
    eq_val = ev - net_debt
    implied = eq_val / mkt["shares_outstanding_current"]

    bridge = [
        ("Terminal Growth Rate (g)",  tg,         NUM_FMT_PCT2, None),
        ("Terminal Year FCF × (1+g)", terminal_fcf, NUM_FMT_INT, None),
        ("Terminal Value",            tv,          NUM_FMT_INT,  None),
        ("PV of Terminal Value",      pv_tv,       NUM_FMT_INT,  LIGHT_BLUE),
        ("",                          None,        None,         None),
        ("Sum of PV(FCFs)",           pv_fcf_sum,  NUM_FMT_INT,  None),
        ("+ PV of Terminal Value",    pv_tv,       NUM_FMT_INT,  None),
        ("= Enterprise Value",        ev,          NUM_FMT_INT,  LIGHT_BLUE),
        ("- Net Debt (+ = Cash)",     -net_debt,   NUM_FMT_INT,  None),
        ("= Equity Value",            eq_val,      NUM_FMT_INT,  LIGHT_GREEN),
        ("/ Shares Outstanding (M)",  mkt["shares_outstanding_current"], NUM_FMT_INT, None),
        ("Implied Price per Share",   implied,     NUM_FMT_USD,  LIGHT_GREEN),
        ("",                          None,        None,         None),
        ("Current Market Price",      mkt["current_stock_price"], NUM_FMT_USD, None),
        ("Upside / (Downside)",       (implied - mkt["current_stock_price"]) / mkt["current_stock_price"],
         NUM_FMT_PCT, LIGHT_YELLOW),
    ]
    for label, val, fmt, fill in bridge:
        if label == "":
            r += 1; continue
        vals = [val] if val is not None else [None]
        f = fmt if fmt else NUM_FMT_INT
        _write_data_row(ws, r, 1, label, vals, fmt=f, bold_label=True, fill=fill); r += 1

    print("  + Tab 2: DCF Model")


# ===========================================================================
# TAB 3 — COMPARABLE ANALYSIS
# ===========================================================================

def build_comps_tab(wb, data):
    ws = wb.create_sheet("Comparable Analysis")
    ws.sheet_properties.tabColor = "0066CC"

    comp = data["comparable_companies"]
    names = comp["names"]

    col_w = {"A": 24}
    for i in range(2, 12):
        col_w[get_column_letter(i)] = 16
    for c, wd in col_w.items():
        ws.column_dimensions[c].width = wd

    r = 1
    _section_title(ws, r, 1, "Comparable Company Analysis", span=7); r += 1
    ws.cell(row=r, column=1,
            value="Benchmarking Tesla against EV/Auto industry peers").font = SMALL_ITALIC
    r += 2

    # -- Trading Multiples --
    headers = ["Company", "Ticker", "Market Cap ($M)", "EV ($M)",
               "EV/Revenue", "EV/EBITDA", "P/E", "Rev Growth", "Gross Margin"]
    _write_header_row(ws, r, 1, headers); r += 1

    fields = [
        ("tickers",           None),
        ("market_cap",        NUM_FMT_INT),
        ("enterprise_value",  NUM_FMT_INT),
        ("ev_revenue",        NUM_FMT_MULT),
        ("ev_ebitda",         NUM_FMT_MULT),
        ("pe_ratio",          NUM_FMT_MULT),
        ("revenue_growth_yoy", NUM_FMT_PCT),
        ("gross_margin",      NUM_FMT_PCT),
    ]

    for idx, name in enumerate(names):
        is_tesla = (name == "Tesla")
        fill = LIGHT_BLUE if is_tesla else None

        # Company name
        nc = ws.cell(row=r, column=1, value=name)
        nc.font = NAVY_BOLD if is_tesla else NORMAL
        nc.alignment = LEFT
        if fill: nc.fill = fill

        for j, (field, fmt) in enumerate(fields):
            vals_list = comp.get(field, [])
            val = vals_list[idx] if idx < len(vals_list) else None
            cell = ws.cell(row=r, column=2 + j,
                           value=val if val is not None else "N/M")
            cell.alignment = RIGHT
            cell.font = NAVY_BOLD if is_tesla else NORMAL
            if fill: cell.fill = fill
            if val is not None and fmt:
                cell.number_format = fmt
        r += 1

    # -- Implied valuation from comps --
    r += 2
    _section_title(ws, r, 1, "Implied Valuation from Peer Multiples", span=5); r += 1
    _write_header_row(ws, r, 1, ["Method", "Peer Median", "Target Metric",
                                  "Implied EV ($M)", "Implied Price"], fill=RED_FILL); r += 1

    target_ebitda = float(comp.get("ebitda_ttm", [data["income_statement"]["ebitda"][-1]])[0])
    target_rev    = float(comp.get("revenue_ttm", [data["income_statement"]["revenue"][-1]])[0])
    net_debt = float(data["balance_sheet"]["total_debt"][-1]) - \
               float(data["balance_sheet"]["cash_and_equivalents"][-1])
    shares   = data["market_data"]["shares_outstanding_current"]

    # Compute peer medians (excluding Target, only positive values)
    ev_ebitda_peers = [v for i, v in enumerate(comp.get("ev_ebitda", []))
                       if v is not None and v > 0 and i != 0]
    pe_peers = [v for i, v in enumerate(comp.get("pe_ratio", []))
                if v is not None and v > 0 and i != 0]
    ev_rev_peers = [v for i, v in enumerate(comp.get("ev_revenue", []))
                    if v is not None and v > 0 and i != 0]

    comps_methods = []
    if ev_ebitda_peers:
        median_ev_ebitda = sorted(ev_ebitda_peers)[len(ev_ebitda_peers) // 2]
        imp_ev = median_ev_ebitda * target_ebitda
        imp_eq = imp_ev - net_debt
        imp_price = imp_eq / shares
        comps_methods.append(("EV/EBITDA", median_ev_ebitda, target_ebitda, imp_ev, imp_price))

    if ev_rev_peers:
        median_ev_rev = sorted(ev_rev_peers)[len(ev_rev_peers) // 2]
        imp_ev = median_ev_rev * target_rev
        imp_eq = imp_ev - net_debt
        imp_price = imp_eq / shares
        comps_methods.append(("EV/Revenue", median_ev_rev, target_rev, imp_ev, imp_price))

    if pe_peers:
        median_pe = sorted(pe_peers)[len(pe_peers) // 2]
        target_ni = float(comp.get("net_income_ttm", [data["income_statement"]["net_income"][-1]])[0])
        imp_mc = median_pe * target_ni
        imp_price = imp_mc / shares
        comps_methods.append(("P/E Ratio", median_pe, target_ni, imp_mc, imp_price))

    for method, mult, metric, imp_ev, imp_price in comps_methods:
        row_vals = [mult, metric, imp_ev, imp_price]
        fmts = [NUM_FMT_MULT, NUM_FMT_INT, NUM_FMT_INT, NUM_FMT_USD]
        cell = ws.cell(row=r, column=1, value=method)
        cell.font = NAVY_BOLD; cell.alignment = LEFT
        for j, (val, fmt) in enumerate(zip(row_vals, fmts)):
            c = ws.cell(row=r, column=2 + j, value=val)
            c.number_format = fmt; c.alignment = RIGHT
        r += 1

    print("  + Tab 3: Comparable Analysis")


# ===========================================================================
# TAB 4 — SENSITIVITY ANALYSIS
# ===========================================================================

def build_sensitivity_tab(wb, data):
    ws = wb.create_sheet("Sensitivity Analysis")
    ws.sheet_properties.tabColor = "2E7D32"

    a    = data["dcf_assumptions"]
    w    = data["wacc_inputs"]
    mkt  = data["market_data"]
    bs   = data["balance_sheet"]
    tax  = w["tax_rate"]

    base_wacc = w["wacc"]
    base_rev  = float(data["income_statement"]["revenue"][-1])
    base_nwc_r = 0.248
    tg = a["terminal_growth_rate"]

    rev_deltas  = [-0.02, -0.01, 0.0, 0.01, 0.02]
    wacc_deltas = [-0.015, -0.010, -0.005, 0.0, 0.005, 0.010, 0.015]

    net_debt = float(bs["total_debt"][-1]) - float(bs["cash_and_equivalents"][-1])
    shares   = mkt["shares_outstanding_current"]

    col_w = {"A": 22}
    for i in range(2, 10):
        col_w[get_column_letter(i)] = 14
    for c, wd in col_w.items():
        ws.column_dimensions[c].width = wd

    r = 1
    _section_title(ws, r, 1, "Sensitivity Analysis — Implied Share Price ($)", span=8); r += 1
    ws.cell(row=r, column=1,
            value="Revenue Growth Δ (rows) × WACC (columns)").font = SMALL_ITALIC
    r += 2

    # Headers
    wacc_headers = [f"{(base_wacc + wd) * 100:.1f}%" for wd in wacc_deltas]
    _write_header_row(ws, r, 1, ["Rev Growth Δ \\ WACC"] + wacc_headers); r += 1

    current_price = mkt["current_stock_price"]

    for rd in rev_deltas:
        label = f"{rd * 100:+.0f}%"
        is_base = (rd == 0.0)
        values = []

        for wd in wacc_deltas:
            adj_wacc = base_wacc + wd
            if adj_wacc <= tg:
                values.append(None)
                continue

            rev = base_rev
            proj_rev = []
            for g in a["revenue_growth_rates"]:
                rev *= (1 + g + rd)
                proj_rev.append(rev)

            ebitda = [rv * m for rv, m in zip(proj_rev, a["ebitda_margin_targets"])]
            da     = [rv * d for rv, d in zip(proj_rev, a["da_pct_revenue"])]
            ebit   = [e - d for e, d in zip(ebitda, da)]
            capex  = [rv * c for rv, c in zip(proj_rev, a["capex_pct_revenue"])]
            nwc    = [rv * n for rv, n in zip(proj_rev, a["nwc_pct_revenue"])]

            dnwc = [nwc[0] - base_rev * base_nwc_r]
            for k in range(1, len(nwc)):
                dnwc.append(nwc[k] - nwc[k - 1])

            fcf = [eb * (1 - tax) + d - c - dn
                   for eb, d, c, dn in zip(ebit, da, capex, dnwc)]
            disc = [(1 + adj_wacc) ** (-t) for t in range(1, len(fcf) + 1)]
            pv_f = sum(f * d for f, d in zip(fcf, disc))
            tv = fcf[-1] * (1 + tg) / (adj_wacc - tg)
            pv_t = tv * disc[-1]
            eq = pv_f + pv_t - net_debt
            values.append(eq / shares)

        # Write row
        lbl_cell = ws.cell(row=r, column=1, value=label)
        lbl_cell.font = NAVY_BOLD if is_base else NORMAL
        lbl_cell.alignment = CENTER
        if is_base:
            lbl_cell.fill = LIGHT_YELLOW

        for j, val in enumerate(values):
            cell = ws.cell(row=r, column=2 + j, value=val)
            cell.number_format = NUM_FMT_USD
            cell.alignment = CENTER

            is_base_col = (wacc_deltas[j] == 0.0)
            if is_base and is_base_col:
                cell.fill = LIGHT_GREEN
                cell.font = NAVY_BOLD
            elif is_base or is_base_col:
                cell.fill = LIGHT_YELLOW

            # Conditional coloring
            if val is not None:
                if val > current_price * 1.1:
                    cell.font = Font(name="Calibri", bold=True, color="2E7D32")
                elif val < current_price * 0.9:
                    cell.font = Font(name="Calibri", bold=True, color="CC0000")
        r += 1

    # Legend
    r += 2
    ws.cell(row=r, column=1, value=f"Current Market Price: ${current_price:.2f}").font = NAVY_BOLD
    r += 1
    ws.cell(row=r, column=1, value="Green = >10% upside  |  Red = >10% downside").font = SMALL_ITALIC
    r += 1
    ws.cell(row=r, column=1, value="Highlighted cells = base case assumptions").font = SMALL_ITALIC

    print("  + Tab 4: Sensitivity Analysis")


# ===========================================================================
# MAIN
# ===========================================================================

def generate_workbook(ticker: str = "TSLA"):
    data = load_data(ticker)
    comp_name = data.get("company", ticker)
    print(f"  Generating Excel model for: {comp_name} ({ticker})")

    wb = Workbook()
    build_historical_tab(wb, data)
    build_dcf_tab(wb, data)
    build_comps_tab(wb, data)
    build_sensitivity_tab(wb, data)

    # Save as default valuation_model.xlsx for TSLA, or valuation_model_<TICKER>.xlsx
    if ticker.upper() == "TSLA":
        out_path = OUTPUT_DIR / "valuation_model.xlsx"
    else:
        out_path = OUTPUT_DIR / f"valuation_model_{ticker.upper()}.xlsx"

    wb.save(str(out_path))
    print(f"  + Workbook saved to {out_path.relative_to(ROOT_DIR)}\n")
    return out_path


def main():
    print("\n" + "=" * 72)
    print("  EXCEL VALUATION MODEL GENERATOR")
    print("=" * 72 + "\n")

    parser = argparse.ArgumentParser(description="Multi-Company Excel Valuation Model Generator")
    parser.add_argument("--company", "-c", default="TSLA", help="Target company ticker (TSLA, ZOMATO, AAPL, BYD)")
    parser.add_argument("--all", action="store_true", help="Generate Excel workbooks for all pre-loaded companies")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    target_tickers = ["TSLA", "ZOMATO", "AAPL", "BYD"] if args.all else [args.company.upper()]

    for ticker in target_tickers:
        generate_workbook(ticker)

    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
