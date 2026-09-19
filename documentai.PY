# ============================================================
# FINPATH - SMART DOCUMENT AI & POLICY AUDITOR
# ============================================================

import io
import re
from pathlib import Path

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    PdfReader = None
    PdfReadError = Exception


# ------------------------------------------------------------
# TEXT EXTRACTION FROM PDF OR BYTES
# ------------------------------------------------------------

def extract_pdf_text(source):
    """
    Extract readable text from PDF bytes, a file path, or file-like object.
    """
    if source is None:
        return ""

    if not PdfReader:
        raise ValueError("pypdf library is not installed. Run 'pip install pypdf'.")

    try:
        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if path_obj.is_file():
                with open(path_obj, "rb") as f:
                    pdf_file = io.BytesIO(f.read())
            else:
                # If it's a string that is not a file, it might be raw text
                return str(source)
        elif isinstance(source, bytes):
            pdf_file = io.BytesIO(source)
        elif hasattr(source, "read"):
            content = source.read()
            if isinstance(content, str):
                return content
            pdf_file = io.BytesIO(content)
        else:
            return str(source)

        reader = PdfReader(pdf_file)
        pages = []

        for page in reader.pages:
            try:
                text = page.extract_text()
                if text:
                    cleaned = text.strip()
                    if cleaned:
                        pages.append(cleaned)
            except Exception:
                continue

        return "\n\n".join(pages)

    except PdfReadError:
        raise ValueError("The uploaded file is not a valid or readable PDF.")
    except Exception as error:
        raise ValueError(f"Unable to read the document: {error}")


# ------------------------------------------------------------
# CLEAN & NORMALIZE TEXT
# ------------------------------------------------------------

def clean_text(text):
    """
    Remove unnecessary spaces, excessive whitespace, and blank lines.
    """
    if not text:
        return ""

    lines = []
    for line in str(text).splitlines():
        cleaned_line = " ".join(line.split())
        if cleaned_line:
            lines.append(cleaned_line)

    return "\n".join(lines)


# ------------------------------------------------------------
# FINANCIAL ENTITY EXTRACTION
# ------------------------------------------------------------

def extract_financial_entities(text):
    """
    Extract key financial figures, percentages, dates, and identifiers.
    """
    if not text:
        return {}

    entities = {
        "amounts": [],
        "interest_rates": [],
        "dates": [],
        "policy_loan_numbers": [],
        "tenures": []
    }

    # 1. Amounts (e.g. ₹50,000, Rs. 1,00,000, $5,000, 250000)
    amount_patterns = [
        r"(?:₹|Rs\.?|INR|\$|€|£)\s*(\d+(?:,\d{2,3})*(?:\.\d{1,2})?)",
        r"(\d+(?:,\d{2,3})+(?:\.\d{1,2})?)\s*(?:INR|rupees|dollars|lakh|crore)?",
        r"(?:sum assured|principal|loan amount|premium|sanctioned amount|balance)[\s:]+(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:,\d{2,3})*(?:\.\d{1,2})?)"
    ]
    seen_amounts = set()
    for pattern in amount_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw_val = match.group(1) if match.groups() else match.group(0)
            clean_num = raw_val.replace(",", "")
            try:
                val = float(clean_num)
                if val >= 100 and val not in seen_amounts:
                    seen_amounts.add(val)
                    entities["amounts"].append(f"{val:,.2f}")
            except Exception:
                continue

    # Limit to top distinct amounts
    entities["amounts"] = entities["amounts"][:8]

    # 2. Interest / Percentage Rates (e.g. 8.5%, 10.25% p.a., 6% per annum)
    rate_patterns = [
        r"(\d+(?:\.\d{1,2})?)\s*%\s*(?:p\.?a\.?|per annum|interest|annual)?",
        r"(?:rate of interest|roi|interest rate)[\s:]+(\d+(?:\.\d{1,2})?)\s*%"
    ]
    seen_rates = set()
    for pattern in rate_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = match.group(1)
            try:
                num = float(val)
                if 0.1 <= num <= 50.0 and val not in seen_rates:
                    seen_rates.add(val)
                    entities["interest_rates"].append(f"{val}%")
            except Exception:
                continue
    entities["interest_rates"] = entities["interest_rates"][:5]

    # 3. Dates (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, Month DD, YYYY)
    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b"
    ]
    seen_dates = set()
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            d = match.group(0).strip()
            if d not in seen_dates:
                seen_dates.add(d)
                entities["dates"].append(d)
    entities["dates"] = entities["dates"][:6]

    # 4. Policy / Loan / Account Reference Numbers
    ref_patterns = [
        r"(?:policy|loan|account|sanction|claim|lan|reference|pan|aadhaar)\s*(?:no\.?|number|id|#)?[\s:]+([A-Z0-9\-_]{6,25})",
        r"\b[A-Z]{3,5}\d{5,12}\b"
    ]
    seen_refs = set()
    for pattern in ref_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            ref = match.group(1) if match.groups() else match.group(0)
            ref = ref.strip()
            if len(ref) >= 6 and ref.isalnum() and not ref.isnumeric() and ref not in seen_refs:
                seen_refs.add(ref)
                entities["policy_loan_numbers"].append(ref)
    entities["policy_loan_numbers"] = entities["policy_loan_numbers"][:4]

    # 5. Tenure / Durations (e.g. 60 months, 5 years, 36 months)
    tenure_matches = re.findall(r"\b(\d+)\s*(months|years|days|tenure)\b", text, re.IGNORECASE)
    seen_tenures = set()
    for num, unit in tenure_matches:
        t_str = f"{num} {unit.capitalize()}"
        if t_str not in seen_tenures:
            seen_tenures.add(t_str)
            entities["tenures"].append(t_str)
    entities["tenures"] = entities["tenures"][:4]

    return entities


# ------------------------------------------------------------
# DOCUMENT CLASSIFIER
# ------------------------------------------------------------

def classify_document(text):
    """
    Classify the uploaded document type and identify corresponding Journey Twin action.
    """
    lower = text.lower()

    scores = {
        "Health Insurance Policy / Claim": 0,
        "Loan Sanction / Agreement": 0,
        "Bank Deposit / Fixed Deposit Certificate": 0,
        "Salary Slip / Income Proof": 0,
        "Identity / KYC Document": 0
    }

    # Insurance scoring
    if any(k in lower for k in ["insurance", "policyholder", "sum insured", "sum assured", "tpa", "cashless", "mediclaim", "hospitalization", "coverage details"]):
        scores["Health Insurance Policy / Claim"] += 4
    if any(k in lower for k in ["premium", "copay", "co-payment", "exclusion", "deductible"]):
        scores["Health Insurance Policy / Claim"] += 2

    # Loan scoring
    if any(k in lower for k in ["sanction letter", "loan agreement", "borrower", "lender", "emi amount", "disbursement", "repayment schedule", "principal sum"]):
        scores["Loan Sanction / Agreement"] += 4
    if any(k in lower for k in ["interest rate", "tenure", "hypothecation", "collateral", "foreclosure"]):
        scores["Loan Sanction / Agreement"] += 2

    # Deposit scoring
    if any(k in lower for k in ["fixed deposit", "term deposit", "recurring deposit", "fd receipt", "maturity value", "deposit advice"]):
        scores["Bank Deposit / Fixed Deposit Certificate"] += 5

    # Salary slip
    if any(k in lower for k in ["payslip", "salary slip", "earnings", "gross pay", "net pay", "provident fund", "deductions", "basic pay"]):
        scores["Salary Slip / Income Proof"] += 5

    # Identity / KYC
    if any(k in lower for k in ["income tax department", "permanent account number", "pan card", "unique identification authority", "aadhaar", "passport", "election commission", "voter id"]):
        scores["Identity / KYC Document"] += 5

    best_doc = max(scores, key=scores.get)
    if scores[best_doc] == 0:
        return "General Financial Document", "Select an action"

    action_map = {
        "Health Insurance Policy / Claim": "Buy Health Insurance",
        "Loan Sanction / Agreement": "Apply for a Loan",
        "Bank Deposit / Fixed Deposit Certificate": "Open a Bank Deposit",
        "Salary Slip / Income Proof": "Apply for a Loan",
        "Identity / KYC Document": "Open a Bank Deposit"
    }

    return best_doc, action_map.get(best_doc, "Select an action")


# ------------------------------------------------------------
# RED FLAG & RISK AUDITOR
# ------------------------------------------------------------

def audit_clauses_and_red_flags(text):
    """
    Inspect document text for hidden clauses, restrictive conditions, and critical red flags.
    """
    if not text:
        return []

    lower = text.lower()
    flags = []

    # 1. Co-payment clause
    if "co-payment" in lower or "copay" in lower or "co payment" in lower:
        flags.append({
            "type": "warning",
            "category": "Co-Payment Clause",
            "title": "Co-Payment Requirement Detected",
            "detail": "This policy requires you to bear a percentage of every claim out-of-pocket before the insurer pays."
        })

    # 2. Room rent sub-limits
    if any(k in lower for k in ["room rent sub-limit", "room rent limit", "1% of sum insured", "capping on room"]):
        flags.append({
            "type": "warning",
            "category": "Room Rent Sub-Limit",
            "title": "Room Rent Sub-Limit / Cap Present",
            "detail": "Hospital room rent may be capped (e.g. 1% of Sum Insured). Exceeding this triggers proportionate deductions on all doctor/procedure charges."
        })

    # 3. Pre-existing disease waiting period
    if any(k in lower for k in ["waiting period", "pre-existing disease", "ped waiting", "24 months", "36 months", "48 months"]):
        flags.append({
            "type": "info",
            "category": "Waiting Period",
            "title": "Pre-Existing Disease (PED) Waiting Period",
            "detail": "Coverage for pre-existing illnesses or specific procedures will be locked for the specified waiting duration (often 12-36 months)."
        })

    # 4. Prepayment / Foreclosure penalty
    if any(k in lower for k in ["prepayment charge", "foreclosure penalty", "pre-closure fee", "foreclosure charge"]):
        flags.append({
            "type": "warning",
            "category": "Foreclosure Fee",
            "title": "Prepayment / Foreclosure Penalty",
            "detail": "Prepaying this loan ahead of schedule may attract penalty fees (usually 2% to 4% on outstanding principal)."
        })

    # 5. Premature withdrawal penalty for deposits
    if any(k in lower for k in ["premature withdrawal", "penalty on early closure", "early withdrawal fee"]):
        flags.append({
            "type": "info",
            "category": "Premature Withdrawal",
            "title": "Premature Withdrawal Penalty",
            "detail": "Closing this deposit prior to maturity will reduce the effective interest rate by 0.5% - 1.0%."
        })

    # 6. Default / Late Payment Interest
    if any(k in lower for k in ["penal interest", "late payment fee", "default interest", "bounce charge"]):
        flags.append({
            "type": "danger",
            "category": "Penal Interest",
            "title": "Default Penal Interest & Bounce Charges",
            "detail": "Overdue payments or missed EMIs will incur additional penal interest rates (often 24% - 36% p.a.) and NACH bounce charges."
        })

    # 7. Exclusions / Non-covered items
    if any(k in lower for k in ["permanent exclusions", "not payable", "excluded treatments", "non-medical expenses"]):
        flags.append({
            "type": "info",
            "category": "Policy Exclusions",
            "title": "Specific Exclusions Apply",
            "detail": "Certain treatments, consumables, cosmetic procedures, or experimental therapies are excluded from claim settlement."
        })

    return flags


# ------------------------------------------------------------
# KEYWORDS EXTRACTION
# ------------------------------------------------------------

def find_keywords(text):
    """
    Find financial keywords present in the document.
    """
    if not text:
        return []

    keywords = [
        "premium", "claim", "coverage", "policy", "interest", "emi",
        "loan", "maturity", "sum assured", "principal", "tenure", "renewal",
        "refund", "hospital", "diagnosis", "treatment", "nominee", "insurer",
        "repayment", "co-payment", "deductible", "foreclosure", "pan", "kyc",
        "sanction", "collateral", "disbursement", "sub-limit"
    ]

    lower_text = text.lower()
    found_keywords = []

    for keyword in keywords:
        if keyword in lower_text:
            found_keywords.append(keyword.title())

    return list(set(found_keywords))


# ------------------------------------------------------------
# CHECKLIST MATCHING FOR JOURNEY TWIN
# ------------------------------------------------------------

def match_journey_documents(classified_type, text):
    """
    Returns list of standard Journey Twin document names verified by this document.
    """
    lower = text.lower()
    matched = []

    if "Identity / KYC" in classified_type or any(k in lower for k in ["pan", "aadhaar", "passport", "voter"]):
        matched.append("Identity proof")
        matched.append("PAN or applicable tax identification")
        matched.append("Tax identification")

    if any(k in lower for k in ["address", "residence", "utility bill", "electricity bill", "aadhaar"]):
        matched.append("Address proof")

    if "Salary Slip" in classified_type or any(k in lower for k in ["salary slip", "payslip", "form 16", "gross salary"]):
        matched.append("Recent salary slips or income proof")
        matched.append("Income proof")
        matched.append("Income proof, if financing is used")

    if any(k in lower for k in ["bank statement", "account statement", "closing balance", "transaction history"]):
        matched.append("Recent bank statements")
        matched.append("Bank statements")
        matched.append("Bank account details")

    if "Health Insurance" in classified_type:
        matched.append("Existing insurance policy documents")
        matched.append("Existing insurance details")

    if "Loan Sanction" in classified_type:
        matched.append("Loan or financing documents, if applicable")
        matched.append("Existing loan statements")

    return list(set(matched))


# ------------------------------------------------------------
# GENERATE DETAILED DOCUMENT SUMMARY
# ------------------------------------------------------------

def generate_summary(text, lines, doc_type, entities, flags):
    """
    Generate an intelligent, human-readable executive summary.
    """
    if not text:
        return "No readable text was found in this document."

    summary_parts = [
        f"**Document Classified As:** {doc_type}.",
        f"**Content Scope:** {len(lines)} lines, {len(text):,} readable characters."
    ]

    if entities.get("amounts"):
        summary_parts.append(f"**Key Financial Amounts Identified:** {', '.join(entities['amounts'][:3])}.")

    if entities.get("interest_rates"):
        summary_parts.append(f"**Stated Rates / Percentage Values:** {', '.join(entities['interest_rates'])}.")

    if entities.get("dates"):
        summary_parts.append(f"**Relevant Dates:** {', '.join(entities['dates'][:3])}.")

    if flags:
        summary_parts.append(f"**Critical Clause Alerts:** {len(flags)} important conditions/flags flagged for your review.")
    else:
        summary_parts.append("**Clause Safety Check:** No high-risk restrictive clauses detected on immediate scan.")

    return "\n\n".join(summary_parts)


# ------------------------------------------------------------
# MAIN ANALYZE DOCUMENT FUNCTION
# ------------------------------------------------------------

def analyze_document(source):
    """
    Main entry point: accepts PDF bytes, file path, file object, or raw text.
    Returns comprehensive analysis including classification, entities, red flags, and keywords.
    """
    if not source:
        return {
            "success": False,
            "document_type": "Unknown",
            "summary": "No document content provided.",
            "key_points": [],
            "keywords": [],
            "entities": {},
            "red_flags": [],
            "matched_checklist_items": [],
            "characters": 0,
            "lines": 0
        }

    # Extract text if source is a file/bytes/Path
    try:
        if isinstance(source, (bytes, io.BytesIO)) or (isinstance(source, (str, Path)) and (Path(str(source)).is_file() or str(source).lower().endswith(".pdf"))):
            raw_text = extract_pdf_text(source)
        else:
            raw_text = str(source)
    except Exception as e:
        raw_text = str(source)

    cleaned_text = clean_text(raw_text)

    if not cleaned_text:
        return {
            "success": False,
            "document_type": "Unreadable Document",
            "summary": "No readable text could be extracted. The document may be scanned image-only or password protected.",
            "key_points": [],
            "keywords": [],
            "entities": {},
            "red_flags": [],
            "matched_checklist_items": [],
            "characters": 0,
            "lines": 0
        }

    lines = cleaned_text.splitlines()
    doc_type, recommended_journey = classify_document(cleaned_text)
    entities = extract_financial_entities(cleaned_text)
    flags = audit_clauses_and_red_flags(cleaned_text)
    keywords = find_keywords(cleaned_text)
    matched_checklist = match_journey_documents(doc_type, cleaned_text)
    summary = generate_summary(cleaned_text, lines, doc_type, entities, flags)

    # Key highlight points (first 10 non-empty descriptive lines)
    key_points = [line for line in lines if len(line) > 15][:10]

    return {
        "success": True,
        "document_type": doc_type,
        "recommended_journey": recommended_journey,
        "summary": summary,
        "key_points": key_points,
        "keywords": keywords,
        "entities": entities,
        "red_flags": flags,
        "matched_checklist_items": matched_checklist,
        "characters": len(cleaned_text),
        "lines": len(lines),
        "raw_text_snippet": cleaned_text[:1200]
    }
