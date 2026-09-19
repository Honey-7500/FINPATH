from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
import traceback
import uuid
import json

try:
    from aiengine import (
        generate_response,
        calculate_loan_amortization,
        calculate_budget_50_30_20,
        calculate_sip_wealth
    )
except Exception:
    generate_response = None
    calculate_loan_amortization = None
    calculate_budget_50_30_20 = None
    calculate_sip_wealth = None

try:
    from documentai import analyze_document
except Exception:
    analyze_document = None


app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Persistent storage for backend memory
BACKEND_STORAGE_FILE = Path("finpath_backend_storage.json")

def load_backend_data():
    if BACKEND_STORAGE_FILE.exists():
        try:
            with open(BACKEND_STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("profiles", {}), data.get("server_journeys", {})
        except Exception as e:
            print(f"[FinPath Backend] Error loading storage: {e}")
    return {}, {}

def save_backend_data():
    try:
        with open(BACKEND_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "profiles": profiles,
                "server_journeys": server_journeys
            }, f, indent=2)
    except Exception as e:
        print(f"[FinPath Backend] Error saving storage: {e}")

profiles, server_journeys = load_backend_data()


# ============================================================
# RESPONSE HELPERS
# ============================================================

def success_response(data=None, message="Success"):
    result = {
        "success": True,
        "message": message
    }

    if data is not None:
        result["data"] = data

    return jsonify(result), 200


def error_response(message, status_code=400, details=None):
    result = {
        "success": False,
        "message": message
    }

    if details:
        result["details"] = details

    return jsonify(result), status_code


def get_request_data():
    return request.get_json(silent=True) or {}


def get_user_id(data=None):
    data = data or {}

    user_id = (
        data.get("user_id")
        or request.args.get("user_id")
        or request.headers.get("X-User-ID")
        or "browser-user"
    )

    return str(user_id)


# ============================================================
# BASIC ROUTES
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "application": "FinPath",
        "message": "FinPath backend is running",
        "endpoints": [
            "/health",
            "/chat",
            "/profile",
            "/journey/start",
            "/journey/status",
            "/journey/complete",
            "/journey/reset",
            "/document"
        ]
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "online",
        "service": "FinPath API"
    })


# ============================================================
# PROFILE ROUTES
# ============================================================

@app.route("/profile", methods=["GET"])
def get_profile():
    user_id = get_user_id()

    profile = profiles.get(
        user_id,
        {
            "name": "",
            "email": "",
            "monthly_income": "",
            "primary_goal": ""
        }
    )

    return success_response(
        data=profile,
        message="Profile loaded"
    )


@app.route("/profile", methods=["POST", "PUT"])
def save_profile():
    data = get_request_data()
    user_id = get_user_id(data)

    profile = {
        "name": str(data.get("name", "")).strip(),
        "email": str(data.get("email", "")).strip(),
        "monthly_income": data.get("monthly_income", ""),
        "primary_goal": str(
            data.get("primary_goal", data.get("goal", ""))
        ).strip()
    }

    profiles[user_id] = profile
    save_backend_data()

    return success_response(
        data=profile,
        message="Profile saved successfully"
    )


# ============================================================
# AI CHAT ROUTE
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():
    data = get_request_data()

    message = (
        data.get("message")
        or data.get("query")
        or data.get("prompt")
        or ""
    )

    message = str(message).strip()

    if not message:
        return error_response(
            "Please enter a question.",
            400
        )

    user_id = get_user_id(data)
    profile = profiles.get(user_id, {})

    try:
        if generate_response is not None:

            # Try engines that accept message and profile
            try:
                result = generate_response(
                    message,
                    profile=profile
                )
            except TypeError:
                # Try engines that accept only message
                result = generate_response(message)

            if isinstance(result, dict):
                answer = (
                    result.get("answer")
                    or result.get("response")
                    or result.get("message")
                    or str(result)
                )
            else:
                answer = str(result)

        else:
            answer = (
                "I can help you understand budgeting, savings, "
                "emergency funds, loans, EMIs, and financial planning. "
                "Please provide more details about your question."
            )

        return success_response(
            data={
                "question": message,
                "answer": answer,
                "response": answer
            },
            message="AI response generated"
        )

    except Exception as error:
        traceback.print_exc()

        return error_response(
            "The AI service could not process your question.",
            500,
            str(error)
        )


# ============================================================
# JOURNEY ROUTES
# ============================================================

@app.route("/journey/status", methods=["GET", "POST"])
def journey_status():
    data = get_request_data()
    user_id = get_user_id(data)

    status = server_journeys.get(
        user_id,
        {
            "started": False,
            "journey_name": "",
            "current_step": 0,
            "completed_steps": [],
            "steps": [],
            "completed": False
        }
    )

    return success_response(
        data=status,
        message="Journey status loaded"
    )


@app.route("/journey/start", methods=["POST"])
def start_journey():
    data = get_request_data()
    user_id = get_user_id(data)

    journey_name = (
        data.get("journey_name")
        or data.get("journey")
        or data.get("goal")
        or "Savings Planning"
    )

    journey_name = str(journey_name).strip()

    server_journeys[user_id] = {
        "started": True,
        "journey_name": journey_name,
        "current_step": 0,
        "completed_steps": [],
        "steps": [],
        "completed": False
    }
    save_backend_data()

    return success_response(
        data=server_journeys[user_id],
        message=f"{journey_name} started successfully"
    )


@app.route("/journey/complete", methods=["POST"])
def complete_journey_step():
    data = get_request_data()
    user_id = get_user_id(data)

    if user_id not in server_journeys:
        return error_response(
            "Please start a journey first.",
            400
        )

    journey = server_journeys[user_id]

    if not journey.get("started"):
        return error_response(
            "Please start a journey first.",
            400
        )

    step = (
        data.get("step")
        or data.get("step_index")
        or data.get("step_number")
    )

    if step is None:
        return error_response(
            "Please provide a step number.",
            400
        )

    try:
        step = int(step)
    except Exception:
        return error_response(
            "Step number must be numeric.",
            400
        )

    completed_steps = journey.get("completed_steps", [])

    if step not in completed_steps:
        completed_steps.append(step)

    completed_steps = sorted(list(set(completed_steps)))

    journey["completed_steps"] = completed_steps
    journey["current_step"] = len(completed_steps)

    if journey.get("steps"):
        journey["completed"] = (
            len(completed_steps) >= len(journey["steps"])
        )

    save_backend_data()

    return success_response(
        data=journey,
        message="Journey step completed"
    )


@app.route("/journey/reset", methods=["POST"])
def reset_journey():
    data = get_request_data()
    user_id = get_user_id(data)

    server_journeys[user_id] = {
        "started": False,
        "journey_name": "",
        "current_step": 0,
        "completed_steps": [],
        "steps": [],
        "completed": False
    }
    save_backend_data()

    return success_response(
        data=server_journeys[user_id],
        message="Journey reset successfully"
    )


# ============================================================
# DOCUMENT ANALYSIS ROUTE
# ============================================================

@app.route("/document", methods=["POST"])
def document_analysis():

    if "file" not in request.files:
        return error_response(
            "Please upload a file using the field name 'file'.",
            400
        )

    uploaded_file = request.files["file"]

    if not uploaded_file or uploaded_file.filename == "":
        return error_response(
            "No file selected.",
            400
        )

    filename = secure_filename(uploaded_file.filename)

    if not filename.lower().endswith(".pdf"):
        return error_response(
            "Only PDF files are supported.",
            400
        )

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = UPLOAD_FOLDER / unique_filename

    try:
        uploaded_file.save(file_path)

        if analyze_document is None:
            return error_response(
                "The documentai.py module is not available.",
                500
            )

        try:
            result = analyze_document(str(file_path))
        except TypeError:
            result = analyze_document(file_path)

        return success_response(
            data={
                "filename": filename,
                "analysis": result
            },
            message="Document analyzed successfully"
        )

    except Exception as error:
        traceback.print_exc()

        return error_response(
            "Unable to analyze the document.",
            500,
            str(error)
        )

    finally:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass


# ============================================================
# CALCULATOR ROUTES
# ============================================================

@app.route("/calculator/loan", methods=["POST"])
def calculate_loan():
    data = get_request_data()
    principal = float(data.get("principal", 0.0))
    rate = float(data.get("rate", 0.0))
    months = int(data.get("months", 0))
    extra_monthly = float(data.get("extra_monthly", 0.0))
    extra_yearly = float(data.get("extra_yearly", 0.0))

    if principal <= 0 or rate < 0 or months <= 0:
        return error_response("Principal, rate, and tenure must be positive numbers.", 400)

    if calculate_loan_amortization is None:
        return error_response("Loan engine is unavailable.", 500)

    result = calculate_loan_amortization(
        principal=principal,
        annual_rate=rate,
        months=months,
        extra_monthly=extra_monthly,
        extra_yearly=extra_yearly
    )

    return success_response(data=result, message="Loan amortization calculated successfully")


@app.route("/calculator/budget", methods=["POST", "GET"])
def calculate_budget():
    data = get_request_data() if request.method == "POST" else request.args
    income = float(data.get("income", 0.0))
    savings = float(data.get("savings", 0.0))

    if calculate_budget_50_30_20 is None:
        return error_response("Budget engine is unavailable.", 500)

    result = calculate_budget_50_30_20(income, savings)
    return success_response(data=result, message="50/30/20 budget breakdown calculated successfully")


@app.route("/calculator/sip", methods=["POST"])
def calculate_sip():
    data = get_request_data()
    monthly_investment = float(data.get("monthly_investment", 0.0))
    rate = float(data.get("rate", 0.0))
    years = float(data.get("years", 0.0))
    step_up = float(data.get("step_up", 0.0))

    if monthly_investment <= 0 or rate < 0 or years <= 0:
        return error_response("Investment amount, return rate, and years must be positive numbers.", 400)

    if calculate_sip_wealth is None:
        return error_response("SIP engine is unavailable.", 500)

    result = calculate_sip_wealth(
        monthly_investment=monthly_investment,
        annual_rate=rate,
        years=years,
        step_up_percent=step_up
    )
    return success_response(data=result, message="SIP projection calculated successfully")


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )