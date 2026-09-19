import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from pathlib import Path
from datetime import datetime
import storage
from pdf_generator import (
    generate_health_report_pdf,
    generate_report_card_with_timeline_pdf
)

try:
    import documentai
except Exception:
    documentai = None

try:
    from aiengine import (
        generate_response,
        calculate_loan_amortization,
        calculate_sip_wealth
    )
except Exception:
    generate_response = None
    calculate_loan_amortization = None
    calculate_sip_wealth = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FinPath",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE & LOCAL STORAGE INITIALIZATION
# ============================================================

stored_data = storage.load_local_storage()

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "currency" not in st.session_state:
    st.session_state.currency = stored_data.get("currency", "INR")

if "profile" not in st.session_state:
    st.session_state.profile = stored_data.get("profile", {
        "name": "",
        "monthly_income": 0.0,
        "monthly_saving_capacity": 0.0
    })

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = stored_data.get("chat_messages", [
        {
            "role": "assistant",
            "content": (
                "Hello. I am your FinPath Financial Assistant. "
                "You can ask me about loan applications, health insurance, "
                "steps to deposit money, SIP wealth compounding, or any financial journey."
            )
        }
    ])

if "checklists" not in st.session_state:
    st.session_state.checklists = stored_data.get("checklists", {})

if "journey_twin" not in st.session_state:
    st.session_state.journey_twin = stored_data.get("journey_twin", {
        "action": "Select an action",
        "documents": {}
    })

# Sync current profile and currency to browser localStorage
storage.sync_to_browser_local_storage("finpath_profile", st.session_state.profile)
storage.sync_to_browser_local_storage("finpath_currency", st.session_state.currency)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        /* Root & Body zero-margin dark theme full screen setup */
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            height: 100% !important;
            overflow-x: hidden !important;
            background-color: #0b1120 !important;
        }

        /* Main application container */
        .stApp {
            background-color: #0b1120 !important;
            color: #f8fafc !important;
            min-height: 100vh !important;
        }

        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            max-width: 1400px;
        }

        /* Professional navy sidebar - Full Height Flex Layout */
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b !important;
            overflow: hidden !important;
            -ms-overflow-style: none !important;
            scrollbar-width: none !important;
        }

        section[data-testid="stSidebar"] > div {
            padding: 0.85rem 0.65rem 0.65rem 0.65rem !important;
            height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            gap: 0.15rem !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }

        /* Sidebar profile card */
        .sidebar-profile-card {
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 0.65rem 0.75rem;
            margin-top: 0.4rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }

        .card-white { color: #f8fafc !important; }
        .card-muted { color: #94a3b8 !important; }
        .card-sub { color: #cbd5e1 !important; }
        .card-green { color: #4ade80 !important; }
        .card-blue { color: #38bdf8 !important; }

        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }

        p, div, span, label {
            color: #cbd5e1 !important;
        }

        /* Hero Banner */
        .hero-box {
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #0369a1 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.5rem;
            color: #ffffff !important;
            box-shadow: 0 8px 24px rgba(0, 127, 255, 0.18);
        }

        .hero-box h1, .hero-box p {
            color: #ffffff !important;
        }

        /* Feature Cards */
        .feature-box {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.1rem;
            height: 155px;
            min-height: 155px;
            max-height: 155px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }

        .feature-box:hover {
            border-color: #007FFF;
            transform: translateY(-2px);
        }

        .feature-box h3 {
            font-size: 1.05rem !important;
            margin: 0 0 0.35rem 0 !important;
            color: #f8fafc !important;
        }

        .feature-box p {
            font-size: 0.85rem !important;
            line-height: 1.35 !important;
            color: #94a3b8 !important;
            margin: 0 !important;
        }

        /* Blue Callout Notes */
        .blue-note {
            background: rgba(30, 58, 138, 0.35);
            border: 1px solid #2563eb;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
        }

        .blue-note strong, .blue-note b {
            color: #93c5fd !important;
        }

        /* Metric Cards */
        div[data-testid="stMetric"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
        }

        div[data-testid="stMetric"] label {
            color: #94a3b8 !important;
            font-size: 0.8rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }

        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #f8fafc !important;
            font-size: 1.45rem !important;
            font-weight: 700 !important;
        }

        /* Available & Missing Boxes */
        .available-box {
            background-color: #052e16 !important;
            border: 1px solid #16a34a !important;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .missing-box {
            background-color: #450a0a !important;
            border: 1px solid #dc2626 !important;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        /* Form Inputs */
        input, textarea, select {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            border-radius: 6px !important;
        }

        div[data-baseweb="select"] > div {
            background-color: #1e293b !important;
            border-color: #334155 !important;
        }

        div[data-baseweb="select"] * {
            color: #f8fafc !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def currency_symbol():
    symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    return symbols.get(st.session_state.currency, "₹")


def money(value):
    try:
        val = safe_float(value, 0.0)
        return f"{currency_symbol()}{val:,.2f}"
    except Exception:
        return f"{currency_symbol()}0.00"


def calculate_fixed_deposit(principal, annual_rate, years):
    interest = principal * (annual_rate / 100.0) * years
    maturity = principal + interest
    return interest, maturity


def calculate_recurring_deposit(monthly_amount, annual_rate, months):
    monthly_rate = annual_rate / 100.0 / 12.0
    if monthly_rate == 0:
        maturity = monthly_amount * months
    else:
        maturity = (
            monthly_amount
            * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            * (1 + monthly_rate)
        )
    total_deposit = monthly_amount * months
    interest = maturity - total_deposit
    return interest, maturity


def get_chat_response(question):
    # Try AI Engine first if available
    if generate_response is not None:
        try:
            profile = st.session_state.get("profile", {})
            try:
                res = generate_response(question, profile=profile)
            except TypeError:
                res = generate_response(question)

            if isinstance(res, dict):
                answer = res.get("answer") or res.get("response") or res.get("message")
                if answer:
                    return answer
            elif res:
                return str(res)
        except Exception:
            pass

    question_lower = question.lower()

    # Loan Application Walkthrough
    if any(phrase in question_lower for phrase in ["how to apply", "apply for loan", "apply for a loan", "loan steps", "loan application"]):
        return (
            "Here is the step-by-step guide on **How to Apply for a Loan**:\n\n"
            "1. **Check Affordability & EMI:** Ensure projected EMI stays below 40% of your net monthly income.\n"
            "2. **Check Credit Score (CIBIL):** Maintain a score of 750+ for lowest interest rates and fast approval.\n"
            "3. **Compare Lenders:** Compare floating vs fixed interest rates, processing fees (0.5% - 2%), and total APR.\n"
            "4. **Gather Documents:** PAN, Aadhaar/Passport, 3-6 months payslips / 2-3 years ITR, 6 months bank statements, and property/collateral documents.\n"
            "5. **Submit Application:** Apply digitally or at a branch for physical/video KYC and verification.\n"
            "6. **Review Sanction Letter:** Audit interest rate, tenure, prepayment terms, and penal interest in Document AI.\n"
            "7. **Complete NACH Auto-Debit & Disbursement:** Authorize electronic mandate and receive disbursement."
        )

    # Health Insurance Walkthrough
    if any(phrase in question_lower for phrase in ["how to take health insurance", "how to buy health insurance", "buy health insurance", "take insurance", "choose health insurance"]):
        return (
            "Here is the step-by-step guide on **How to Choose & Take Health Insurance**:\n\n"
            "1. **Determine Sum Insured:** Choose a base coverage equal to at least 50% to 100% of annual household income (minimum ₹10-15 Lakhs).\n"
            "2. **Select Policy Type:** Family Floater for couples/young children; Individual policy for senior citizen parents.\n"
            "3. **Audit Key Clauses:**\n"
            "   - **Room Rent Limit:** Select *No Room Rent Sub-Limit* to prevent proportionate claim deductions.\n"
            "   - **Co-Payment:** Ensure *0% Co-Pay* so you don't pay 10%-20% out-of-pocket on every claim.\n"
            "   - **PED Waiting Period:** Choose shorter waiting periods (1-3 years).\n"
            "   - **Restoration Benefit:** Ensure 100% sum insured auto-refills upon exhaustion.\n"
            "4. **Verify Hospital Network:** Confirm major hospitals near your home offer cashless settlement.\n"
            "5. **Accurate Proposal Form Disclosures:** Disclose all pre-existing medical conditions truthfully to prevent claim rejections.\n"
            "6. **Pay Premium & Save Helpline:** Download the policy schedule and keep the 24/7 TPA helpline saved."
        )

    # Steps to Deposit Money / Open FD / RD
    if any(phrase in question_lower for phrase in ["steps to deposit", "how to deposit", "open fixed deposit", "open fd", "deposit money", "how to save in bank"]):
        return (
            "Here is the step-by-step guide on **How to Deposit Money & Open a Bank Deposit (FD / RD)**:\n\n"
            "1. **Choose Deposit Type:** Fixed Deposit (FD) for lump-sum amounts; Recurring Deposit (RD) for monthly savings.\n"
            "2. **Compare Interest Rates:** Check 1 to 3-year tenures for peak interest rates (+0.50% extra for senior citizens).\n"
            "3. **Select Payout Option:** Cumulative (compounded quarterly for maximum wealth) or Non-Cumulative (monthly/quarterly interest payout for cash flow).\n"
            "4. **Complete KYC:** Open in seconds via Net Banking/Mobile App for existing accounts, or provide PAN + Aadhaar at branch.\n"
            "5. **Add a Nominee:** Always register a nominee to ensure smooth transfer to legal heirs.\n"
            "6. **Manage TDS (Form 15G / 15H):** Submit Form 15G/15H if your annual income is non-taxable to prevent 10% TDS on interest.\n"
            "7. **Set Maturity Instructions:** Choose auto-renewal or direct credit to your savings account upon maturity."
        )

    # How to Start a SIP
    if any(phrase in question_lower for phrase in ["how to start a sip", "start sip", "how to invest in sip", "sip steps"]):
        return (
            "Here is the step-by-step guide on **How to Start a Systematic Investment Plan (SIP)**:\n\n"
            "1. **Complete Mutual Fund KYC:** Submit PAN, Aadhaar OTP verification, and bank details online.\n"
            "2. **Define Goal & Horizon:** Debt funds for <3 years; Hybrid funds for 3-5 years; Index/Flexi-cap equity funds for >5 years.\n"
            "3. **Choose Direct-Growth Plans:** Direct plans avoid distributor commissions, boosting returns by 1% to 1.5% every year.\n"
            "4. **Set Monthly Auto-Debit:** Schedule the debit date 2-3 days after monthly salary credit.\n"
            "5. **Activate Annual Step-Up:** Increase monthly SIP by 10% each year with salary hikes to more than double your 15-year corpus.\n"
            "6. **Stay Disciplined:** Continue investing through market corrections to maximize Rupee Cost Averaging."
        )

    # How to Repay Loans Faster
    if any(phrase in question_lower for phrase in ["how to repay", "repay loan faster", "prepayment", "loan repayment"]):
        return (
            "Here is the step-by-step playbook to **Repay Your Loan Faster and Slash Interest**:\n\n"
            "1. **The 13th EMI Technique:** Pay 1 extra EMI each year to cut a 20-year home loan by 4 to 5 full years.\n"
            "2. **5% Annual Step-Up:** Increase your EMI by 5% every year as income rises to shave ~7 years off a 20-year tenure.\n"
            "3. **Direct Principal Prepayment:** Apply bonuses and tax refunds to Principal Reduction rather than advance EMI storage.\n"
            "4. **Choose Tenure Reduction:** Always instruct lender to reduce loan tenure rather than monthly EMI.\n"
            "5. **Debt Avalanche:** Prioritize surplus funds on highest-interest debts first (Credit cards > Personal loans > Auto loans > Home loans)."
        )

    return (
        "I can help you with step-by-step procedural guides (applying for loans, buying health insurance, depositing money, starting a SIP), "
        "as well as mathematical loan and investment calculations. Please ask any specific financial question."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    # Check Flask backend connectivity
    backend_online = False
    try:
        r = requests.get("http://127.0.0.1:5000/health", timeout=0.2)
        if r.status_code == 200:
            backend_online = True
    except Exception:
        backend_online = False

    status_pill = (
        '<div style="display:inline-flex;align-items:center;gap:0.35rem;background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.3);border-radius:12px;padding:2px 8px;margin-bottom:0.5rem;font-size:0.68rem;color:#4ade80;">'
        '<span style="width:6px;height:6px;border-radius:50%;background-color:#22c55e;display:inline-block;"></span> Flask API Synced'
        '</div>'
    ) if backend_online else (
        '<div style="display:inline-flex;align-items:center;gap:0.35rem;background:rgba(56,189,248,0.15);border:1px solid rgba(56,189,248,0.3);border-radius:12px;padding:2px 8px;margin-bottom:0.5rem;font-size:0.68rem;color:#38bdf8;">'
        '<span style="width:6px;height:6px;border-radius:50%;background-color:#38bdf8;display:inline-block;"></span> Standalone Engine'
        '</div>'
    )

    st.markdown(
        f"""
        <div style="padding: 0.1rem 0 0.4rem 0.35rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.25rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <h2 style="color: white !important; margin: 0; font-size: 1.35rem; font-weight: 700; line-height: 1;">FinPath</h2>
                </div>
            </div>
            {status_pill}
        </div>
        """,
        unsafe_allow_html=True
    )

    nav_items = [
        ("Dashboard", ":material/dashboard:"),
        ("Decision Guide", ":material/explore:"),
        ("Journey Twin", ":material/sync_alt:"),
        ("Wealth & Debt Hub", ":material/calculate:"),
        ("Document AI", ":material/description:"),
        ("Financial Assistant", ":material/smart_toy:"),
        ("Document Checklist", ":material/checklist:"),
        ("Profile", ":material/account_circle:")
    ]

    for label, icon in nav_items:
        is_active = (st.session_state.page in [label, "Deposit Planner"] if label == "Wealth & Debt Hub" else st.session_state.page == label)
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            label,
            key=f"sb_nav_{label.replace(' ', '_').lower()}",
            icon=icon,
            type=btn_type,
            use_container_width=True
        ):
            if st.session_state.page != label:
                st.session_state.page = label
                st.rerun()

    # User Profile Card
    sidebar_profile = st.session_state.profile
    sb_name = sidebar_profile.get("name", "").strip()
    sb_display_name = sb_name if sb_name else "FinPath Member"

    if sb_name:
        parts = sb_name.split()
        if len(parts) >= 2:
            sb_initials = f"{parts[0][0]}{parts[1][0]}".upper()
        else:
            sb_initials = sb_name[:2].upper()
        sb_status = "Verified Member"
        sb_dot = "#22c55e"
    else:
        sb_initials = "FP"
        sb_status = "Basic Account"
        sb_dot = "#94a3b8"

    sb_income = float(sidebar_profile.get("monthly_income", 0.0))
    sb_saving = float(sidebar_profile.get("monthly_saving_capacity", 0.0))
    sb_sym = currency_symbol()

    sb_income_str = f"{sb_sym}{sb_income:,.0f}" if sb_income > 0 else f"{sb_sym}0"
    sb_saving_str = f"{sb_sym}{sb_saving:,.0f}" if sb_saving > 0 else f"{sb_sym}0"

    if sb_income > 0 and sb_saving > 0:
        sb_rate_val = int((sb_saving / sb_income) * 100)
        sb_rate_badge = f"<span class='card-green' style='font-weight:600;'>{sb_rate_val}% Saved</span>"
    else:
        sb_rate_badge = "<span class='card-muted'>Standard</span>"

    card_html = (
        f'<div class="sidebar-profile-card">'
        f'<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.45rem;">'
        f'<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#007FFF 0%,#1e40af 100%);color:#ffffff !important;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;border:2px solid rgba(255,255,255,0.25);box-shadow:0 2px 6px rgba(0,127,255,0.35);flex-shrink:0;">{sb_initials}</div>'
        f'<div style="min-width:0;flex-grow:1;">'
        f'<div class="card-white" style="font-weight:600;font-size:0.88rem;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{sb_display_name}</div>'
        f'<div style="display:flex;align-items:center;gap:0.3rem;margin-top:1px;">'
        f'<span style="width:6px;height:6px;border-radius:50%;background-color:{sb_dot};display:inline-block;"></span>'
        f'<span class="card-sub" style="font-size:0.72rem;font-weight:500;">{sb_status}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.35rem;margin-bottom:0.35rem;">'
        f'<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:0.3rem 0.45rem;">'
        f'<span class="card-muted" style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.4px;display:block;">Income</span>'
        f'<span class="card-white" style="font-weight:600;font-size:0.78rem;">{sb_income_str}</span>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:0.3rem 0.45rem;">'
        f'<span class="card-muted" style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.4px;display:block;">Savings</span>'
        f'<span class="card-blue" style="font-weight:600;font-size:0.78rem;">{sb_saving_str}</span>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;padding-top:0.3rem;border-top:1px solid rgba(255,255,255,0.08);font-size:0.68rem;">'
        f'<span class="card-muted">Currency: <b class="card-white">{st.session_state.currency} ({sb_sym})</b></span>'
        f'{sb_rate_badge}'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


# ============================================================
# EXECUTIVE REPORT GENERATOR HELPER
# ============================================================

def generate_executive_report_markdown():
    profile = st.session_state.get("profile", {})
    name = str(profile.get("name", "")).strip() or "Valued Client"
    income = safe_float(profile.get("monthly_income", 0.0))
    savings = safe_float(profile.get("monthly_saving_capacity", 0.0))
    curr = st.session_state.get("currency", "INR")
    sym = currency_symbol()

    loan_info = st.session_state.get("modeled_loan", {})
    loan_p = safe_float(loan_info.get("principal", 1000000.0))
    loan_r = safe_float(loan_info.get("rate", 8.75))
    loan_t = safe_float(loan_info.get("tenure_years", 10.0))
    loan_emi = safe_float(loan_info.get("emi", 12532.0))
    loan_tot_int = safe_float(loan_info.get("total_interest", 503840.0))

    sip_info = st.session_state.get("modeled_sip", {})
    sip_m = safe_float(sip_info.get("monthly_sip", min(savings, 10000.0) if savings > 0 else 5000.0))
    sip_r = safe_float(sip_info.get("expected_return", 12.5))
    sip_y = safe_float(sip_info.get("years", 15.0))
    sip_fv = safe_float(sip_info.get("future_value", 5020000.0))

    jt = st.session_state.get("journey_twin", {})
    action = jt.get("action", "General Financial Planning")

    if income > 0:
        savings_rate_str = f"{int((savings / income) * 100)}% savings rate"
        foir_val = (loan_emi / income) * 100
        foir_status = "Safe (<=40%)" if foir_val <= 40 else "High Risk (>40%)"
        foir_str = f"{foir_val:.1f}% ({foir_status})"
    else:
        savings_rate_str = "0% (Income not set)"
        foir_str = "N/A (Income not set)"

    activities = storage.get_activity_log()

    report = f"""# FinPath Executive Financial Health and Readiness Report
**Prepared For:** {name} | **Currency:** {curr} ({sym}) | **Status:** Active Assessment

---

## 1. Executive Cash Flow & Profile Snapshot
- **Monthly Net Income:** {sym}{income:,.2f}
- **Monthly Saving Capacity:** {sym}{savings:,.2f} ({savings_rate_str})
- **Active Goal Milestone:** {action}

---

## 2. Debt & Loan Amortization Profile
- **Modeled Principal Amount:** {sym}{loan_p:,.2f}
- **Annual Interest Rate:** {loan_r:.2f}% (Reducing Balance)
- **Loan Tenure:** {loan_t:.1f} Years ({int(loan_t*12)} Months)
- **Monthly EMI Obligation:** {sym}{loan_emi:,.2f}
- **Total Interest Payable:** {sym}{loan_tot_int:,.2f}
- **Debt-to-Income (FOIR):** {foir_str}

---

## 3. 50/30/20 Budget Blueprint & Safety Net
- **Essential Needs (50%):** {sym}{income * 0.50:,.2f}
- **Discretionary Wants (30%):** {sym}{income * 0.30:,.2f}
- **Target Savings (20%):** {sym}{income * 0.20:,.2f}
- **6-Month Emergency Fund Target:** {sym}{income * 0.50 * 6:,.2f}

---

## 4. Wealth Compounding & SIP Outlook
- **Monthly SIP Allocation:** {sym}{sip_m:,.2f}
- **Expected Return:** {sip_r:.1f}% p.a.
- **Tenure:** {sip_y:.0f} Years
- **Projected Future Corpus:** {sym}{sip_fv:,.2f}

---

## 5. Complete User Activity Audit Timeline
"""
    if activities:
        for act in reversed(activities):
            report += f"- **[{act.get('timestamp')}] {act.get('category')}:** {act.get('action')} *(Details: {act.get('details')})*\n"
    else:
        report += "- *No previous interaction logged.*\n"

    report += f"""
---

## 6. Strategic Financial Advisory Action Items
1. **Emergency Reserve:** Maintain at least 3 to 6 months of essential living expenses in high-liquidity deposits (min ₹1,000 FD, min ₹500 RD).
2. **Debt Optimization:** Keep total monthly debt repayments strictly below 40% of net monthly income and use 13th EMI prepayments to cut tenure.
3. **Risk Protection:** Secure comprehensive health insurance (0% co-pay, no room rent cap) and term life cover of 10-15x income.
4. **Wealth Creation:** Direct surplus monthly savings into direct-growth equity index SIPs with 10% annual step-up allocations.

*Generated securely by FinPath Financial Planning Engine.*
"""
    return report


# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():
    profile = st.session_state.profile
    name = str(profile.get("name", "")).strip()
    greeting = f"Welcome, {name}" if name else "Welcome to FinPath"

    st.markdown(
        f"""
        <div class="hero-box">
            <h1 style="margin-bottom:0.3rem;">{greeting}</h1>
            <p style="font-size:1.05rem;opacity:0.92;margin:0;">
                Your financial planning assistant: audit policies with Document AI, model loans and amortization, simulate investments, and build sustainable wealth.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Top Executive KPI Summary Row (Clean 3-column layout without Document Readiness)
    income = safe_float(profile.get("monthly_income", 0.0))
    savings = safe_float(profile.get("monthly_saving_capacity", 0.0))
    sym = currency_symbol()

    kpi1, kpi2, kpi3 = st.columns([1, 1, 1])
    with kpi1:
        st.metric("Monthly Income", f"{sym}{income:,.0f}" if income > 0 else f"{sym}0", "Profile baseline")
    with kpi2:
        saving_pct = int((savings / income) * 100) if income > 0 else 0
        st.metric("Monthly Savings", f"{sym}{savings:,.0f}" if savings > 0 else f"{sym}0", f"{saving_pct}% savings rate")
    with kpi3:
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        try:
            report_pdf = generate_health_report_pdf(
                profile_data=profile,
                loan_data=st.session_state.get("modeled_loan", {}),
                sip_data=st.session_state.get("modeled_sip", {}),
                currency=st.session_state.currency
            )
        except Exception as e:
            print(f"[FinPath] Health PDF error: {e}")
            report_pdf = b"%PDF-1.4 Health Report"

        st.download_button(
            "Export Health Report (PDF)",
            data=report_pdf,
            file_name=f"FinPath_Health_Report_{name or 'Client'}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            help="Download comprehensive PDF report with your profile, monthly income, saving, loan/debt obligations, and 50/30/20 budget runway."
        )

    st.markdown("---")
    st.subheader("Financial Operations Hub")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            '<div class="feature-box">'
            '<h3>Wealth and Debt Hub</h3>'
            '<p>Interactive Loan Amortization, Prepayment Slasher, SIP Wealth Modeling, and Complete Terms Guide.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("Open Wealth and Debt Hub", key="dash_btn_wealth", use_container_width=True):
            st.session_state.page = "Wealth & Debt Hub"
            st.rerun()

    with col2:
        st.markdown(
            '<div class="feature-box">'
            '<h3>Document AI</h3>'
            '<p>Audit insurance policies, loan sanction letters, extract financial figures, and detect hidden clauses.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("Launch Document AI", key="dash_btn_docai", use_container_width=True):
            st.session_state.page = "Document AI"
            st.rerun()

    with col3:
        st.markdown(
            '<div class="feature-box">'
            '<h3>Journey Twin</h3>'
            '<p>Select financial actions, verify required documents with live gauges, and auto-sync uploaded documents.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("Check Journey Readiness", key="dash_btn_journey", use_container_width=True):
            st.session_state.page = "Journey Twin"
            st.rerun()

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown(
            '<div class="feature-box">'
            '<h3>Financial Assistant</h3>'
            '<p>Ask questions about loans, insurance, deposits, SIPs, and any major financial journey.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("Chat with Assistant", key="dash_btn_assistant", use_container_width=True):
            st.session_state.page = "Financial Assistant"
            st.rerun()

    with col5:
        st.markdown(
            '<div class="feature-box">'
            '<h3>Decision Guide</h3>'
            '<p>Understand structured steps, mandatory documents, payments, and key questions for financial actions.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("Open Decision Guide", key="dash_btn_decision", use_container_width=True):
            st.session_state.page = "Decision Guide"
            st.rerun()

    with col6:
        st.markdown(
            '<div class="feature-box">'
            '<h3>Profile and Settings</h3>'
            '<p>Manage income, saving capacity, currency preference, and generate complete financial reports.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("Manage Profile", key="dash_btn_profile", use_container_width=True):
            st.session_state.page = "Profile"
            st.rerun()

    st.markdown("---")
    st.subheader("How FinPath works")

    st.markdown(
        """
        <div class="blue-note">
            <h3>Plan → Check → Prepare → Act</h3>
            <ol>
                <li>Select the financial action or journey you want to take.</li>
                <li>Understand the process and common regulatory requirements.</li>
                <li>Use Journey Twin and Document AI to audit contracts and check paperwork.</li>
                <li>Model loans, prepayments, and SIP wealth accumulation with exact math.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DECISION GUIDE PAGE
# ============================================================

def decision_guide_page():
    st.title("Decision Guide")

    st.write(
        "Choose a financial action to understand its purpose, common steps, "
        "documents, payments, and questions to ask."
    )

    decisions = {
        "Open a Bank Deposit": {
            "purpose": "Save a lump sum or make regular deposits for a defined period.",
            "steps": [
                "Compare available deposit products.",
                "Check interest rates and tenure options.",
                "Review premature withdrawal rules.",
                "Complete the application and KYC process.",
                "Confirm nomination and maturity instructions."
            ],
            "documents": [
                "Identity proof",
                "Address proof",
                "Tax identification",
                "Photograph",
                "Bank account details",
                "Nominee details"
            ],
            "payments": [
                "Initial deposit amount",
                "Applicable account or service charges",
                "Tax deductions, if applicable"
            ],
            "questions": [
                "What is the interest rate?",
                "What happens if I withdraw early?",
                "Is nomination available?",
                "How will maturity proceeds be paid?"
            ]
        },
        "Apply for a Loan": {
            "purpose": "Borrow money for a defined need and repay it over time.",
            "steps": [
                "Define the borrowing purpose.",
                "Estimate an affordable EMI.",
                "Compare lenders and loan terms.",
                "Submit documents and application.",
                "Review the sanction letter and agreement.",
                "Track repayment dates and charges."
            ],
            "documents": [
                "Identity proof",
                "Address proof",
                "Income proof",
                "Bank statements",
                "Employment or business proof",
                "Tax returns, where applicable",
                "Collateral documents, where applicable"
            ],
            "payments": [
                "Processing fee",
                "Down payment, where applicable",
                "Monthly EMI",
                "Insurance or additional charges, if applicable"
            ],
            "questions": [
                "What is the total repayment amount?",
                "Is the rate fixed or floating?",
                "Are there prepayment charges?",
                "What happens if an EMI is missed?"
            ]
        },
        "Buy Health Insurance": {
            "purpose": "Obtain financial protection against eligible healthcare expenses.",
            "steps": [
                "Assess your coverage needs.",
                "Compare policy benefits and exclusions.",
                "Review waiting periods and co-payment.",
                "Submit the proposal and required information.",
                "Read the policy document carefully.",
                "Save policy and claim contact details."
            ],
            "documents": [
                "Identity proof",
                "Address proof",
                "Age proof",
                "Medical history",
                "Medical reports, if requested",
                "Existing policy details",
                "Nominee details"
            ],
            "payments": [
                "Premium",
                "Applicable taxes",
                "Optional add-on charges"
            ],
            "questions": [
                "What are the waiting periods?",
                "Which hospitals are in the network?",
                "What exclusions apply?",
                "Is there a co-payment?",
                "How are claims submitted?"
            ]
        },
        "Start a Regular Contribution": {
            "purpose": "Build savings or investments through a repeated contribution plan.",
            "steps": [
                "Define the financial goal.",
                "Select a contribution amount.",
                "Choose a suitable product or account.",
                "Review fees, risks, and withdrawal rules.",
                "Complete registration.",
                "Set up a payment schedule."
            ],
            "documents": [
                "Identity proof",
                "Address proof",
                "Tax identification",
                "Bank account details",
                "Nominee details",
                "Risk profile information, where applicable"
            ],
            "payments": [
                "Regular contribution",
                "Account or platform fees, if applicable",
                "Tax-related payments, where applicable"
            ],
            "questions": [
                "Can I change the contribution amount?",
                "What happens if I miss a payment?",
                "Are withdrawals allowed?",
                "What fees apply?",
                "What risks should I understand?"
            ]
        },
        "Make a Major Purchase": {
            "purpose": "Plan and complete a large purchase while managing payment obligations.",
            "steps": [
                "Define the purchase budget.",
                "Compare sellers or providers.",
                "Request a detailed quotation.",
                "Review warranty, refund, and cancellation terms.",
                "Verify payment and agreement details.",
                "Store invoices and receipts."
            ],
            "documents": [
                "Identity proof",
                "Address proof",
                "Income proof, if financing is used",
                "Quotation or invoice",
                "Purchase agreement",
                "Payment receipt",
                "Registration documents, where applicable"
            ],
            "payments": [
                "Booking amount",
                "Down payment",
                "Scheduled instalments",
                "Taxes and registration charges, where applicable"
            ],
            "questions": [
                "What is the complete cost?",
                "Are there additional charges?",
                "What is the cancellation policy?",
                "When will I receive the invoice?",
                "What documents prove ownership or purchase?"
            ]
        }
    }

    selected_decision = st.selectbox(
        "Choose a financial action",
        list(decisions.keys())
    )

    data = decisions[selected_decision]

    st.markdown("---")
    st.subheader(selected_decision)

    st.markdown(
        f"""
        <div class="blue-note">
            <strong>Purpose:</strong> {data["purpose"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Common Steps")
        for step in data["steps"]:
            st.markdown(f"- {step}")

        st.markdown("### Common Documents")
        for document in data["documents"]:
            st.markdown(f"- {document}")

    with col2:
        st.markdown("### Possible Payments")
        for payment in data["payments"]:
            st.markdown(f"- {payment}")

        st.markdown("### Questions to Ask")
        for question in data["questions"]:
            st.markdown(f"- {question}")


# ============================================================
# SMART DOCUMENT AI PAGE
# ============================================================

def document_ai_page():
    st.title("Smart Document AI & Policy Auditor")
    st.write(
        "Upload any financial document (health policy, loan sanction letter, payslip, FD certificate) "
        "to automatically extract financial figures, audit hidden clauses / red flags, and sync with your Journey Twin checklist."
    )

    st.markdown(
        """
        <div class="blue-note">
            <p>
                <b>How it works:</b> FinPath extracts financial amounts, dates, interest rates, and loan/policy IDs, while actively auditing for restrictive clauses like room-rent caps, co-payments, and prepayment penalties.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_upload, tab_samples = st.tabs(["Upload PDF or Document", "Instant Sample Presets"])

    doc_source = None
    source_name = ""

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload Policy or Agreement PDF / TXT",
            type=["pdf", "txt"],
            help="Upload your health insurance policy, sanction letter, or financial statement (Max 15MB)."
        )
        if uploaded_file is not None:
            doc_source = uploaded_file.read()
            source_name = uploaded_file.name

    with tab_samples:
        st.write("Don't have a document handy? Select an interactive sample to test the auditor:")
        sample_choice = st.selectbox(
            "Select a realistic financial sample:",
            [
                "None",
                "Health Insurance Policy (With 1% Room Rent Cap & 10% Co-Pay)",
                "Home Loan Sanction Letter (4,500,000 at 8.75% for 240 Months with Prepayment Clause)",
                "Monthly Salary Slip (Gross 85,000, PF, Tax Deductions & Net Pay)"
            ]
        )

        if sample_choice == "Health Insurance Policy (With 1% Room Rent Cap & 10% Co-Pay)":
            doc_source = """
            HEALTH INSURANCE POLICY SCHEDULE
            Insurer: Star Care Health Insurance Ltd.
            Policy Number: POL-994821034
            Policyholder: FinPath Member
            Period of Insurance: 01/04/2026 to 31/03/2027
            Sum Insured: ₹500,000 (INR Five Lakhs)
            Annual Premium Paid: ₹14,500
            
            IMPORTANT TERMS AND RESTRICTIVE CONDITIONS:
            1. Room Rent Sub-Limit: Daily hospital room rent is capped at 1% of Sum Insured (₹5,000/day). ICU room rent is capped at 2% of Sum Insured. Exceeding this limit will trigger proportionate deductions across all surgeon fees, doctor visits, and procedure bills.
            2. Co-Payment: A mandatory 10% Co-Payment applies on every admissible claim for hospitals located in Zone B and for members aged above 60.
            3. Pre-Existing Disease (PED) Waiting Period: A waiting period of 36 months applies for pre-existing medical conditions and specific treatments (cataract, hernia, joint replacement).
            4. Permanent Exclusions: Cosmetic procedures, dietary supplements, and non-medical items are excluded from claim settlement.
            5. Cashless Hospitalization available across 8,500 network hospitals upon 48-hour prior authorization.
            """
            source_name = "Sample_Health_Policy.txt"

        elif sample_choice == "Home Loan Sanction Letter (4,500,000 at 8.75% for 240 Months with Prepayment Clause)":
            doc_source = """
            CREDIT SANCTION LETTER - HOME LOAN
            Lender: Apex Housing Finance Corporation
            Sanction Reference Number: LAN-2026-883192
            Applicant Name: FinPath Member
            Sanction Date: 15/02/2026
            
            SANCTION TERMS & FINANCIAL BREAKDOWN:
            Sanctioned Loan Principal: ₹4,500,000 (INR Forty-Five Lakhs)
            Rate of Interest: 8.75% p.a. (Floating Rate linked to Repo)
            Loan Tenure: 240 Months (20 Years)
            Equated Monthly Installment (EMI): ₹39,781.00
            Processing Fee: 0.5% of Loan Amount (₹22,500 + GST)
            
            SPECIAL CONDITIONS & PENAL PROVISIONS:
            1. Prepayment Charge: Zero prepayment penalty on individual floating-rate home loans. Commercial borrowers will incur 2% foreclosure penalty.
            2. Penal Interest: In the event of default or delayed EMI, default penal interest of 24% p.a. will be levied on overdue payments, alongside NACH bounce charges of ₹500 per bounce.
            3. Security / Collateral: Equitable mortgage of Residential Flat No. 402, Green Acres.
            4. Disbursement: Subject to verification of 3-year Income Tax Returns and clear legal title search report.
            """
            source_name = "Sample_Home_Loan_Sanction.txt"

        elif sample_choice == "Monthly Salary Slip (Gross 85,000, PF, Tax Deductions & Net Pay)":
            doc_source = """
            MONTHLY PAYSLIP - SALARY CERTIFICATE
            Employer: Global Tech Solutions India Pvt Ltd
            Employee ID: EMP-774102
            Employee Name: FinPath Member
            Month / Year: February 2026 | Pay Date: 28/02/2026
            PAN Number: ABCDE1234F | Bank Account: HDFC0001234
            
            EARNINGS:
            Basic Pay: ₹42,500.00
            House Rent Allowance (HRA): ₹21,250.00
            Special Allowance: ₹15,250.00
            Medical & Travel Allowance: ₹6,000.00
            Gross Earnings: ₹85,000.00
            
            DEDUCTIONS:
            Provident Fund (PF): ₹5,100.00
            Professional Tax: ₹200.00
            Income Tax (TDS): ₹6,200.00
            Total Deductions: ₹11,500.00
            
            NET SALARY TRANSFERRED: ₹73,500.00 (INR Seventy-Three Thousand Five Hundred)
            """
            source_name = "Sample_Payslip.txt"

    if not doc_source:
        st.info("Please upload a PDF/text document or select a sample preset above to begin analysis.")
        return

    st.markdown("---")
    st.subheader(f"Analysis Results: {source_name}")

    with st.spinner("Analyzing document structure, extracting financial entities, and auditing clauses..."):
        if documentai is not None:
            analysis = documentai.analyze_document(doc_source)
        else:
            analysis = {
                "success": True,
                "document_type": "General Financial Document",
                "recommended_journey": "Apply for a Loan",
                "summary": "Document processed in basic mode.",
                "entities": {},
                "red_flags": [],
                "matched_checklist_items": ["Identity proof", "Address proof"],
                "characters": len(str(doc_source)),
                "lines": len(str(doc_source).splitlines()),
                "raw_text_snippet": str(doc_source)[:500]
            }

    doc_type = analysis.get("document_type", "Financial Document")
    rec_journey = analysis.get("recommended_journey", "Select an action")
    entities = analysis.get("entities", {})
    flags = analysis.get("red_flags", [])
    matched_docs = analysis.get("matched_checklist_items", [])

    # Classification & Action Banner
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, #1e3a8a, #1d4ed8);border-radius:12px;padding:1.2rem;color:white;margin-bottom:1.2rem;">
            <div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.5px;opacity:0.85;">Document Classification</div>
            <h2 style="color:white !important;margin:0.2rem 0 0.5rem 0;font-size:1.4rem;">{doc_type}</h2>
            <div style="font-size:0.9rem;opacity:0.95;">
                <b>Recommended Journey Match:</b> {rec_journey}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Extracted Financial Entities Grid
    st.markdown("### Extracted Financial Entities and Key Metrics")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    amounts = entities.get("amounts", [])
    rates = entities.get("interest_rates", [])
    dates = entities.get("dates", [])
    tenures = entities.get("tenures", [])
    refs = entities.get("policy_loan_numbers", [])

    with m_col1:
        st.metric(
            "Primary Amount",
            amounts[0] if amounts else "N/A",
            "Identified figure"
        )
    with m_col2:
        st.metric(
            "Rate / Percentage",
            rates[0] if rates else "N/A",
            "Identified rate"
        )
    with m_col3:
        st.metric(
            "Tenure / Duration",
            tenures[0] if tenures else "N/A",
            "Term duration"
        )
    with m_col4:
        st.metric(
            "Reference / ID",
            refs[0] if refs else (dates[0] if dates else "N/A"),
            "Policy/Account ID"
        )

    # Additional Entities Expandable
    with st.expander("View All Detected Entities and Values", expanded=False):
        e_c1, e_c2 = st.columns(2)
        with e_c1:
            st.markdown("**All Identified Amounts:**")
            if amounts:
                for a in amounts:
                    st.markdown(f"- {currency_symbol()}{a}")
            else:
                st.write("None found")
            st.markdown("**All Stated Rates:**")
            st.write(", ".join(rates) if rates else "None found")
        with e_c2:
            st.markdown("**Identified Dates:**")
            st.write(", ".join(dates) if dates else "None found")
            st.markdown("**Reference Numbers:**")
            st.write(", ".join(refs) if refs else "None found")

    # Policy Auditor & Red Flag Warnings
    st.markdown("### Critical Clause and Red Flag Audit")
    if flags:
        st.warning(f"Auditor flagged {len(flags)} critical clauses or restrictive conditions that require your attention.")
        for f in flags:
            f_cat = f.get("category", "Clause")
            f_title = f.get("title", "Notice")
            f_detail = f.get("detail", "")
            f_type = f.get("type", "warning")

            if f_type == "danger":
                box_style = "background-color:#fef2f2;border-left:5px solid #ef4444;border-radius:8px;padding:0.9rem;margin-bottom:0.75rem;"
                title_color = "#991b1b"
            elif f_type == "warning":
                box_style = "background-color:#fffbeb;border-left:5px solid #f59e0b;border-radius:8px;padding:0.9rem;margin-bottom:0.75rem;"
                title_color = "#92400e"
            else:
                box_style = "background-color:#eff6ff;border-left:5px solid #3b82f6;border-radius:8px;padding:0.9rem;margin-bottom:0.75rem;"
                title_color = "#1e40af"

            st.markdown(
                f"""
                <div style="{box_style}">
                    <div style="font-weight:700;color:{title_color};font-size:1rem;margin-bottom:0.25rem;">
                        {f_title} <span style="font-size:0.75rem;opacity:0.8;font-weight:500;">({f_cat})</span>
                    </div>
                    <p style="color:#1e293b !important;margin:0;font-size:0.9rem;line-height:1.4;">{f_detail}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.success("Clean Audit: No restrictive room-rent caps, excessive co-payments, or penalty clauses detected.")

    # Executive Summary & Extracted Text
    st.markdown("### Executive Summary")
    st.markdown(
        f"""
        <div class="blue-note">
            {analysis.get('summary', '').replace(chr(10), '<br/>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Journey Twin Auto-Sync Button
    if matched_docs and rec_journey != "Select an action":
        st.markdown("---")
        st.markdown("### Journey Twin Auto-Verification")
        st.write(
            f"Based on this document, the following items can be automatically verified in your **Journey Twin ({rec_journey})**:"
        )
        for d in matched_docs:
            st.markdown(f"- **{d}**")

        if st.button(f"Auto-Check Matched Documents in Journey Twin ({rec_journey})", type="primary", use_container_width=True):
            saved_jt = st.session_state.get("journey_twin", {})
            saved_jt["action"] = rec_journey
            saved_docs = saved_jt.get("documents", {})

            for d in matched_docs:
                storage_key = f"{rec_journey}_{d}"
                saved_docs[storage_key] = True

            saved_jt["documents"] = saved_docs
            st.session_state.journey_twin = saved_jt
            storage.set_stored_item("journey_twin", saved_jt)
            storage.sync_to_browser_local_storage("finpath_journey_twin", saved_jt)
            st.success(f"Successfully synchronized {len(matched_docs)} verified document(s) into Journey Twin.")
            st.rerun()


# ============================================================
# JOURNEY TWIN PAGE (ENHANCED WITH GAUGE & AUTO-MATCH)
# ============================================================

def journey_twin_page():
    st.title("Journey Twin")

    st.write(
        "Journey Twin acts as your personal digital checklist and readiness tracker "
        "for major financial decisions."
    )

    action_options = [
        "Select an action",
        "Open a Bank Deposit",
        "Apply for a Loan",
        "Buy Health Insurance",
        "Start a Regular Contribution",
        "Make a Major Purchase"
    ]

    saved_jt = st.session_state.get("journey_twin", {})
    saved_action = saved_jt.get("action", "Select an action")
    default_action_idx = action_options.index(saved_action) if saved_action in action_options else 0

    col_act1, col_act2 = st.columns([3, 1])
    with col_act1:
        action = st.selectbox(
            "What financial goal are you preparing for?",
            action_options,
            index=default_action_idx,
            key="journey_twin_action"
        )

    if action != saved_action:
        saved_jt["action"] = action
        st.session_state.journey_twin = saved_jt
        storage.set_stored_item("journey_twin", saved_jt)
        storage.sync_to_browser_local_storage("finpath_journey_twin", saved_jt)

    document_requirements = {
        "Open a Bank Deposit": [
            "Identity proof",
            "Address proof",
            "PAN or applicable tax identification",
            "Recent photograph",
            "Bank account details",
            "Nominee details",
            "Completed KYC form"
        ],
        "Apply for a Loan": [
            "Identity proof",
            "Address proof",
            "PAN or applicable tax identification",
            "Recent salary slips or income proof",
            "Recent bank statements",
            "Employment or business proof",
            "Income tax returns, where applicable",
            "Existing loan statements",
            "Property or collateral documents, where applicable",
            "Loan-purpose quotation or invoice, where applicable"
        ],
        "Buy Health Insurance": [
            "Identity proof",
            "Address proof",
            "Age proof",
            "Recent photograph",
            "Medical history, if requested",
            "Medical reports, if requested",
            "Existing insurance policy documents",
            "Previous claim details, if applicable",
            "Nominee details",
            "Completed proposal form"
        ],
        "Start a Regular Contribution": [
            "Identity proof",
            "Address proof",
            "PAN or applicable tax identification",
            "Bank account details",
            "Nominee details",
            "Risk profile information, where applicable",
            "Completed application or registration form"
        ],
        "Make a Major Purchase": [
            "Identity proof",
            "Address proof",
            "Income proof, if financing is used",
            "Bank statements, if financing is used",
            "Quotation or invoice",
            "Purchase agreement",
            "Payment receipt or booking receipt",
            "Registration documents, where applicable",
            "Loan or financing documents, if applicable"
        ]
    }

    if action == "Select an action":
        st.info("Select a financial action above to load your document checklist.")
        return

    required_documents = document_requirements[action]
    saved_docs = saved_jt.get("documents", {})
    document_status = {}

    st.markdown("---")
    st.subheader(f"Readiness Checklist: {action}")

    # Checklist checkboxes
    chk_cols = st.columns(2)
    for index, document in enumerate(required_documents):
        doc_storage_key = f"{action}_{document}"
        initial_val = saved_docs.get(doc_storage_key, False)
        widget_key = f"journey_doc_{action}_{index}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = initial_val

        with chk_cols[index % 2]:
            checked = st.checkbox(
                f"{document}",
                value=initial_val,
                key=widget_key
            )

        if checked != initial_val:
            saved_docs[doc_storage_key] = checked
            saved_jt["documents"] = saved_docs
            saved_jt["action"] = action
            st.session_state.journey_twin = saved_jt
            storage.set_stored_item("journey_twin", saved_jt)
            storage.sync_to_browser_local_storage("finpath_journey_twin", saved_jt)

        document_status[document] = checked

    available_documents = [doc for doc, is_avail in document_status.items() if is_avail]
    missing_documents = [doc for doc, is_avail in document_status.items() if not is_avail]
    total_documents = len(required_documents)
    available_count = len(available_documents)
    missing_count = len(missing_documents)
    completion_percentage = (available_count / total_documents * 100) if total_documents > 0 else 0

    st.markdown("---")
    st.subheader("Your Document Readiness Gauge")

    g_col1, g_col2 = st.columns([1, 1])

    with g_col1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=completion_percentage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Document Preparedness ({available_count}/{total_documents})", 'font': {'size': 18, 'color': '#ffffff'}},
            number={'suffix': "%", 'font': {'color': '#ffffff', 'size': 36}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
                'bar': {'color': "#007FFF"},
                'bgcolor': "#1e293b",
                'borderwidth': 2,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 40], 'color': '#ef4444'},
                    {'range': [40, 80], 'color': '#f59e0b'},
                    {'range': [80, 100], 'color': '#22c55e'}
                ]
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=260,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with g_col2:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        if missing_count == 0:
            st.success("100% Prepared: You have marked all standard required documents as ready.")
        elif completion_percentage >= 60:
            st.warning(f"Almost There: You have {available_count} of {total_documents} documents. {missing_count} item(s) remain.")
        else:
            st.error(f"Action Needed: You have collected {available_count} of {total_documents} required documents.")

        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:0.9rem;">
                <div style="font-size:0.85rem;color:#94a3b8;"><b>Pro-Tip:</b></div>
                <div style="font-size:0.85rem;color:#f8fafc;margin-top:0.2rem;">
                    Upload your loan agreement or insurance policy in <b>Document AI</b> to audit for red flags and auto-verify documents here with 1 click.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Missing vs Available Breakdowns
    col_av, col_mis = st.columns(2)
    with col_av:
        st.markdown(
            """
            <div class="available-box">
                <h3 style="color:#4ade80 !important;margin-top:0;">Ready and Verified Documents</h3>
            """,
            unsafe_allow_html=True
        )
        if available_documents:
            for doc in available_documents:
                st.markdown(f"- {doc}")
        else:
            st.write("No documents marked as ready yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_mis:
        st.markdown(
            """
            <div class="missing-box">
                <h3 style="color:#f87171 !important;margin-top:0;">Pending / Actionable Documents</h3>
            """,
            unsafe_allow_html=True
        )
        if missing_documents:
            for doc in missing_documents:
                st.markdown(f"- {doc}")
        else:
            st.write("No missing documents! All items checked.")
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# WEALTH & DEBT HUB (COMPREHENSIVE MULTI-TOOL ENGINE)
# ============================================================

def wealth_debt_hub_page():
    st.title("Wealth and Debt Hub")
    st.write(
        "Interactive mathematical models for loans, prepayment acceleration, systematic investments (SIP), "
        "fixed deposits, and an exhaustive guide on financial terms, conditions, and repayment strategies."
    )

    tabs = st.tabs([
        "Loan EMI and Amortization",
        "Loan Prepayment and Repayment Strategies",
        "Systematic Investment Plan (SIP)",
        "Fixed and Recurring Deposits",
        "Financial Terms, Conditions and Repayment Guide"
    ])

    sym = currency_symbol()

    # --------------------------------------------------------
    # TAB 1: LOAN EMI & AMORTIZATION
    # --------------------------------------------------------
    with tabs[0]:
        st.subheader("Loan EMI and Amortization Schedule")
        st.write("Customize your loan principal, interest rate, and tenure freely to inspect monthly EMI and amortization curve.")

        col_l1, col_l2, col_l3 = st.columns(3)

        with col_l1:
            principal = st.number_input(
                "Principal Loan Amount",
                min_value=0.0,
                value=1000000.0,
                step=10000.0,
                key="loan_p_in",
                help="Enter any loan principal amount you wish to borrow or model."
            )
        with col_l2:
            rate = st.number_input(
                "Annual Interest Rate (%)",
                min_value=0.0,
                max_value=50.0,
                value=8.75,
                step=0.25,
                key="loan_r_in",
                help="Annual nominal interest rate offered by the lender."
            )
        with col_l3:
            tenure_years = st.number_input(
                "Tenure (Years)",
                min_value=0.1,
                max_value=40.0,
                value=10.0,
                step=0.5,
                key="loan_t_in",
                help="Duration of the loan in years."
            )

        months = int(tenure_years * 12)
        amort = calculate_loan_amortization(principal, rate, months) if (calculate_loan_amortization and principal > 0) else {}

        emi = amort.get("base_emi", 0.0)
        tot_interest = amort.get("total_interest", 0.0)
        tot_payment = amort.get("total_payment", 0.0)

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Monthly EMI", f"{sym}{emi:,.2f}")
        with m2:
            st.metric("Principal Borrowed", f"{sym}{principal:,.0f}")
        with m3:
            ratio_str = f"{(tot_interest/principal)*100:.1f}% of loan" if principal > 0 else "0%"
            st.metric("Total Interest Paid", f"{sym}{tot_interest:,.2f}", ratio_str)
        with m4:
            st.metric("Total Amount Repaid", f"{sym}{tot_payment:,.2f}")

        # Plotly Stacked Bar Chart for Amortization Schedule
        schedule = amort.get("schedule", [])
        if schedule:
            df_sched = pd.DataFrame(schedule)
            if months > 24:
                df_sched["Year"] = ((df_sched["month"] - 1) // 12) + 1
                df_yearly = df_sched.groupby("Year").agg({
                    "principal_paid": "sum",
                    "interest_paid": "sum",
                    "remaining_balance": "last"
                }).reset_index()

                fig_amort = go.Figure()
                fig_amort.add_trace(go.Bar(x=df_yearly["Year"], y=df_yearly["principal_paid"], name="Principal Paid", marker_color="#007FFF"))
                fig_amort.add_trace(go.Bar(x=df_yearly["Year"], y=df_yearly["interest_paid"], name="Interest Paid", marker_color="#f59e0b"))
                fig_amort.update_layout(
                    barmode='stack',
                    title="Year-by-Year Principal vs. Interest Repayment",
                    xaxis_title="Year",
                    yaxis_title=f"Amount ({sym})",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(font=dict(color='#ffffff')),
                    font=dict(color='#ffffff')
                )
                st.plotly_chart(fig_amort, use_container_width=True)

            with st.expander("View Full Month-by-Month Amortization Table"):
                st.dataframe(df_sched, use_container_width=True)

    # --------------------------------------------------------
    # TAB 2: PREPAYMENT SIMULATOR & STRATEGIES
    # --------------------------------------------------------
    with tabs[1]:
        st.subheader("Loan Prepayment and Repayment Strategies")
        st.write(
            "Simulate how extra monthly or annual lump-sum prepayments shorten your loan tenure, "
            "eliminate compound interest, and save hundreds of thousands in borrowing costs."
        )

        col_prep_l, col_prep_r = st.columns(2)
        with col_prep_l:
            p_loan = st.number_input("Loan Amount (Principal)", min_value=0.0, value=2500000.0, step=50000.0, key="prep_p")
            p_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=50.0, value=9.0, step=0.25, key="prep_r")
            p_years = st.number_input("Original Tenure (Years)", min_value=0.5, max_value=40.0, value=20.0, step=1.0, key="prep_y")
        with col_prep_r:
            extra_mo = st.number_input(
                "Extra Monthly Prepayment",
                min_value=0.0,
                value=2500.0,
                step=500.0,
                key="prep_extra_mo",
                help="Amount added to your normal EMI payment every single month."
            )
            extra_yr = st.number_input(
                "Extra Annual Lump Sum Prepayment",
                min_value=0.0,
                value=25000.0,
                step=5000.0,
                key="prep_extra_yr",
                help="One-time prepayment made once every year (e.g. from annual bonus or tax refund)."
            )

        p_months = int(p_years * 12)
        prep_res = calculate_loan_amortization(p_loan, p_rate, p_months, extra_monthly=extra_mo, extra_yearly=extra_yr) if (calculate_loan_amortization and p_loan > 0) else {}

        int_saved = prep_res.get("interest_saved", 0.0)
        mo_saved = prep_res.get("months_saved", 0)
        yrs_saved = round(mo_saved / 12, 1)

        st.markdown("---")
        ps1, ps2, ps3 = st.columns(3)
        with ps1:
            st.metric("Total Interest Saved", f"{sym}{int_saved:,.2f}", "Cash saved directly")
        with ps2:
            st.metric("Tenure Reduced", f"{yrs_saved} Years ({mo_saved} Months)", "Debt freedom achieved early")
        with ps3:
            st.metric("Prepaid Total Repayment", f"{sym}{prep_res.get('prepaid_total_payment', 0):,.2f}")

        # Comparison Chart
        df_comp = pd.DataFrame({
            "Scenario": ["Standard Loan", "With Prepayments"],
            "Interest Paid": [prep_res.get("total_interest", 0), prep_res.get("prepaid_total_interest", 0)],
            "Principal": [p_loan, p_loan]
        })
        fig_comp = px.bar(
            df_comp,
            x="Scenario",
            y=["Principal", "Interest Paid"],
            title="Total Cost of Loan: Standard vs. Prepayment Strategy",
            barmode="stack",
            color_discrete_sequence=["#007FFF", "#ef4444"]
        )
        fig_comp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### Practical Loan Repayment Playbook")
        st.markdown(
            f"""
            <div class="blue-note">
                <ol>
                    <li><b>The 13th EMI Rule:</b> Paying just one extra EMI per calendar year cuts a 20-year home loan by 4 to 5 full years.</li>
                    <li><b>The 5% Annual Step-Up Strategy:</b> Increasing your EMI payment by 5% each year as your salary increases can shave nearly 7 years off a 20-year tenure.</li>
                    <li><b>Direct Principal Offset:</b> Whenever receiving bonuses, incentives, or dividends, deposit them directly toward the principal balance. Make sure the lender applies the amount to the outstanding principal rather than advancing future EMI dates.</li>
                    <li><b>Debt Avalanche Method:</b> If you have multiple loans, direct all excess cash to the loan with the highest interest rate first (e.g. credit cards or personal loans), while paying minimums on the rest.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # TAB 3: SYSTEMATIC INVESTMENT PLAN (SIP)
    # --------------------------------------------------------
    with tabs[2]:
        st.subheader("Systematic Investment Plan (SIP) and Compounding")
        st.write("Decide your monthly SIP investment freely and model long-term compounding with optional annual step-ups.")

        sip_c1, sip_c2, sip_c3, sip_c4 = st.columns(4)
        with sip_c1:
            sip_amt = st.number_input(
                "Monthly SIP Investment",
                min_value=0.0,
                value=10000.0,
                step=500.0,
                key="sip_amt_in",
                help="Amount you invest each month."
            )
        with sip_c2:
            sip_exp_r = st.number_input(
                "Expected Return (% p.a.)",
                min_value=0.0,
                max_value=40.0,
                value=12.5,
                step=0.5,
                key="sip_r_in",
                help="Estimated annualized return rate (e.g. 12% to 14% for diversified equity)."
            )
        with sip_c3:
            sip_yrs = st.number_input(
                "Investment Horizon (Years)",
                min_value=0.5,
                max_value=40.0,
                value=15.0,
                step=1.0,
                key="sip_y_in",
                help="Total years you plan to stay invested."
            )
        with sip_c4:
            sip_step = st.number_input(
                "Annual Step-Up (% hike)",
                min_value=0.0,
                max_value=50.0,
                value=10.0,
                step=1.0,
                key="sip_step_in",
                help="Annual percentage increase in monthly SIP allocation."
            )

        sip_res = calculate_sip_wealth(sip_amt, sip_exp_r, sip_yrs, step_up_percent=sip_step) if (calculate_sip_wealth and sip_amt > 0) else {}

        tot_inv = sip_res.get("total_invested", 0.0)
        tot_ret = sip_res.get("total_returns", 0.0)
        tot_fv = sip_res.get("future_value", 0.0)

        st.markdown("---")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Total Invested", f"{sym}{tot_inv:,.2f}")
        with s2:
            gain_pct = f"{(tot_ret/tot_inv)*100:.1f}% gain" if tot_inv > 0 else "0%"
            st.metric("Wealth Gain (Returns)", f"{sym}{tot_ret:,.2f}", gain_pct)
        with s3:
            st.metric("Projected Future Corpus", f"{sym}{tot_fv:,.2f}")
        with s4:
            mult = f"{tot_fv/tot_inv:.2f}x" if tot_inv > 0 else "1.00x"
            st.metric("Wealth Multiplier", mult, "Capital multiplication factor")

        # SIP Growth Trajectory Chart
        breakdown = sip_res.get("yearly_breakdown", [])
        if breakdown:
            df_sip = pd.DataFrame(breakdown)
            fig_sip = go.Figure()
            fig_sip.add_trace(go.Scatter(x=df_sip["year"], y=df_sip["wealth"], mode='lines+markers', name="Total Wealth", line=dict(color='#10b981', width=3), fill='tozeroy'))
            fig_sip.add_trace(go.Scatter(x=df_sip["year"], y=df_sip["invested"], mode='lines+markers', name="Invested Capital", line=dict(color='#007FFF', width=2, dash='dash')))
            fig_sip.update_layout(
                title="SIP Wealth Trajectory Over Time",
                xaxis_title="Years Elapsed",
                yaxis_title=f"Portfolio Value ({sym})",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ffffff')
            )
            st.plotly_chart(fig_sip, use_container_width=True)

            with st.expander("View Year-by-Year Growth Table"):
                st.dataframe(df_sip, use_container_width=True)

    # --------------------------------------------------------
    # TAB 4: FIXED & RECURRING DEPOSITS
    # --------------------------------------------------------
    with tabs[3]:
        st.subheader("Fixed Deposit and Recurring Deposit Planner")
        st.write("Calculate guaranteed returns, interest accrual, and inflation-adjusted real returns for fixed and recurring deposits.")

        dep_type = st.radio("Choose Deposit Type:", ["Fixed Deposit (Lump Sum)", "Recurring Deposit (Monthly)"], horizontal=True)

        if dep_type == "Fixed Deposit (Lump Sum)":
            fd_c1, fd_c2, fd_c3 = st.columns(3)
            with fd_c1:
                fd_p = st.number_input(
                    "Deposit Principal Amount (Min ₹1,000)",
                    min_value=1000.0,
                    value=100000.0,
                    step=1000.0,
                    key="fd_p",
                    help="Minimum initial fixed deposit principal amount is ₹1,000."
                )
            with fd_c2:
                fd_r = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=30.0, value=7.25, step=0.1, key="fd_r")
            with fd_c3:
                fd_t = st.number_input("Tenure (Years)", min_value=0.1, max_value=30.0, value=3.0, step=0.25, key="fd_t")

            fd_int, fd_mat = calculate_fixed_deposit(fd_p, fd_r, fd_t)

            st.markdown("---")
            f1, f2, f3 = st.columns(3)
            with f1:
                st.metric("Total Deposited", f"{sym}{fd_p:,.2f}")
            with f2:
                st.metric("Total Interest Earned", f"{sym}{fd_int:,.2f}")
            with f3:
                st.metric("Maturity Payout", f"{sym}{fd_mat:,.2f}")

        else:
            rd_c1, rd_c2, rd_c3 = st.columns(3)
            with rd_c1:
                rd_m = st.number_input(
                    "Monthly Deposit Amount (Min ₹500)",
                    min_value=500.0,
                    value=5000.0,
                    step=500.0,
                    key="rd_m",
                    help="Minimum recurring deposit monthly installment is ₹500."
                )
            with rd_c2:
                rd_r = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=30.0, value=7.0, step=0.1, key="rd_r")
            with rd_c3:
                rd_mo = st.number_input("Tenure (Months)", min_value=1, max_value=120, value=24, step=3, key="rd_mo")

            rd_int, rd_mat = calculate_recurring_deposit(rd_m, rd_r, rd_mo)
            rd_tot = rd_m * rd_mo

            st.markdown("---")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Total Deposited", f"{sym}{rd_tot:,.2f}")
            with r2:
                st.metric("Total Interest Earned", f"{sym}{rd_int:,.2f}")
            with r3:
                st.metric("Maturity Payout", f"{sym}{rd_mat:,.2f}")

    # --------------------------------------------------------
    # TAB 5: FINANCIAL TERMS, CONDITIONS & REPAYMENT GUIDE
    # --------------------------------------------------------
    with tabs[4]:
        st.subheader("Financial Terms, Conditions and Repayment Guide")
        st.write(
            "A master educational and regulatory reference guide explaining all terms, conditions, "
            "repayment mechanics, and fine print across loans, SIPs, deposits, and insurance."
        )

        with st.expander("1. How to Repay Loans Faster: Step-by-Step Practical Guide", expanded=True):
            st.markdown(
                """
                ### Core Strategies to Accelerate Loan Repayment

                1. **Understand Reducing Balance Interest:**
                   - In reducing balance loans, interest is calculated on the remaining principal balance at the end of each month.
                   - In the early years of any long-term loan (e.g., home loan), **70% to 80% of your EMI goes purely toward paying interest**, while only a small fraction reduces principal.
                   - Any extra payment you make goes **100% toward principal reduction**, immediately lowering all future monthly interest calculations.

                2. **The 13th EMI Method:**
                   - Pay 1 extra EMI every year (e.g. from your annual bonus or festival payout).
                   - For a 20-year home loan of ₹30 Lakhs at 8.75%, this simple step cuts the loan tenure down by **4.5 years** and saves over **₹6.5 Lakhs** in interest.

                3. **Annual 5% to 10% Step-Up EMI:**
                   - When your annual income increases, instruct your bank to increase your monthly EMI by 5% to 10%.
                   - Stepping up EMI by 5% each year reduces a 20-year loan tenure down to approximately **12 years**.

                4. **Verify Application of Prepayment with Lender:**
                   - Always obtain a written or digital receipt stating that the prepayment is credited against **Principal Outstanding**, rather than stored as an advance against upcoming EMIs.
                   - Opt for **Tenure Reduction** instead of EMI Reduction when prepaying to maximize interest savings.

                5. **Debt Avalanche vs Debt Snowball (For Multiple Debts):**
                   - **Debt Avalanche (Mathematically Optimal):** Pay minimums on all debts, and allocate every spare rupee to the debt with the highest interest rate (e.g., Credit Cards @ 40% p.a. > Personal Loans @ 14% p.a. > Auto Loans @ 9% p.a. > Home Loans @ 8.5% p.a.).
                   - **Debt Snowball (Psychological Momentum):** Pay off the smallest debt balance first to celebrate quick wins, then roll that monthly payment into the next smallest balance.
                """
            )

        with st.expander("2. How SIP and Compounding Investments Work: Master Guide", expanded=True):
            st.markdown(
                """
                ### Understanding Systematic Investment Plans (SIP)

                1. **The Compounding Formula:**
                   - Wealth accumulates exponentially through compound interest:
                     $$\\text{Future Value} = P \\times (1 + r)^t + \\sum \\text{Contributions}$$
                   - Time in the market matters significantly more than timing the market. Starting 5 years earlier can double your eventual retirement corpus.

                2. **Rupee Cost Averaging:**
                   - When market prices dip, your fixed monthly SIP purchases more fund units.
                   - When market prices surge, your SIP purchases fewer units.
                   - Over 5 to 10+ years, this eliminates the risk of bad market timing and generates a lower average purchase cost.

                3. **The Step-Up SIP Advantage:**
                   - Increasing your monthly investment by 10% annually dramatically accelerates wealth creation.
                   - Example: A base SIP of ₹10,000/month at 12% return yields ₹50 Lakhs in 15 years. With a 10% annual step-up, the final corpus exceeds **₹98 Lakhs** for the exact same 15-year period.
                """
            )

        with st.expander("3. Loan and Debt Terms and Conditions Explained"):
            st.markdown(
                """
                ### Key Loan Terms You Must Know

                - **APR (Annual Percentage Rate) vs. Nominal Rate:**
                  - The nominal rate is just the interest percentage. The APR reflects the true annual borrowing cost, including processing fees, administrative charges, documentation fees, and mandatory credit insurance.
                - **Flat Interest Rate vs. Reducing Balance Rate:**
                  - In a *flat rate loan*, interest is always computed on the initial principal throughout the entire tenure. A 10% flat interest rate is mathematically equivalent to approximately an **18% to 19% reducing balance interest rate**.
                - **Prepayment & Foreclosure Penalties (RBI Guidelines):**
                  - Under Reserve Bank of India (RBI) regulations, banks and NBFCs cannot charge foreclosure or prepayment penalties on **floating-rate home loans** taken by individual borrowers.
                  - Fixed-rate loans, commercial loans, and corporate borrowings may carry prepayment charges ranging from 2% to 4% + GST.
                - **Penal Interest and NACH Bounce Charges:**
                  - If an EMI is missed or delayed, banks levy penal interest (typically 18% to 24% p.a.) on the overdue instalment, alongside electronic mandate (NACH) bounce charges (₹400 to ₹750 per failure).
                - **Loan-to-Value (LTV) Ratio:**
                  - The percentage of the property or asset value that a lender is willing to finance (e.g. 75% to 80% for housing loans; the remaining 20% to 25% is your down payment).
                - **Credit Score (CIBIL) Impact:**
                  - Every missed EMI drops credit scores by 30 to 50+ points, leading to higher interest rates or loan rejections in the future.
                """
            )

        with st.expander("4. Investment and Mutual Fund Terms and Conditions Explained"):
            st.markdown(
                """
                ### Key Investment and Mutual Fund Terms

                - **NAV (Net Asset Value):**
                  - The per-unit market value of a mutual fund scheme, calculated by dividing the total net assets of the fund by the total outstanding units.
                - **TER (Total Expense Ratio):**
                  - The annual percentage fee charged by the fund house to manage the fund. Direct mutual fund plans have lower expense ratios (often 0.3% to 0.8%) compared to Regular plans (1.5% to 2.2%), saving significant wealth over decades.
                - **Exit Load:**
                  - A fee levied if you redeem or sell mutual fund units before a specified holding period (e.g. 1% if redeemed within 365 days of investment).
                - **LTCG and STCG Taxation (India Tax Code):**
                  - **Equity Mutual Funds:** Holding period > 12 months is classified as Long-Term Capital Gains (LTCG). Gains up to ₹1.25 Lakh per financial year are tax-exempt; gains above ₹1.25 Lakh are taxed at 12.5%. Short-term gains (< 12 months) are taxed at 20%.
                  - **Debt Mutual Funds:** Taxed as per your applicable income tax slab rate.
                - **Asset Allocation:**
                  - The strategy of balancing risk and reward by dividing investments among equities, debt/fixed income, and cash/gold based on your time horizon and risk tolerance.
                """
            )

        with st.expander("5. Deposit and Insurance Terms and Conditions Explained"):
            st.markdown(
                """
                ### Key Deposit and Insurance Terms

                - **Premature Fixed Deposit Withdrawal Penalty:**
                  - Withdrawing a fixed deposit before the agreed maturity date generally incurs a penal reduction of 0.5% to 1.0% from the applicable interest rate for the actual duration held.
                - **TDS and Form 15G / 15H:**
                  - Tax Deducted at Source (TDS) is deducted on bank interest exceeding ₹40,000/year (₹50,000 for senior citizens). Submitting Form 15G (for individuals below 60) or Form 15H (for senior citizens) prevents TDS if total taxable income is nil.
                - **DICGC Deposit Insurance:**
                  - The Deposit Insurance and Credit Guarantee Corporation (a subsidiary of the RBI) insures bank deposits (savings, current, fixed, recurring) up to **₹5,00,000** per depositor per bank across all branches.
                - **Room Rent Sub-Limits in Health Insurance:**
                  - Capping hospital room rent at 1% of the sum insured triggers *proportionate deduction* across doctor consultation, surgeon fees, and surgical procedures if a higher room tier is chosen.
                - **Co-Payment Clause:**
                  - A mandatory percentage (e.g. 10% to 20%) of the total approved hospital claim that the policyholder must pay out-of-pocket on every claim.
                - **PED Waiting Period:**
                  - The mandatory period (typically 24 to 36 months) before claims for Pre-Existing Diseases (e.g., diabetes, hypertension) become eligible for coverage.
                """
            )


# ============================================================
# FINANCIAL ASSISTANT PAGE
# ============================================================

def financial_assistant_page():
    st.title("Financial Assistant")

    col_chat_title, col_chat_actions = st.columns([3, 2])
    with col_chat_title:
        st.write("Context-aware financial planning assistant with numerical calculation capabilities and multi-journey intelligence.")
    with col_chat_actions:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("Clear Chat", key="clear_chat_history_btn", use_container_width=True):
                default_greeting = [
                    {
                        "role": "assistant",
                        "content": "Hello. I am your FinPath Financial Assistant. You can ask me about loan applications, health insurance, bank deposits, SIP wealth compounding, or any financial journey."
                    }
                ]
                st.session_state.chat_messages = default_greeting
                storage.set_stored_item("chat_messages", default_greeting)
                storage.sync_to_browser_local_storage("finpath_chat_messages", default_greeting)
                st.rerun()
        with btn_c2:
            chat_text = "\n\n".join([f"**{m['role'].upper()}:**\n{m['content']}" for m in st.session_state.chat_messages])
            st.download_button(
                "Export Chat Transcript",
                data=chat_text,
                file_name="FinPath_Chat_Transcript.md",
                mime="text/markdown",
                use_container_width=True
            )

    st.markdown("### Suggested Questions and Quick Scenarios")
    suggested_questions = [
        "How do I apply for a loan step-by-step?",
        "What are the steps to choose and take health insurance?",
        "What are the steps to deposit money in a bank or open an FD?",
        "How can I repay my loan faster using prepayment strategies?",
        "How do I start a Systematic Investment Plan (SIP)?",
        "Calculate EMI for loan of 1000000 at 8.5% for 120 months"
    ]

    cols = st.columns(2)
    for index, question in enumerate(suggested_questions):
        with cols[index % 2]:
            if st.button(question, key=f"suggested_question_{index}", use_container_width=True):
                response = get_chat_response(question)
                st.session_state.chat_messages.append({"role": "user", "content": question})
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                storage.set_stored_item("chat_messages", st.session_state.chat_messages)
                storage.sync_to_browser_local_storage("finpath_chat_messages", st.session_state.chat_messages)
                st.rerun()

    st.markdown("---")

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input("Ask your financial question (e.g. loan applications, health insurance, deposits, SIP compounding, major journeys)...")
    if user_question:
        response = get_chat_response(user_question)
        st.session_state.chat_messages.append({"role": "user", "content": user_question})
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        storage.set_stored_item("chat_messages", st.session_state.chat_messages)
        storage.sync_to_browser_local_storage("finpath_chat_messages", st.session_state.chat_messages)
        st.rerun()


# ============================================================
# DOCUMENT CHECKLIST PAGE
# ============================================================

def document_checklist_page():
    st.title("Document Checklist")
    st.write("Use this checklist to track common documents for a selected financial activity.")

    activity_documents = {
        "Bank Deposit": [
            "Identity proof",
            "Address proof",
            "Tax identification",
            "Photograph",
            "Bank account details",
            "Nominee details",
            "KYC form"
        ],
        "Loan Application": [
            "Identity proof",
            "Address proof",
            "Tax identification",
            "Salary slips or income proof",
            "Bank statements",
            "Employment or business proof",
            "Income tax returns, where applicable",
            "Collateral documents, where applicable"
        ],
        "Health Insurance": [
            "Identity proof",
            "Address proof",
            "Age proof",
            "Medical history",
            "Medical reports, if requested",
            "Existing insurance details",
            "Nominee details",
            "Proposal form"
        ],
        "Regular Contribution": [
            "Identity proof",
            "Address proof",
            "Tax identification",
            "Bank account details",
            "Nominee details",
            "Risk profile information, where applicable",
            "Registration form"
        ]
    }

    activity = st.selectbox("Choose an activity", list(activity_documents.keys()))
    documents = activity_documents[activity]
    saved_checklists = st.session_state.get("checklists", {})
    checked_count = 0

    for index, document in enumerate(documents):
        doc_storage_key = f"{activity}_{document}"
        initial_val = saved_checklists.get(doc_storage_key, False)
        widget_key = f"chk_{activity}_{index}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = initial_val

        checked = st.checkbox(document, key=widget_key)
        if checked != initial_val:
            saved_checklists[doc_storage_key] = checked
            st.session_state.checklists = saved_checklists
            storage.set_stored_item("checklists", saved_checklists)
            storage.sync_to_browser_local_storage("finpath_checklists", saved_checklists)

        if checked:
            checked_count += 1

    total = len(documents)
    progress = checked_count / total if total else 0

    st.markdown("---")
    st.subheader("Checklist Progress")
    st.progress(progress)
    st.write(f"{checked_count} of {total} documents checked ({progress * 100:.0f}%)")

    if checked_count == total:
        st.success("All documents in this checklist are marked complete.")
    else:
        st.info(f"{total - checked_count} document(s) remain unchecked.")


# ============================================================
# PROFILE PAGE
# ============================================================

def profile_page():
    st.title("User Profile & Financial Identity")
    st.write("Enter your **Name**, **Monthly Net Income**, and **Monthly Savings** to personalize all financial models, budget blueprints, and PDF reports.")

    profile = st.session_state.get("profile", {})
    curr_name = str(profile.get("name", "") or "")
    curr_income = safe_float(profile.get("monthly_income", 0.0))
    curr_savings = safe_float(profile.get("monthly_saving_capacity", 0.0))

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            "Full Name *",
            value=curr_name,
            placeholder="e.g. John Doe",
            help="Enter your name as you would like it to appear on your financial reports"
        )
        monthly_income = st.number_input(
            f"Monthly Net Income ({currency_symbol()}) *",
            min_value=0.0,
            value=curr_income,
            step=1000.0,
            help="Your take-home monthly salary or business net income"
        )

    with col2:
        monthly_saving_capacity = st.number_input(
            f"Monthly Savings / Saving Capacity ({currency_symbol()}) *",
            min_value=0.0,
            value=curr_savings,
            step=500.0,
            help="Amount you save or invest every month"
        )
        currency_options = ["INR", "USD", "EUR", "GBP"]
        curr_index = currency_options.index(st.session_state.currency) if st.session_state.currency in currency_options else 0
        currency = st.selectbox(
            "Preferred Currency",
            currency_options,
            index=curr_index,
            help="Currency used across all dashboards and reports"
        )

    # Optional Additional Details
    with st.expander("Additional Optional Details (Age, Occupation, Goals, Existing Debts, Insurance)", expanded=False):
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            age = st.number_input("Age (Years)", min_value=18, max_value=100, value=int(profile.get("age", 28) or 28), step=1)
            occupation_options = [
                "Salaried Professional (Private Sector)",
                "Salaried Professional (Govt / PSU)",
                "Business Owner / Entrepreneur",
                "Self-Employed / Freelancer / Consultant",
                "Healthcare / Medical Professional",
                "Homemaker",
                "Retired Professional",
                "Student / Early Career"
            ]
            current_occ = profile.get("occupation", "Salaried Professional (Private Sector)")
            occ_index = occupation_options.index(current_occ) if current_occ in occupation_options else 0
            occupation = st.selectbox("Occupation / Employment Type", occupation_options, index=occ_index)
            city = st.text_input("City / State", value=str(profile.get("city", "") or ""), placeholder="e.g. Mumbai, Maharashtra")
            existing_monthly_emi = st.number_input("Current Monthly EMI Obligations", min_value=0.0, value=safe_float(profile.get("existing_monthly_emi", 0.0)), step=500.0)

        with col_opt2:
            goal_options = [
                "Buying a Home / Property",
                "Buying a Vehicle / Car",
                "Child Higher Education & Future",
                "Debt Freedom & Rapid Loan Prepayment",
                "Wealth Compounding & Early Retirement (FIRE)",
                "Emergency Fund Creation & Risk Shielding",
                "Vacation & Lifestyle Milestone",
                "General Wealth Building & Capital Growth"
            ]
            current_goal = profile.get("primary_goal", "Buying a Home / Property")
            goal_index = goal_options.index(current_goal) if current_goal in goal_options else 0
            primary_goal = st.selectbox("Primary Financial Milestone", goal_options, index=goal_index)

            risk_options = [
                "Conservative (Capital Preservation, FDs & Debt Funds)",
                "Moderate (Balanced Growth, 50% Equity / 50% Debt)",
                "Aggressive (High Growth, Index & Large-Cap Equity)",
                "Very Aggressive (Maximum Growth, Mid/Small Caps & Thematic)"
            ]
            current_risk = profile.get("risk_profile", "Moderate (Balanced Growth)")
            risk_index = risk_options.index(current_risk) if current_risk in risk_options else 1
            risk_profile = st.selectbox("Investment Risk Profile", risk_options, index=risk_index)

            health_insurance_cover = st.number_input("Health Insurance Coverage (Sum Insured)", min_value=0.0, value=safe_float(profile.get("health_insurance_cover", 0.0)), step=50000.0)
            term_insurance_cover = st.number_input("Term / Life Insurance Coverage", min_value=0.0, value=safe_float(profile.get("term_insurance_cover", 0.0)), step=100000.0)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("Save User Profile", type="primary", use_container_width=True):
            new_profile = {
                "name": name.strip(),
                "email": str(profile.get("email", "") or "").strip(),
                "age": int(age) if 'age' in locals() else int(profile.get("age", 28) or 28),
                "occupation": occupation if 'occupation' in locals() else str(profile.get("occupation", "Salaried Professional")),
                "city": city.strip() if 'city' in locals() else str(profile.get("city", "")),
                "dependents": int(profile.get("dependents", 0) or 0),
                "monthly_income": safe_float(monthly_income),
                "monthly_saving_capacity": safe_float(monthly_saving_capacity),
                "existing_monthly_emi": safe_float(existing_monthly_emi) if 'existing_monthly_emi' in locals() else safe_float(profile.get("existing_monthly_emi", 0.0)),
                "existing_investments": safe_float(profile.get("existing_investments", 0.0)),
                "emergency_fund": safe_float(profile.get("emergency_fund", 0.0)),
                "health_insurance_cover": safe_float(health_insurance_cover) if 'health_insurance_cover' in locals() else safe_float(profile.get("health_insurance_cover", 0.0)),
                "term_insurance_cover": safe_float(term_insurance_cover) if 'term_insurance_cover' in locals() else safe_float(profile.get("term_insurance_cover", 0.0)),
                "primary_goal": primary_goal if 'primary_goal' in locals() else str(profile.get("primary_goal", "Buying a Home / Property")),
                "target_horizon": str(profile.get("target_horizon", "Medium-Term (3 - 5 Years)")),
                "risk_profile": risk_profile if 'risk_profile' in locals() else str(profile.get("risk_profile", "Moderate (Balanced Growth)"))
            }
            st.session_state.profile = new_profile
            st.session_state.currency = currency

            storage.set_stored_item("profile", new_profile)
            storage.set_stored_item("currency", currency)
            storage.sync_to_browser_local_storage("finpath_profile", new_profile)
            storage.sync_to_browser_local_storage("finpath_currency", currency)

            try:
                requests.post("http://127.0.0.1:5000/profile", json={
                    "name": name.strip(),
                    "monthly_income": safe_float(monthly_income),
                    "primary_goal": new_profile.get("primary_goal", "Financial Planning")
                }, timeout=0.5)
            except Exception:
                pass

            storage.log_activity(
                "Profile Management",
                f"Updated Profile: {name.strip() or 'User'}",
                f"Income: {currency_symbol()}{safe_float(monthly_income):,.2f} | Savings: {currency_symbol()}{safe_float(monthly_saving_capacity):,.2f} ({currency})"
            )

            st.success("User profile saved successfully!")
            st.rerun()

    with col_btn2:
        if st.button("Reset / Clear Profile", use_container_width=True):
            storage.clear_local_storage()
            storage.clear_browser_local_storage()
            st.session_state.profile = storage.DEFAULT_STORAGE["profile"]
            st.session_state.currency = "INR"
            st.session_state.checklists = {}
            st.session_state.journey_twin = {"action": "Select an action", "documents": {}}
            st.info("Profile data has been cleared.")
            st.rerun()

    st.markdown("---")
    st.subheader("Full Financial Report Card & User Activity Audit")
    st.write(
        "Download your comprehensive financial health assessment and a complete chronological timeline "
        "of all financial models, simulations, document audits, and journey milestones performed on FinPath."
    )

    activities = storage.get_activity_log() or []

    # Chronological Activity Timeline Container with live view
    with st.expander(f"Chronological Site Activity Timeline ({len(activities)} Total Events)", expanded=True):
        if activities:
            tab_cards, tab_table = st.tabs(["Interactive Timeline Cards", "Audit Data Table"])

            with tab_cards:
                for act in reversed(activities[-25:]):
                    t_stamp = act.get("timestamp", "")
                    cat = act.get("category", "General")
                    action_text = act.get("action", "")
                    details_text = act.get("details", "")

                    st.markdown(
                        f"""
                        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-left:3px solid #007FFF;border-radius:6px;padding:0.5rem 0.8rem;margin-bottom:0.45rem;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-weight:600;font-size:0.86rem;color:#f8fafc;">{action_text}</span>
                                <span style="font-size:0.72rem;color:#94a3b8;">{t_stamp}</span>
                            </div>
                            <div style="font-size:0.78rem;color:#cbd5e1;margin-top:2px;">
                                <span style="background:rgba(0,127,255,0.2);color:#93c5fd;padding:1px 6px;border-radius:4px;font-size:0.7rem;margin-right:6px;">{cat}</span>
                                {details_text}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            with tab_table:
                df_act = pd.DataFrame(activities)
                if not df_act.empty:
                    st.dataframe(
                        df_act.iloc[::-1],
                        column_config={
                            "timestamp": "Timestamp",
                            "category": "Domain",
                            "action": "Action Taken",
                            "details": "Details & Impact"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
        else:
            st.info("No activities recorded yet. Explore Wealth & Debt Hub, Document AI, or Journey Twin to build your timeline.")

    st.markdown("### Export Full Report & Activity Timeline")
    st.write("Choose your preferred format to download your complete profile, financial health grade, and activity timeline:")

    clean_name = name.strip() or "Client"

    try:
        report_card_pdf = generate_report_card_with_timeline_pdf(
            profile_data=st.session_state.get("profile", {}),
            activities=activities,
            journey_data=st.session_state.get("journey_twin", {}),
            currency=st.session_state.currency
        )
    except Exception as e:
        print(f"[FinPath] PDF Error: {e}")
        report_card_pdf = b"%PDF-1.4 Empty Report"

    try:
        rep_md = generate_executive_report_markdown()
    except Exception as e:
        print(f"[FinPath] MD Error: {e}")
        rep_md = "# FinPath Report\n\nReport generation in progress."

    # CSV Timeline Builder
    try:
        import io as py_io
        import csv as py_csv
        csv_buffer = py_io.StringIO()
        csv_writer = py_csv.DictWriter(csv_buffer, fieldnames=["timestamp", "category", "action", "details"])
        csv_writer.writeheader()
        for act in activities:
            csv_writer.writerow({
                "timestamp": act.get("timestamp", ""),
                "category": act.get("category", ""),
                "action": act.get("action", ""),
                "details": act.get("details", "")
            })
        csv_data = csv_buffer.getvalue().encode("utf-8")
    except Exception:
        csv_data = b"timestamp,category,action,details\n"

    # JSON Timeline Builder
    try:
        json_data = json.dumps({
            "profile": st.session_state.get("profile", {}),
            "currency": st.session_state.currency,
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activity_log": activities
        }, indent=2).encode("utf-8")
    except Exception:
        json_data = b"{}"

    # Export Buttons Grid
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.download_button(
            "Download Full Report Card with Timeline (PDF)",
            data=report_card_pdf,
            file_name=f"FinPath_Report_Card_{clean_name}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            help="Download comprehensive PDF report card with full activity history and timeline."
        )
        st.download_button(
            "Download Full Activity Timeline (CSV)",
            data=csv_data,
            file_name=f"FinPath_Activity_Timeline_{clean_name}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_exp2:
        st.download_button(
            "Download Full Report Card (.md)",
            data=rep_md,
            file_name=f"FinPath_Financial_Health_{clean_name}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.download_button(
            "Download Activity Audit (.json)",
            data=json_data,
            file_name=f"FinPath_Activity_Audit_{clean_name}.json",
            mime="application/json",
            use_container_width=True
        )


# ============================================================
# PAGE ROUTER
# ============================================================

if st.session_state.page in ["Dashboard", "Overview"]:
    dashboard_page()

elif st.session_state.page == "Decision Guide":
    decision_guide_page()

elif st.session_state.page == "Journey Twin":
    journey_twin_page()

elif st.session_state.page in ["Wealth & Debt Hub", "Deposit Planner"]:
    wealth_debt_hub_page()

elif st.session_state.page == "Document AI":
    document_ai_page()

elif st.session_state.page == "Financial Assistant":
    financial_assistant_page()

elif st.session_state.page == "Document Checklist":
    document_checklist_page()

elif st.session_state.page == "Profile":
    profile_page()