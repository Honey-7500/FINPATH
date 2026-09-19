# ============================================================
# FINPATH - EXECUTIVE PDF REPORT GENERATOR
# ============================================================

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)


# Color Palette
NAVY_PRIMARY = colors.HexColor("#0f2744")
BLUE_ACCENT = colors.HexColor("#007FFF")
BLUE_LIGHT = colors.HexColor("#e0f2fe")
DARK_TEXT = colors.HexColor("#1e293b")
MUTED_TEXT = colors.HexColor("#64748b")
BG_LIGHT = colors.HexColor("#f8fafc")
BG_HEADER = colors.HexColor("#f1f5f9")
GREEN_ACCENT = colors.HexColor("#16a34a")
AMBER_ACCENT = colors.HexColor("#d97706")
BORDER_COLOR = colors.HexColor("#cbd5e1")


def safe_float(val, default=0.0):
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def get_custom_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=NAVY_PRIMARY,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='DocSubTitle',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=MUTED_TEXT,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=NAVY_PRIMARY,
        spaceBefore=8,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=NAVY_PRIMARY,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=DARK_TEXT,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=DARK_TEXT,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='TableCellGreen',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=GREEN_ACCENT,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        name='BadgeText',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=BLUE_ACCENT
    ))

    styles.add(ParagraphStyle(
        name='BodyCustom',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=DARK_TEXT
    ))

    styles.add(ParagraphStyle(
        name='BulletCustom',
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT,
        leftIndent=12
    ))

    styles.add(ParagraphStyle(
        name='FooterNote',
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=MUTED_TEXT,
        alignment=1
    ))

    return styles


def format_currency_amount(amount, currency_code="INR"):
    try:
        val = safe_float(amount)
        if currency_code == "INR":
            return f"INR {val:,.2f}"
        elif currency_code == "USD":
            return f"${val:,.2f}"
        elif currency_code == "EUR":
            return f"EUR {val:,.2f}"
        elif currency_code == "GBP":
            return f"GBP {val:,.2f}"
        else:
            return f"{currency_code} {val:,.2f}"
    except Exception:
        return f"{currency_code} 0.00"


# ============================================================
# 1. EXECUTIVE HEALTH REPORT PDF GENERATOR
# ============================================================

def generate_health_report_pdf(profile_data, loan_data=None, sip_data=None, budget_data=None, currency="INR"):
    """
    Generates a PDF of the user's executive financial health report,
    including profile, monthly income, saving, loan details, budget breakdown, and advisory.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = get_custom_styles()
    story = []

    profile_data = profile_data or {}
    name = str(profile_data.get("name", "")).strip() or "Valued Client"
    income = safe_float(profile_data.get("monthly_income", 0.0))
    savings = safe_float(profile_data.get("monthly_saving_capacity", 0.0))
    savings_rate = (savings / income * 100) if income > 0 else 0.0
    now_str = datetime.now().strftime("%B %d, %Y - %H:%M:%S")

    # Header Title Banner
    story.append(Paragraph("FinPath Executive Financial Health Report", styles['DocTitle']))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        f"Confidential Financial Assessment | Client: <b>{name}</b> | Generated: {now_str} | Base Currency: {currency}",
        styles['DocSubTitle']
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE_ACCENT, spaceBefore=2, spaceAfter=8))

    # SECTION 1: PROFILE & CASHFLOW SNAPSHOT
    story.append(Paragraph("1. Personal Profile & Monthly Cash Flow Snapshot", styles['SectionHeader']))

    age = int(profile_data.get("age", 28) or 28)
    occ = str(profile_data.get("occupation", "Salaried Professional") or "Salaried Professional")
    city = str(profile_data.get("city", "") or "Not Specified")
    goal = str(profile_data.get("primary_goal", "Comprehensive Financial Growth") or "Comprehensive Financial Growth")
    risk = str(profile_data.get("risk_profile", "Moderate (Balanced)") or "Moderate (Balanced)")
    exist_emi = safe_float(profile_data.get("existing_monthly_emi", 0.0))
    health_cov = safe_float(profile_data.get("health_insurance_cover", 0.0))
    term_cov = safe_float(profile_data.get("term_insurance_cover", 0.0))

    profile_rows = [
        [
            Paragraph("Client Name", styles['TableHeader']),
            Paragraph(f"<b>{name}</b> ({age} yrs)", styles['TableCellBold']),
            Paragraph("Occupation / Role", styles['TableHeader']),
            Paragraph(occ, styles['TableCell'])
        ],
        [
            Paragraph("Location / City", styles['TableHeader']),
            Paragraph(city, styles['TableCell']),
            Paragraph("Assessment Date", styles['TableHeader']),
            Paragraph(now_str[:12], styles['TableCell'])
        ],
        [
            Paragraph("Monthly Net Income", styles['TableHeader']),
            Paragraph(format_currency_amount(income, currency), styles['TableCellBold']),
            Paragraph("Monthly Saving Capacity", styles['TableHeader']),
            Paragraph(format_currency_amount(savings, currency), styles['TableCellGreen'])
        ],
        [
            Paragraph("Savings Rate", styles['TableHeader']),
            Paragraph(f"<b>{savings_rate:.1f}%</b> ({'Optimal (>=20%)' if savings_rate >= 20 else 'Needs Attention (<20%)'})", styles['TableCell']),
            Paragraph("Existing Monthly EMIs", styles['TableHeader']),
            Paragraph(format_currency_amount(exist_emi, currency), styles['TableCell'])
        ],
        [
            Paragraph("Primary Milestone", styles['TableHeader']),
            Paragraph(goal, styles['TableCellBold']),
            Paragraph("Risk Profile", styles['TableHeader']),
            Paragraph(risk, styles['TableCell'])
        ],
        [
            Paragraph("Health Insurance Cover", styles['TableHeader']),
            Paragraph(format_currency_amount(health_cov, currency) if health_cov > 0 else "Needs Review", styles['TableCell']),
            Paragraph("Term Life Cover", styles['TableHeader']),
            Paragraph(format_currency_amount(term_cov, currency) if term_cov > 0 else "Needs Review", styles['TableCell'])
        ]
    ]

    t_prof = Table(profile_rows, colWidths=[130, 140, 130, 140])
    t_prof.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), BG_HEADER),
        ('BACKGROUND', (2, 0), (2, -1), BG_HEADER),
    ]))
    story.append(t_prof)
    story.append(Spacer(1, 10))

    # SECTION 2: LOAN & DEBT OBLIGATIONS PROFILE
    story.append(Paragraph("2. Debt Portfolio & Loan Amortization Profile", styles['SectionHeader']))

    loan_data = loan_data or {}
    loan_p = safe_float(loan_data.get("principal", 1000000.0))
    loan_r = safe_float(loan_data.get("rate", 8.75))
    loan_t = safe_float(loan_data.get("tenure_years", 10.0))
    loan_emi = safe_float(loan_data.get("emi", 12532.0))
    loan_tot_int = safe_float(loan_data.get("total_interest", 503840.0))
    loan_tot_pay = safe_float(loan_data.get("total_payment", loan_p + loan_tot_int))

    foir = (loan_emi / income * 100) if income > 0 else 0.0
    foir_status = "Safe (<=40%)" if foir <= 40 else "High Risk (>40%)"

    loan_rows = [
        [
            Paragraph("Modeled Loan Principal", styles['TableHeader']),
            Paragraph(format_currency_amount(loan_p, currency), styles['TableCellBold']),
            Paragraph("Interest Rate (p.a.)", styles['TableHeader']),
            Paragraph(f"{loan_r:.2f}% (Reducing Balance)", styles['TableCell'])
        ],
        [
            Paragraph("Loan Tenure", styles['TableHeader']),
            Paragraph(f"{loan_t:.1f} Years ({int(loan_t*12)} Months)", styles['TableCell']),
            Paragraph("Monthly Loan EMI", styles['TableHeader']),
            Paragraph(format_currency_amount(loan_emi, currency), styles['TableCellBold'])
        ],
        [
            Paragraph("Total Interest Payable", styles['TableHeader']),
            Paragraph(format_currency_amount(loan_tot_int, currency), styles['TableCell']),
            Paragraph("Total Repayment", styles['TableHeader']),
            Paragraph(format_currency_amount(loan_tot_pay, currency), styles['TableCell'])
        ],
        [
            Paragraph("Debt-to-Income (FOIR)", styles['TableHeader']),
            Paragraph(f"<b>{foir:.1f}%</b> ({foir_status})", styles['TableCellBold'] if foir <= 40 else styles['TableCell']),
            Paragraph("Prepayment Guideline", styles['TableHeader']),
            Paragraph("13th EMI / 5% Step-Up cuts tenure by ~4.5 yrs", styles['TableCell'])
        ]
    ]

    t_loan = Table(loan_rows, colWidths=[130, 140, 130, 140])
    t_loan.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), BG_HEADER),
        ('BACKGROUND', (2, 0), (2, -1), BG_HEADER),
    ]))
    story.append(t_loan)
    story.append(Spacer(1, 10))

    # SECTION 3: 50/30/20 BUDGETING BLUEPRINT & EMERGENCY BUFFER
    story.append(Paragraph("3. 50/30/20 Budget Blueprint & Safety Net Runway", styles['SectionHeader']))

    needs_50 = income * 0.50
    wants_30 = income * 0.30
    savings_20 = income * 0.20
    emer_3mo = needs_50 * 3
    emer_6mo = needs_50 * 6

    budget_rows = [
        [
            Paragraph("Essential Needs (50%)", styles['TableHeader']),
            Paragraph(format_currency_amount(needs_50, currency), styles['TableCellBold']),
            Paragraph("Discretionary Wants (30%)", styles['TableHeader']),
            Paragraph(format_currency_amount(wants_30, currency), styles['TableCell'])
        ],
        [
            Paragraph("Target Savings (20%)", styles['TableHeader']),
            Paragraph(format_currency_amount(savings_20, currency), styles['TableCellBold']),
            Paragraph("Actual Monthly Savings", styles['TableHeader']),
            Paragraph(format_currency_amount(savings, currency), styles['TableCellGreen'])
        ],
        [
            Paragraph("3-Month Emergency Fund", styles['TableHeader']),
            Paragraph(format_currency_amount(emer_3mo, currency), styles['TableCell']),
            Paragraph("6-Month Target Safety Net", styles['TableHeader']),
            Paragraph(format_currency_amount(emer_6mo, currency), styles['TableCellBold'])
        ]
    ]

    t_bud = Table(budget_rows, colWidths=[130, 140, 130, 140])
    t_bud.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), BG_HEADER),
        ('BACKGROUND', (2, 0), (2, -1), BG_HEADER),
    ]))
    story.append(t_bud)
    story.append(Spacer(1, 10))

    # SECTION 4: WEALTH COMPOUNDING & SIP OUTLOOK
    story.append(Paragraph("4. Systematic Investment Plan (SIP) Compounding Outlook", styles['SectionHeader']))

    sip_data = sip_data or {}
    sip_m = safe_float(sip_data.get("monthly_sip", min(savings, 10000.0) if savings > 0 else 5000.0))
    sip_r = safe_float(sip_data.get("expected_return", 12.5))
    sip_y = safe_float(sip_data.get("years", 15.0))

    # Simple future value
    total_inv_calc = sip_m * 12 * sip_y
    m_rate = (sip_r / 100.0) / 12.0
    tot_months = int(sip_y * 12)
    fv_calc = sip_m * (((1 + m_rate)**tot_months - 1) / m_rate) * (1 + m_rate) if m_rate > 0 else total_inv_calc
    returns_calc = max(0.0, fv_calc - total_inv_calc)

    sip_rows = [
        [
            Paragraph("Monthly SIP Allocation", styles['TableHeader']),
            Paragraph(format_currency_amount(sip_m, currency), styles['TableCellBold']),
            Paragraph("Expected Annual Return", styles['TableHeader']),
            Paragraph(f"{sip_r:.1f}% (Direct Equity Index)", styles['TableCell'])
        ],
        [
            Paragraph("Investment Horizon", styles['TableHeader']),
            Paragraph(f"{sip_y:.0f} Years ({tot_months} instalments)", styles['TableCell']),
            Paragraph("Total Capital Invested", styles['TableHeader']),
            Paragraph(format_currency_amount(total_inv_calc, currency), styles['TableCell'])
        ],
        [
            Paragraph("Estimated Wealth Gain", styles['TableHeader']),
            Paragraph(format_currency_amount(returns_calc, currency), styles['TableCellGreen']),
            Paragraph("Projected Future Corpus", styles['TableHeader']),
            Paragraph(format_currency_amount(fv_calc, currency), styles['TableCellBold'])
        ]
    ]

    t_sip = Table(sip_rows, colWidths=[130, 140, 130, 140])
    t_sip.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), BG_HEADER),
        ('BACKGROUND', (2, 0), (2, -1), BG_HEADER),
    ]))
    story.append(t_sip)
    story.append(Spacer(1, 10))

    # SECTION 5: EXECUTIVE ADVISORY & STRATEGIC RECOMMENDATIONS
    story.append(Paragraph("5. Strategic Financial Health Recommendations", styles['SectionHeader']))
    story.append(Paragraph("• <b>Risk Protection First:</b> Secure base health cover of INR 10-25 Lakhs (0% co-pay, no room rent sub-limit) and 10-15x term life cover before aggressive investing.", styles['BulletCustom']))
    story.append(Paragraph(f"• <b>Build Liquid Emergency Buffer:</b> Target <b>{format_currency_amount(emer_6mo, currency)}</b> in fixed deposits (min INR 1,000) or recurring deposits (min INR 500/mo).", styles['BulletCustom']))
    story.append(Paragraph("• <b>Accelerate Debt Freedom:</b> Apply the 13th EMI rule and 5% annual step-up prepayment to eliminate loan interest.", styles['BulletCustom']))
    story.append(Paragraph("• <b>Compounding Discipline:</b> Automate direct-growth mutual fund SIPs 2-3 days post-salary with a 10% annual step-up.", styles['BulletCustom']))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=4, spaceAfter=6))
    story.append(Paragraph("Report generated securely by FinPath Financial Planning Engine. All rights reserved.", styles['FooterNote']))

    doc.build(story)
    return buffer.getvalue()


# ============================================================
# 2. FULL FINANCIAL REPORT CARD & ACTIVITY TIMELINE PDF
# ============================================================

def generate_report_card_with_timeline_pdf(profile_data, activities, journey_data=None, currency="INR"):
    """
    Generates a PDF of the user's Full Financial Report Card,
    including complete chronological activity history, timestamps, module details,
    journey milestones, and overall financial grade.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = get_custom_styles()
    story = []

    profile_data = profile_data or {}
    name = str(profile_data.get("name", "")).strip() or "Valued Client"
    income = safe_float(profile_data.get("monthly_income", 0.0))
    savings = safe_float(profile_data.get("monthly_saving_capacity", 0.0))
    now_str = datetime.now().strftime("%B %d, %Y - %H:%M:%S")

    journey_data = journey_data or {}
    action = journey_data.get("action", "Comprehensive Financial Planning")
    docs = journey_data.get("documents", {})
    total_docs = len(docs)
    avail_docs = sum(1 for v in docs.values() if v)
    readiness = int((avail_docs / total_docs * 100)) if total_docs > 0 else 0

    activities = activities or []
    if not activities:
        activities = [
            {
                "timestamp": now_str[:19],
                "category": "Session Initiation",
                "action": "Initialized FinPath Financial Planning Workspace",
                "details": f"Configured workspace for {name}"
            }
        ]

    # Title Banner
    story.append(Paragraph("FinPath Full Financial Report Card & Activity Audit", styles['DocTitle']))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        f"Complete Interaction Audit & Financial Milestone Summary | Client: <b>{name}</b> | Generated: {now_str}",
        styles['DocSubTitle']
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY_PRIMARY, spaceBefore=2, spaceAfter=8))

    # SECTION 1: EXECUTIVE FINANCIAL POSITION & SCORECARD
    story.append(Paragraph("1. Executive Financial Position & Milestone Grade", styles['SectionHeader']))

    if income > 0:
        ratio = savings / income
        if ratio >= 0.25 and readiness >= 80:
            grade = "A+ (Excellent)"
        elif ratio >= 0.20 or readiness >= 60:
            grade = "A (Strong)"
        else:
            grade = "B (Active Planning)"
    else:
        grade = "Pending Profile Setup"

    age = int(profile_data.get("age", 28) or 28)
    occ = str(profile_data.get("occupation", "Salaried Professional") or "Salaried Professional")
    goal = str(profile_data.get("primary_goal", action) or action)
    risk = str(profile_data.get("risk_profile", "Moderate (Balanced)") or "Moderate (Balanced)")
    exist_invest = safe_float(profile_data.get("existing_investments", 0.0))
    emer_fund = safe_float(profile_data.get("emergency_fund", 0.0))

    score_rows = [
        [
            Paragraph("Client Name", styles['TableHeader']),
            Paragraph(f"<b>{name}</b> ({age} yrs, {occ[:22]})", styles['TableCellBold']),
            Paragraph("Overall Health Grade", styles['TableHeader']),
            Paragraph(f"<b>{grade}</b>", styles['TableCellGreen'])
        ],
        [
            Paragraph("Monthly Net Income", styles['TableHeader']),
            Paragraph(format_currency_amount(income, currency), styles['TableCellBold']),
            Paragraph("Monthly Saving Capacity", styles['TableHeader']),
            Paragraph(format_currency_amount(savings, currency), styles['TableCellGreen'])
        ],
        [
            Paragraph("Existing Investments", styles['TableHeader']),
            Paragraph(format_currency_amount(exist_invest, currency) if exist_invest > 0 else "Baseline Setup", styles['TableCell']),
            Paragraph("Emergency Reserve Buffer", styles['TableHeader']),
            Paragraph(format_currency_amount(emer_fund, currency) if emer_fund > 0 else "To be created", styles['TableCell'])
        ],
        [
            Paragraph("Active Financial Goal", styles['TableHeader']),
            Paragraph(goal, styles['TableCellBold']),
            Paragraph("Risk Profile", styles['TableHeader']),
            Paragraph(risk, styles['TableCell'])
        ],
        [
            Paragraph("Total Activities Logged", styles['TableHeader']),
            Paragraph(f"<b>{len(activities)} interaction(s)</b>", styles['TableCellBold']),
            Paragraph("Document Readiness", styles['TableHeader']),
            Paragraph(f"{readiness}% ({avail_docs}/{total_docs} verified)" if total_docs > 0 else "In Progress", styles['TableCell'])
        ]
    ]

    t_score = Table(score_rows, colWidths=[130, 140, 130, 140])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), BG_HEADER),
        ('BACKGROUND', (2, 0), (2, -1), BG_HEADER),
    ]))
    story.append(t_score)
    story.append(Spacer(1, 12))

    # SECTION 2: CHRONOLOGICAL ACTIVITY AUDIT TIMELINE TABLE
    story.append(Paragraph(f"2. Complete Chronological Site Activity Timeline ({len(activities)} Records)", styles['SectionHeader']))
    story.append(Paragraph("A complete log of every financial model, document audit, journey milestone, and planning activity performed in FinPath.", styles['BodyCustom']))
    story.append(Spacer(1, 6))

    timeline_table_data = [
        [
            Paragraph("Date & Time", styles['TableHeader']),
            Paragraph("Module / Domain", styles['TableHeader']),
            Paragraph("Activity & Operation", styles['TableHeader']),
            Paragraph("Impact / Outcome Details", styles['TableHeader'])
        ]
    ]

    for act in reversed(activities[-35:]):  # up to last 35 activities
        ts = str(act.get("timestamp", ""))
        cat = str(act.get("category", "General"))
        act_desc = str(act.get("action", ""))
        det = str(act.get("details", ""))

        timeline_table_data.append([
            Paragraph(ts, styles['TableCell']),
            Paragraph(f"<b>{cat}</b>", styles['BadgeText']),
            Paragraph(act_desc, styles['TableCellBold']),
            Paragraph(det or "Operation completed successfully", styles['TableCell'])
        ])

    t_timeline = Table(timeline_table_data, colWidths=[90, 110, 175, 165])
    t_timeline.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_HEADER),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_timeline)
    story.append(Spacer(1, 12))

    # SECTION 3: JOURNEY CHECKLIST AUDIT (IF ANY)
    if docs:
        story.append(Paragraph(f"3. Journey Twin Verification Audit: {action}", styles['SectionHeader']))
        doc_rows = [[Paragraph("Required Document", styles['TableHeader']), Paragraph("Verification Status", styles['TableHeader'])]]
        for doc_name, is_done in docs.items():
            clean = doc_name.replace(f"{action}_", "")
            status_p = Paragraph("<font color='#16a34a'><b>Verified / Ready</b></font>" if is_done else "<font color='#dc2626'>Pending Collection</font>", styles['TableCell'])
            doc_rows.append([Paragraph(clean, styles['TableCell']), status_p])

        t_docs = Table(doc_rows, colWidths=[320, 220])
        t_docs.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_HEADER),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('PADDING', (0, 0), (-1, -1), 4.5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_docs)
        story.append(Spacer(1, 10))

    # SECTION 4: STRATEGIC NEXT STEPS
    story.append(Paragraph("4. Recommended Financial Action Steps", styles['SectionHeader']))
    story.append(Paragraph("1. <b>Maintain Regular Tracking:</b> Update income and savings capacity quarterly to keep amortization models accurate.", styles['BulletCustom']))
    story.append(Paragraph("2. <b>Review Policy Fine-Print:</b> Audit all insurance contracts annually with Document AI to detect hidden sub-limits.", styles['BulletCustom']))
    story.append(Paragraph("3. <b>Execute Compounding Goals:</b> Maintain monthly SIP auto-debits and set automatic annual step-up reminders.", styles['BulletCustom']))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=4, spaceAfter=6))
    story.append(Paragraph(f"Official FinPath User Report Card | Exported on {now_str} | ID: FP-AUDIT-{datetime.now().strftime('%Y%m%d%H%M')}", styles['FooterNote']))

    doc.build(story)
    return buffer.getvalue()
