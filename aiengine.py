# ============================================================
# FINPATH - CONTEXT-AWARE FINANCIAL AI ENGINE
# ============================================================

import re


# ------------------------------------------------------------
# INTENT DETECTION KEYWORDS
# ------------------------------------------------------------

INTENT_KEYWORDS = {
    "journey": [
        "journey", "financial journey", "milestone", "roadmap", "lifecycle",
        "stages", "step by step journey", "claim journey", "loan journey",
        "investment journey", "savings journey", "retirement journey",
        "home buying journey", "tax journey"
    ],
    "insurance": [
        "insurance", "claim", "policy", "premium", "hospital",
        "medical", "coverage", "health insurance", "life insurance",
        "term insurance", "mediclaim", "copay", "co-payment",
        "sub-limit", "room rent", "waiting period", "ped", "tpa",
        "cashless", "reimbursement", "critical illness", "restoration",
        "no claim bonus", "ncb", "ombudsman"
    ],
    "loan": [
        "loan", "borrow", "emi", "credit", "debt", "interest rate",
        "repayment", "lending", "amortization", "prepayment",
        "foreclosure", "tenure", "principal", "cibil", "credit score",
        "sanction letter", "nach", "foir", "ltv", "balance transfer",
        "home loan", "personal loan", "car loan", "auto loan", "gold loan",
        "fixed rate", "floating rate", "13th emi", "debt avalanche", "debt snowball"
    ],
    "investment": [
        "invest", "investment", "investing", "mutual fund", "sip",
        "systematic investment plan", "step up", "step-up", "stock", "stocks",
        "shares", "portfolio", "return", "returns", "compound", "compounding",
        "wealth", "equity", "debt fund", "index fund", "nifty", "nav",
        "expense ratio", "ter", "direct plan", "regular plan", "ltcg", "stcg",
        "rupee cost averaging", "cagr", "elss"
    ],
    "saving": [
        "save", "saving", "savings", "fixed deposit", "recurring deposit",
        "fd", "rd", "term deposit", "deposit", "money management",
        "form 15g", "form 15h", "tds", "dicgc", "nominee", "nomination",
        "minimum deposit", "minimum amount", "premature withdrawal"
    ],
    "budget": [
        "budget", "50/30/20", "needs", "wants", "emergency fund",
        "runway", "monthly expense", "spending", "allocate", "living expense"
    ],
    "general": [
        "finance", "financial", "money", "financial planning",
        "help", "advice", "guidance", "hello", "hi", "hey"
    ]
}


# ------------------------------------------------------------
# FIND INTENT
# ------------------------------------------------------------

def understand_intent(message):
    if not message:
        return "general"

    message = str(message).lower()
    scores = {}

    # Check for explicit journey mentions
    if any(k in message for k in ["journey", "financial journey", "roadmap", "step by step roadmap", "milestones"]):
        return "journey"

    for intent, words in INTENT_KEYWORDS.items():
        score = 0
        for word in words:
            if word in message:
                # Give higher weight to multi-word phrases
                score += (2 if " " in word else 1)
        scores[intent] = score

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] == 0:
        return "general"

    return best_intent


# ------------------------------------------------------------
# EXTRACT NUMBERS
# ------------------------------------------------------------

def extract_numbers(message):
    if not message:
        return []
    cleaned = str(message).replace(",", "")
    numbers = re.findall(r"\d+(?:\.\d+)?", cleaned)
    return [float(number) for number in numbers]


# ------------------------------------------------------------
# FINANCIAL MATH ENGINES
# ------------------------------------------------------------

def calculate_emi(principal, annual_rate, months):
    """
    Standard Equated Monthly Installment (EMI) Formula.
    """
    if principal <= 0 or months <= 0:
        return 0.0

    monthly_rate = annual_rate / 12.0 / 100.0

    if monthly_rate == 0:
        return principal / months

    try:
        factor = (1 + monthly_rate) ** months
        emi = (principal * monthly_rate * factor) / (factor - 1)
        return emi
    except OverflowError:
        return 0.0


def calculate_loan_amortization(principal, annual_rate, months, extra_monthly=0.0, extra_yearly=0.0):
    """
    Detailed loan amortization schedule with prepayment simulation.
    Returns monthly schedule, total interest, total paid, and savings.
    """
    if principal <= 0 or months <= 0:
        return {
            "schedule": [],
            "base_emi": 0.0,
            "total_interest": 0.0,
            "total_payment": 0.0,
            "prepaid_schedule": [],
            "prepaid_total_interest": 0.0,
            "prepaid_total_payment": 0.0,
            "interest_saved": 0.0,
            "months_saved": 0
        }

    monthly_rate = annual_rate / 12.0 / 100.0
    base_emi = calculate_emi(principal, annual_rate, months)

    # 1. Base Schedule (No Prepayments)
    base_schedule = []
    balance = float(principal)
    total_interest_base = 0.0

    for m in range(1, int(months) + 1):
        if balance <= 0:
            break
        interest_for_month = balance * monthly_rate
        principal_for_month = min(balance, base_emi - interest_for_month)
        if principal_for_month < 0:
            principal_for_month = 0.0
        payment = principal_for_month + interest_for_month
        balance -= principal_for_month
        total_interest_base += interest_for_month

        base_schedule.append({
            "month": m,
            "payment": round(payment, 2),
            "principal_paid": round(principal_for_month, 2),
            "interest_paid": round(interest_for_month, 2),
            "remaining_balance": round(max(0.0, balance), 2)
        })

    # 2. Prepayment Schedule (If extra payment applied)
    prepaid_schedule = []
    prepaid_balance = float(principal)
    total_interest_prepaid = 0.0
    prepaid_months_count = 0

    has_prepayment = (extra_monthly > 0 or extra_yearly > 0)

    if has_prepayment:
        for m in range(1, int(months) * 2):  # safety bound
            if prepaid_balance <= 0.01:
                break
            prepaid_months_count += 1
            interest_for_month = prepaid_balance * monthly_rate

            extra_this_month = extra_monthly
            if m % 12 == 0:
                extra_this_month += extra_yearly

            target_payment = base_emi + extra_this_month
            principal_for_month = min(prepaid_balance, target_payment - interest_for_month)
            if principal_for_month < 0:
                principal_for_month = 0.0
            payment = principal_for_month + interest_for_month
            prepaid_balance -= principal_for_month
            total_interest_prepaid += interest_for_month

            prepaid_schedule.append({
                "month": m,
                "payment": round(payment, 2),
                "principal_paid": round(principal_for_month, 2),
                "interest_paid": round(interest_for_month, 2),
                "remaining_balance": round(max(0.0, prepaid_balance), 2)
            })

        interest_saved = max(0.0, total_interest_base - total_interest_prepaid)
        months_saved = max(0, int(months) - prepaid_months_count)
    else:
        prepaid_schedule = base_schedule
        total_interest_prepaid = total_interest_base
        interest_saved = 0.0
        months_saved = 0

    return {
        "base_emi": round(base_emi, 2),
        "total_interest": round(total_interest_base, 2),
        "total_payment": round(principal + total_interest_base, 2),
        "schedule": base_schedule,
        "prepaid_schedule": prepaid_schedule,
        "prepaid_total_interest": round(total_interest_prepaid, 2),
        "prepaid_total_payment": round(principal + total_interest_prepaid, 2),
        "interest_saved": round(interest_saved, 2),
        "months_saved": months_saved
    }


def calculate_budget_50_30_20(monthly_income, monthly_savings=0.0):
    """
    50/30/20 Budgeting rule breakdown and Emergency Runway calculator.
    """
    income = max(0.0, float(monthly_income))
    needs = round(income * 0.50, 2)
    wants = round(income * 0.30, 2)
    recommended_savings = round(income * 0.20, 2)
    actual_savings = max(0.0, float(monthly_savings))

    # Emergency Fund (3 months and 6 months of essential needs)
    emergency_3mo = round(needs * 3, 2)
    emergency_6mo = round(needs * 6, 2)

    # Time to build 6-month fund
    if actual_savings > 0:
        months_to_6mo = round(emergency_6mo / actual_savings, 1)
    else:
        months_to_6mo = 0

    return {
        "income": income,
        "needs_50": needs,
        "wants_30": wants,
        "savings_20": recommended_savings,
        "actual_savings": actual_savings,
        "emergency_3_months": emergency_3mo,
        "emergency_6_months": emergency_6mo,
        "months_to_build_emergency_fund": months_to_6mo
    }


def calculate_sip_wealth(monthly_investment, annual_rate, years, step_up_percent=0.0):
    """
    Calculates compound growth of regular SIP investment with optional annual step-up.
    """
    months = int(years * 12)
    monthly_rate = (annual_rate / 100.0) / 12.0
    current_sip = float(monthly_investment)
    total_invested = 0.0
    future_value = 0.0
    yearly_breakdown = []

    for m in range(1, months + 1):
        if step_up_percent > 0 and m > 1 and (m - 1) % 12 == 0:
            current_sip += current_sip * (step_up_percent / 100.0)

        total_invested += current_sip
        future_value = (future_value + current_sip) * (1.0 + monthly_rate)

        if m % 12 == 0 or m == months:
            year_num = m // 12 if m % 12 == 0 else years
            yearly_breakdown.append({
                "year": year_num,
                "invested": round(total_invested, 2),
                "wealth": round(future_value, 2),
                "returns": round(max(0.0, future_value - total_invested), 2)
            })

    total_returns = max(0.0, future_value - total_invested)
    return {
        "total_invested": round(total_invested, 2),
        "total_returns": round(total_returns, 2),
        "future_value": round(future_value, 2),
        "yearly_breakdown": yearly_breakdown
    }


# ------------------------------------------------------------
# CONTEXT-AWARE RESPONSE GENERATORS
# ------------------------------------------------------------

def insurance_response(message, profile=None):
    profile = profile or {}
    name = profile.get("name", "").strip()
    greeting = f"Hello {name}, " if name else ""
    msg_lower = str(message).lower()

    # 1. Insurance Claim Journey / Process
    if any(phrase in msg_lower for phrase in [
        "claim", "how to claim", "file a claim", "claim process", "claim settlement",
        "cashless claim", "reimbursement claim", "claim rejected", "tpa"
    ]):
        response = (
            f"{greeting}Here is the complete step-by-step **Health & Term Insurance Claim Journey**:\n\n"
            "### A. Cashless Hospitalization Journey (At Network Hospitals)\n"
            "1. **Pre-Authorization (Planned Hospitalization):** Inform the hospital TPA / Insurance desk 48 to 72 hours prior to admission with your E-Card and Photo ID (PAN / Aadhaar).\n"
            "2. **Emergency Hospitalization:** Intimate your insurer / TPA within 24 hours of hospital admission.\n"
            "3. **Initial Sanction:** The insurer issues an initial pre-approval for admissible medical expenses.\n"
            "4. **Final Bill & Discharge:** At discharge, the hospital sends final summary to the insurer. Insurer settles the approved amount directly with the hospital, while you only pay non-medical expenses / co-pay.\n\n"
            "### B. Reimbursement Claim Journey (At Non-Network Hospitals)\n"
            "1. **Notify Insurer:** Send intimation within 24-48 hours of admission.\n"
            "2. **Collect All Original Documents:**\n"
            "   - Duly filled and signed Claim Form (Part A & Part B).\n"
            "   - Original Hospital Discharge Summary mentioning diagnosis, history, and treatment given.\n"
            "   - Original Itemized Hospital Bills, Pharmacy Receipts, and Payment Receipts.\n"
            "   - Diagnostic Test Reports (Blood tests, X-rays, MRI, Histopathology, etc.).\n"
            "   - Doctor's initial consultation prescription.\n"
            "3. **Submit Within 15 to 30 Days:** Dispatch original dossier to the TPA office and track acknowledgment.\n"
            "4. **Settlement:** Insurer processes reimbursement directly to your bank account via NEFT within 15-30 days.\n\n"
            "### C. Claim Rejection & Grievance Redressal\n"
            "- If a claim is unfairly rejected or delayed, escalate to the Insurer's Grievance Redressal Officer (GRO).\n"
            "- If unresolved within 30 days, file a complaint with the **Insurance Ombudsman** or IRDAI Bima Bharosa portal."
        )
        return {
            "title": "Insurance Claim Roadmap",
            "response": response,
            "tips": [
                "Always notify the insurer/TPA within 24-48 hours of hospital admission.",
                "Keep duplicate photocopies of all hospital bills and discharge summaries before submission.",
                "Verify non-medical items list (gloves, sanitizers) which are generally non-payable."
            ]
        }

    # 2. How to Choose & Buy Health Insurance Journey
    is_how_to = any(phrase in msg_lower for phrase in [
        "how to take", "how to buy", "steps to take", "steps to buy",
        "how do i buy", "how do i take", "how to choose", "buying insurance",
        "taking health insurance", "guide to buy", "term insurance", "life insurance"
    ])

    if is_how_to:
        response = (
            f"{greeting}Here is the complete step-by-step guide on **How to Choose & Buy Health & Term Insurance**:\n\n"
            "### 1. Determine the Right Sum Insured (Coverage)\n"
            "- **Health Insurance:** Your base cover should be **at least 50% to 100% of your annual household income** (minimum ₹10 to ₹15 Lakhs) to shield against medical inflation.\n"
            "- **Term Life Insurance:** Choose pure term cover of **10x to 15x your annual income** until retirement age (e.g. age 60-65).\n\n"
            "### 2. Choose Policy Structure\n"
            "- **Family Floater:** Cost-effective for young couples and children under a shared sum insured.\n"
            "- **Individual Policy:** Best for senior citizen parents so their higher claim probability doesn't exhaust the family pool.\n\n"
            "### 3. Audit 4 Crucial Policy Clauses\n"
            "- **Room Rent Sub-Limit:** Insist on *'No Room Rent Capping'* or *'Single Private AC Room'*. A 1% room rent cap triggers proportionate deductions across doctor consultations, surgeon fees, and surgical bills.\n"
            "- **Zero Co-Payment:** Choose 0% co-pay so you don't pay 10% to 20% out-of-pocket on every hospital claim.\n"
            "- **Pre-Existing Disease (PED) Waiting Period:** Opt for policies with 1 to 3 years waiting periods (avoid 4-year locks if possible).\n"
            "- **Restoration / Reinstatement Benefit:** Ensure 100% of your sum insured automatically refills if exhausted within a policy year.\n\n"
            "### 4. Check Cashless Hospital Network\n"
            "- Verify premier multi-specialty hospitals near your residence offer direct cashless settlement.\n\n"
            "### 5. 100% Accurate Medical Disclosures\n"
            "- Disclose past surgeries, chronic ailments (diabetes, hypertension, thyroid), and family history. Non-disclosure is the #1 cause of claim rejection."
        )
    else:
        response = (
            f"{greeting}When reviewing an insurance policy, ensure these 4 pillars are fully optimized:\n\n"
            "1. **Coverage Adequacy:** Health cover of ₹10L-₹25L+ and Term Life cover of 10-15x annual income.\n"
            "2. **Room Rent Sub-Limits:** Ensure no room rent capping (e.g. 1% limit) to prevent proportionate deduction.\n"
            "3. **Co-Payment Clauses:** Always aim for 0% co-pay so the insurer covers 100% of eligible expenses.\n"
            "4. **Waiting Periods:** Check 12 to 36 months waiting periods for pre-existing diseases (PED).\n\n"
            "Tip: You can upload your insurance PDF in the Document AI tab to automatically audit for hidden clauses."
        )

    return {
        "title": "Health and Life Insurance Guidance",
        "response": response,
        "tips": [
            "Opt for policies without room rent caps or co-pays.",
            "Disclose all pre-existing medical conditions to prevent claim rejections.",
            "Keep digital copies of hospital bills, discharge summary, and pharmacy receipts.",
            "Check the insurer's network cashless hospital list in your city."
        ]
    }


def loan_response(message, profile=None):
    profile = profile or {}
    numbers = extract_numbers(message)
    calculator = None
    currency_sym = "₹"
    msg_lower = str(message).lower()

    income = float(profile.get("monthly_income", 0.0))
    saving_capacity = float(profile.get("monthly_saving_capacity", 0.0))

    # 1. Numerical Calculation (Principal, Rate, Tenure)
    if len(numbers) >= 3:
        principal = numbers[0]
        rate = numbers[1]
        tenure_raw = numbers[2]
        # If user passes tenure <= 40, assume years unless message mentions months
        if tenure_raw <= 40 and "month" not in msg_lower:
            months = int(tenure_raw * 12)
        else:
            months = int(tenure_raw)

        amortization = calculate_loan_amortization(principal, rate, months)
        emi = amortization["base_emi"]
        total_payment = amortization["total_payment"]
        total_interest = amortization["total_interest"]

        # Affordability check
        affordability_note = ""
        if income > 0:
            foir = (emi / income) * 100
            if foir > 40:
                affordability_note = f"\n\n> ⚠️ **Affordability Alert:** This EMI takes **{foir:.1f}%** of your monthly income ({currency_sym}{income:,.0f}). Lenders prefer total EMIs to stay strictly below 40% of net income (FOIR)."
            else:
                affordability_note = f"\n\n> ✅ **Affordability Check:** This EMI is **{foir:.1f}%** of your monthly income, which is comfortably within safe debt-to-income limits (≤40%)."

        calculator = {
            "principal": round(principal, 2),
            "annual_rate": round(rate, 2),
            "months": months,
            "monthly_emi": emi,
            "total_payment": total_payment,
            "total_interest": total_interest
        }

        response = (
            f"### Loan EMI Breakdown for {currency_sym}{principal:,.0f}\n\n"
            f"- **Monthly EMI:** **{currency_sym}{emi:,.2f}**\n"
            f"- **Total Interest Payable:** {currency_sym}{total_interest:,.2f} ({(total_interest/principal)*100:.1f}% of principal borrowed)\n"
            f"- **Total Amount Repaid:** {currency_sym}{total_payment:,.2f}\n"
            f"- **Tenure:** {months} months ({months/12:.1f} years) @ {rate}% p.a."
            f"{affordability_note}\n\n"
            "💡 *Tip: Visit the Wealth and Debt Hub page for interactive year-by-year Amortization charts and Prepayment simulation.*"
        )

    # 2. How to apply for a loan / Complete Loan Journey
    elif any(phrase in msg_lower for phrase in [
        "how to apply", "how do i apply", "steps to apply", "application process",
        "how to get a loan", "applying for loan", "apply for a loan", "loan procedure", "loan journey"
    ]):
        response = (
            "Here is the complete step-by-step **Loan Application & Planning Journey**:\n\n"
            "### 1. Assess Need & Debt Affordability\n"
            "- Determine the required principal. Ensure your total projected monthly EMIs across all loans do not exceed **40% of your net monthly income** (FOIR - Fixed Obligation to Income Ratio).\n\n"
            "### 2. Check & Optimize Credit Score (CIBIL)\n"
            "- Maintain a credit score of **750 or higher**. A score above 750 qualifies you for lower interest rates, reduced processing fees, and instant loan sanctioning.\n\n"
            "### 3. Compare Lenders & Loan Structures\n"
            "- Compare interest rate types (**Floating vs. Fixed**), Annual Percentage Rates (APR), processing fees (0.5% to 2%), and prepayment terms across banks and NBFCs.\n\n"
            "### 4. Prepare Mandatory Documentation\n"
            "- **Identity & Address Proof:** PAN Card, Aadhaar, Passport, or Voter ID.\n"
            "- **Income Proof:** Last 3-6 months salary slips (salaried) or 2-3 years ITR with computation (self-employed).\n"
            "- **Bank Statements:** Last 6 months bank statements showing salary credits or business cashflows.\n"
            "- **Property / Collateral Papers:** Title deeds, sale agreement, approved builder blueprint (for home/secured loans).\n\n"
            "### 5. Submit Application & Complete Verification\n"
            "- Submit application via digital portal or branch. The lender conducts KYC, field verification, employment verification, and legal/technical valuation.\n\n"
            "### 6. Review Sanction Letter with Document AI\n"
            "- Upon approval, the lender issues a Sanction Letter. Audit interest rate, tenure, penal charges, and reset clauses in FinPath's Document AI before signing.\n\n"
            "### 7. NACH Mandate Registration & Disbursal\n"
            "- Register an electronic NACH auto-debit mandate for monthly EMIs, sign the loan contract, and receive the loan disbursement."
        )

    # 3. How to repay loan faster / Prepayment strategies
    elif any(phrase in msg_lower for phrase in [
        "how to repay", "repay loan faster", "prepayment", "pay off loan",
        "close loan early", "reduce loan tenure", "repayment strategies", "13th emi", "debt avalanche"
    ]):
        response = (
            "Here is the complete playbook to **Repay Your Loan Faster and Slash Compounding Interest**:\n\n"
            "### 1. The 13th EMI Technique\n"
            "- Pay just **1 extra EMI per calendar year** (e.g. from your annual performance bonus). On a 20-year home loan, this single tactic cuts your loan tenure by **4 to 5 full years** and saves substantial interest.\n\n"
            "### 2. 5% to 10% Annual Step-Up EMI\n"
            "- Whenever your annual salary increases, increase your monthly EMI by 5% to 10%. Stepping up EMI by 5% annually reduces a 20-year tenure down to approximately **12 years**.\n\n"
            "### 3. Direct Principal Offset with Lump Sums\n"
            "- Whenever you receive incentives, tax refunds, or maturing investments, make a lump-sum prepayment. Ensure the lender applies the amount to **Principal Reduction** rather than storing it as advance EMI.\n\n"
            "### 4. Always Opt for 'Tenure Reduction'\n"
            "- When making prepayments, instruct your lender to shorten the loan tenure rather than decreasing the monthly EMI. Tenure reduction maximizes compounding interest savings.\n\n"
            "### 5. Debt Avalanche Method (For Multiple Debts)\n"
            "- Pay minimums on all loans, and direct every spare rupee to the loan with the highest interest rate first (Credit Cards > Personal Loans > Auto Loans > Home Loans).\n\n"
            "### 6. Zero Foreclosure Charges (RBI Rule)\n"
            "- Under RBI guidelines, banks cannot levy foreclosure or prepayment penalties on individual floating-rate home loans."
        )

    else:
        response = (
            "When evaluating a loan, consider the total cost of borrowing rather than just the EMI amount.\n\n"
            "**Key rules for smart borrowing:**\n"
            "1. **40% Rule:** Total monthly debt obligations should not exceed 40% of net monthly income.\n"
            "2. **Effective Rate vs Processing Fees:** Always compare the total annual percentage rate (APR) including processing fees and taxes.\n"
            "3. **Prepayment Freedom:** Floating rate home loans carry zero prepayment penalty under RBI rules.\n\n"
            "To calculate a specific loan, include the amount, interest rate, and tenure (e.g. 'Calculate EMI for loan of 1000000 at 8.5% for 120 months')."
        )

    return {
        "title": "Loan and EMI Advisory",
        "response": response,
        "tips": [
            "Avoid tenures longer than necessary; interest compounds rapidly over long periods.",
            "Compare Fixed vs Floating rates depending on the interest rate cycle.",
            "Check for hidden processing, documentation, or legal verification charges.",
            "Maintain a credit score above 750 for best loan terms."
        ],
        "calculator": calculator
    }


def investment_response(message, profile=None):
    numbers = extract_numbers(message)
    profile = profile or {}
    msg_lower = str(message).lower()
    currency_sym = "₹"

    # 1. Numerical SIP Projection
    if len(numbers) >= 3:
        sip_amt = numbers[0]
        rate = numbers[1]
        years = numbers[2]
        step_up = numbers[3] if len(numbers) >= 4 else 0.0

        wealth = calculate_sip_wealth(sip_amt, rate, years, step_up_percent=step_up)

        step_up_str = f" with {step_up}% annual step-up" if step_up > 0 else ""
        response = (
            f"### SIP Wealth Projection for {currency_sym}{sip_amt:,.0f}/month @ {rate}% over {years:.0f} Years{step_up_str}\n\n"
            f"- **Total Amount Invested:** {currency_sym}{wealth['total_invested']:,.2f}\n"
            f"- **Estimated Wealth Gain (Returns):** {currency_sym}{wealth['total_returns']:,.2f}\n"
            f"- **Projected Future Corpus:** **{currency_sym}{wealth['future_value']:,.2f}**\n\n"
            f"📈 **Power of Compounding:** Your wealth gain represents **{(wealth['total_returns']/wealth['total_invested'])*100:.1f}%** profit on top of your invested capital (Wealth multiplier: **{wealth['future_value']/wealth['total_invested']:.2f}x**)."
        )

    # 2. How to start a SIP / Complete Investment Journey
    elif any(phrase in msg_lower for phrase in [
        "how to start a sip", "how to start sip", "how do i start a sip",
        "steps to start sip", "how to invest in sip", "how to invest in mutual funds",
        "starting a sip", "sip guide", "investment journey"
    ]):
        response = (
            "Here is the complete step-by-step **SIP & Wealth Building Investment Journey**:\n\n"
            "### 1. Complete One-Time Mutual Fund KYC\n"
            "- Complete digital e-KYC using your PAN, Aadhaar OTP verification, and bank account proof through an authorized investment portal or fund house (AMC).\n\n"
            "### 2. Define Goal Horizon & Asset Allocation\n"
            "- **Short-Term (< 3 years):** Liquid Funds, Overnight Funds, or Short-Duration Debt Funds.\n"
            "- **Medium-Term (3 to 5 years):** Aggressive Hybrid or Balanced Advantage Funds.\n"
            "- **Long-Term (> 5 years):** Broad Index Funds (Nifty 50) and Flexi-Cap / Mid-Cap Equity Funds for high compounding growth.\n\n"
            "### 3. Always Select 'Direct-Growth' Plans\n"
            "- Choose **Direct Plans** over Regular Plans. Direct plans eliminate distributor commissions, lowering expense ratios by 1% to 1.5% every year and compounding to massive additional wealth over 15-20 years.\n\n"
            "### 4. Schedule Auto-Debit 2-3 Days Post-Salary\n"
            "- Set your monthly SIP auto-debit date **2 to 3 days after your salary credit** so wealth is built automatically before discretionary spending happens.\n\n"
            "### 5. Enable Annual 10% Step-Up SIP\n"
            "- Increasing your SIP by 10% each year with salary hikes more than doubles your 15-year wealth corpus compared to a static SIP.\n\n"
            "### 6. Stay Disciplined Through Market Corrections (Rupee Cost Averaging)\n"
            "- Never pause SIPs during market downturns. Market dips allow your fixed SIP amount to acquire more fund units at discounted NAVs."
        )

    else:
        response = (
            "Before starting investments, follow the financial hierarchy of needs:\n\n"
            "1. **Adequate Life and Health Insurance** (Risk Protection)\n"
            "2. **6-Month Emergency Runway** (Liquidity Buffer in Deposits)\n"
            "3. **Index and Mutual Fund SIPs** (Wealth Creation)\n\n"
            "Try asking: 'How do I start a Systematic Investment Plan (SIP)?' or 'Calculate SIP of 10000 at 12% for 15 years' to see compound projections."
        )

    return {
        "title": "Investment and SIP Compounding",
        "response": response,
        "tips": [
            "Start early to maximize the compounding duration.",
            "Step up your SIP by 10% annually with every salary increment.",
            "Choose Direct-Growth plans to save on commissions.",
            "Diversify across equity (growth) and fixed income (stability)."
        ]
    }


def saving_response(message, profile=None):
    numbers = extract_numbers(message)
    profile = profile or {}
    msg_lower = str(message).lower()

    # 1. How to deposit money / Open an FD / RD
    if any(phrase in msg_lower for phrase in [
        "steps to deposit", "how to deposit", "open fixed deposit", "open fd",
        "steps for fd", "deposit money", "how to open a fixed deposit",
        "how to open an fd", "how to open deposit", "how to save in bank", "open rd", "recurring deposit"
    ]):
        response = (
            "Here is the complete step-by-step guide on **How to Deposit Money & Open Bank Deposits (FD / RD)**:\n\n"
            "### 1. Choose Between Fixed Deposit (FD) vs. Recurring Deposit (RD)\n"
            "- **Fixed Deposit (FD):** Ideal for depositing a one-time lump-sum (**Minimum ₹1,000**) to earn guaranteed interest over 7 days to 10 years.\n"
            "- **Recurring Deposit (RD):** Ideal for monthly disciplined savings (**Minimum ₹500/month**) over 6 months to 10 years.\n\n"
            "### 2. Compare Interest Rates Across Tenures\n"
            "- Peak interest rates are typically offered on tenures of **1 to 3 years** (e.g. 400 or 555-day special buckets). Senior citizens (aged 60+) receive an extra **+0.50% p.a.**\n\n"
            "### 3. Select Interest Payout Frequency\n"
            "- **Cumulative (Reinvestment):** Interest is compounded quarterly and paid at maturity. *Best for compounding.*\n"
            "- **Non-Cumulative (Monthly/Quarterly Payout):** Interest is paid regularly into your savings account. *Best for regular income.*\n\n"
            "### 4. Complete KYC & Open Account\n"
            "- **Existing Customers:** Open in under 60 seconds via Mobile Banking or Net Banking.\n"
            "- **New Customers:** Visit branch or complete video KYC with PAN, Aadhaar, and address proof.\n\n"
            "### 5. Add a Nominee (Mandatory Best Practice)\n"
            "- Register a nominee name and relationship to guarantee smooth transfer of funds to legal heirs.\n\n"
            "### 6. Manage TDS with Form 15G / 15H\n"
            "- Banks deduct 10% TDS if interest earned exceeds ₹40,000/year (₹50,000 for senior citizens). If total taxable income is nil, submit **Form 15G** (or **Form 15H** for seniors) to prevent TDS deduction.\n\n"
            "### 7. DICGC Deposit Safety Guarantee\n"
            "- All bank deposits are insured up to **₹5,00,000** per depositor per bank by DICGC (RBI subsidiary)."
        )

    # 2. Calculating Surplus / Savings Capacity
    elif len(numbers) >= 2:
        num_inc = numbers[0]
        num_exp = numbers[1]
        monthly_sav = num_inc - num_exp
        pct = (monthly_sav / num_inc) * 100 if num_inc > 0 else 0
        response = (
            f"Based on monthly income of ₹{num_inc:,.0f} and expenses of ₹{num_exp:,.0f}:\n\n"
            f"- **Monthly Surplus:** ₹{monthly_sav:,.2f}\n"
            f"- **Savings Rate:** **{pct:.1f}%**\n\n"
            f"A savings rate above 20% is solid. Allocate at least half of this surplus into Systematic Investment Plans (SIPs) and the rest into high-liquidity deposits (FD min ₹1,000, RD min ₹500)."
        )
    else:
        response = (
            "A structured savings roadmap combines stability with inflation-beating growth:\n\n"
            "1. **Emergency Buffer:** Keep 3-6 months expenses in liquid Fixed Deposits (min ₹1,000).\n"
            "2. **Short-Term Goals (< 3 yrs):** Use Recurring Deposits (min ₹500/month) or Short-Term Debt Funds.\n"
            "3. **Long-Term Goals (> 5 yrs):** Invest in diversified index funds and equity SIPs.\n\n"
            "Try asking: 'What are the steps to deposit money in a bank or open an FD?' for complete account setup guidance."
        )

    return {
        "title": "Savings and Deposit Guidance",
        "response": response,
        "tips": [
            "Fixed deposit minimum entry is ₹1,000; recurring deposit minimum entry is ₹500.",
            "Always keep your emergency buffer separate from your daily transactional account.",
            "DICGC insures bank deposits up to ₹5 Lakhs per bank per depositor."
        ]
    }


def budget_response(message, profile=None):
    profile = profile or {}
    income = float(profile.get("monthly_income", 0.0))
    savings = float(profile.get("monthly_saving_capacity", 0.0))
    numbers = extract_numbers(message)

    if numbers and numbers[0] > 1000:
        income = numbers[0]

    budget = calculate_budget_50_30_20(income, savings)

    if income > 0:
        response = (
            f"### 50/30/20 Budgeting Blueprint for Monthly Income: ₹{income:,.0f}\n\n"
            f"1. **Essential Needs (50%) -> ₹{budget['needs_50']:,.0f}:** Rent/EMI, groceries, utilities, basic healthcare, insurance premiums.\n"
            f"2. **Discretionary Wants (30%) -> ₹{budget['wants_30']:,.0f}:** Lifestyle, dining out, entertainment, vacations, and subscriptions.\n"
            f"3. **Savings & Investments (20%) -> ₹{budget['savings_20']:,.0f}:** Emergency fund, SIPs, retirement corpus, and debt reduction.\n\n"
            f"🛡️ **Emergency Fund Target (6 Months Needs):** **₹{budget['emergency_6_months']:,.0f}**\n"
        )
        if savings > 0:
            response += f"At your current saving rate of ₹{savings:,.0f}/month, you will fully build this safety net in **{budget['months_to_build_emergency_fund']} months**."
    else:
        response = (
            "A balanced personal budget follows three main tiers:\n\n"
            "- **50% Needs:** Non-negotiables like rent, groceries, bills, and insurance.\n"
            "- **30% Wants:** Discretionary spending, dining, hobbies, and leisure.\n"
            "- **20% Savings:** Investments, emergency buffer, and wealth building.\n\n"
            "Set your monthly income in the Profile tab to generate your personalized budget map."
        )

    return {
        "title": "Budget and Emergency Fund Roadmap",
        "response": response,
        "tips": [
            "Build a 3 to 6 month emergency fund in liquid deposits before aggressive investing.",
            "Automate transfers to savings on the day your salary is credited.",
            "Review recurring digital subscriptions every quarter."
        ]
    }


def financial_journey_response(message, profile=None):
    profile = profile or {}
    name = profile.get("name", "").strip()
    greeting = f"Hello {name}, " if name else ""
    msg_lower = str(message).lower()

    if "insurance" in msg_lower or "claim" in msg_lower:
        return insurance_response(message, profile)

    if "loan" in msg_lower or "borrow" in msg_lower or "emi" in msg_lower or "prepay" in msg_lower:
        return loan_response(message, profile)

    if "sip" in msg_lower or "invest" in msg_lower or "mutual fund" in msg_lower or "wealth" in msg_lower:
        return investment_response(message, profile)

    if "deposit" in msg_lower or "fd" in msg_lower or "rd" in msg_lower or "save" in msg_lower:
        return saving_response(message, profile)

    # Master Financial Planning Journey Roadmap
    response = (
        f"{greeting}Here is the complete **Master Financial Journey Framework** to achieve lifelong financial freedom:\n\n"
        "### Stage 1: Risk Protection (Foundation)\n"
        "- **Health Insurance:** Secure comprehensive health insurance for yourself and family (₹10L-₹25L cover, 0% co-pay, no room rent sub-limit).\n"
        "- **Term Life Insurance:** Pure term insurance equal to **10-15x annual income** if you have financial dependents.\n\n"
        "### Stage 2: Liquidity Buffer (Emergency Runway)\n"
        "- Build **3 to 6 months of living expenses** in high-liquidity fixed deposits (min ₹1,000) and recurring deposits (min ₹500/month).\n\n"
        "### Stage 3: Debt Optimization\n"
        "- Keep total monthly debt EMIs strictly below **40% of net monthly income**.\n"
        "- Use the **13th EMI rule** and **5-10% annual step-up prepayments** to close home loans in 10-12 years instead of 20 years.\n\n"
        "### Stage 4: Wealth Creation & Compounding (SIP)\n"
        "- Set up **Direct-Growth Equity Mutual Fund SIPs** (Index Funds / Flexi-Cap).\n"
        "- Automate SIPs 2-3 days after monthly salary credit with an **annual 10% Step-Up** to multiply wealth exponentially.\n\n"
        "### Stage 5: Retirement & Milestone Planning\n"
        "- Determine your target retirement corpus using the Rule of 25 (25x annual expenses).\n"
        "- Rebalance asset allocation annually between Equity (growth) and Debt/Fixed Income (capital preservation).\n\n"
        "💡 *You can ask me to dive deeper into any specific financial journey: Loan Planning, Insurance Claims, SIP Compounding, or Bank Deposits!*"
    )

    return {
        "title": "Master Financial Journey Roadmap",
        "response": response,
        "tips": [
            "Follow the sequence: Protect (Insurance) -> Buffer (Emergency Fund) -> Optimize Debt -> Invest & Compound (SIP).",
            "Automate all savings and investments on salary day.",
            "Audit your financial health regularly using FinPath's tools."
        ]
    }


def general_response(message, profile=None):
    profile = profile or {}
    name = profile.get("name", "").strip()
    greeting = f"Welcome {name}! " if name else ""

    return {
        "title": "FinPath AI Financial Assistant",
        "response": (
            f"{greeting}I am your **FinPath Financial Planning Assistant**.\n\n"
            "I can guide you through every stage of your financial journey and perform instant calculations:\n\n"
            "### 1. Loan Planning & Debt Freedom\n"
            "- **How to Apply for a Loan:** Complete application roadmap, CIBIL 750+ guidelines, document checks, and sanction letter audits.\n"
            "- **Prepayment Playbook:** Slash interest with the 13th EMI rule, 5-10% annual step-up, and debt avalanche strategies.\n"
            "- **Instant EMI Calculator:** e.g. *'Calculate EMI for loan of 1000000 at 8.5% for 120 months'*\n\n"
            "### 2. Insurance & Claim Guidance\n"
            "- **How to Choose & Buy Health Insurance:** Room rent sub-limits, 0% co-pay, waiting periods, and network hospitals.\n"
            "- **Insurance Claim Journey:** Step-by-step walkthrough for Cashless Hospitalization & Reimbursement claims.\n\n"
            "### 3. SIP & Wealth Compounding\n"
            "- **How to Start a SIP:** Complete mutual fund guide, Direct-Growth plans, and Rupee Cost Averaging.\n"
            "- **SIP Wealth Calculations:** e.g. *'Calculate SIP of 10000 at 12.5% for 15 years with 10% step up'*\n\n"
            "### 4. Bank Deposits & Savings (FD / RD)\n"
            "- **Fixed Deposits (Min ₹1,000)** & **Recurring Deposits (Min ₹500/month)**: Interest rates, Form 15G/15H TDS rules, and DICGC deposit safety.\n\n"
            "### 5. Comprehensive Financial Journeys\n"
            "- Step-by-step guidance for any milestone: Emergency fund building, buying a home, retirement planning, and tax optimization.\n\n"
            "**What financial topic or calculation would you like to explore today?**"
        ),
        "tips": [
            "Ask any question about loans, insurance, SIPs, deposits, or financial journeys.",
            "Provide figures (e.g. loan 2000000 at 9% for 20 years) for instant mathematical models."
        ]
    }


# ------------------------------------------------------------
# MAIN AI DISPATCHER
# ------------------------------------------------------------

def generate_response(message, profile=None):
    intent = understand_intent(message)

    if intent == "journey":
        result = financial_journey_response(message, profile=profile)
    elif intent == "insurance":
        result = insurance_response(message, profile=profile)
    elif intent == "loan":
        result = loan_response(message, profile=profile)
    elif intent == "budget":
        result = budget_response(message, profile=profile)
    elif intent == "saving":
        result = saving_response(message, profile=profile)
    elif intent == "investment":
        result = investment_response(message, profile=profile)
    else:
        result = general_response(message, profile=profile)

    result["intent"] = intent
    return result