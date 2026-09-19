# storage.py
# FinPath Local and Browser Storage Manager

import json
import os
from datetime import datetime
from pathlib import Path

try:
    import streamlit.components.v1 as components
except Exception:
    components = None

STORAGE_FILE = Path(__file__).parent / "finpath_local_storage.json"

DEFAULT_STORAGE = {
    "profile": {
        "name": "",
        "email": "",
        "age": 28,
        "occupation": "Salaried Professional",
        "city": "",
        "dependents": 0,
        "monthly_income": 0.0,
        "monthly_saving_capacity": 0.0,
        "existing_monthly_emi": 0.0,
        "existing_investments": 0.0,
        "emergency_fund": 0.0,
        "health_insurance_cover": 0.0,
        "term_insurance_cover": 0.0,
        "primary_goal": "Buying a Home / Property",
        "target_horizon": "Medium-Term (3 - 5 Years)",
        "risk_profile": "Moderate (Balanced Growth)"
    },
    "currency": "INR",
    "chat_messages": [
        {
            "role": "assistant",
            "content": (
                "Hello. I am your FinPath Financial Assistant. "
                "You can ask me about loan EMIs, prepayment strategies, "
                "SIP wealth compounding, health & term insurance, claim procedures, "
                "deposits, or any financial journey."
            )
        }
    ],
    "checklists": {},
    "journey_twin": {
        "action": "Select an action",
        "documents": {}
    },
    "activity_log": [
        {
            "timestamp": "2026-09-19 09:00:00",
            "category": "Workspace Initialization",
            "action": "Initialized FinPath Financial Planning Workspace",
            "details": "Ready for financial assessments and modeling"
        }
    ]
}


def load_local_storage():
    """
    Load data from the local storage JSON file on disk.
    If the file does not exist or is invalid, returns the default storage data.
    """
    if not STORAGE_FILE.exists():
        data = dict(DEFAULT_STORAGE)
        save_local_storage(data)
        return data

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return dict(DEFAULT_STORAGE)

            # Ensure all default keys exist
            for key, val in DEFAULT_STORAGE.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception as e:
        print(f"[FinPath Storage] Error loading local storage file: {e}")
        return dict(DEFAULT_STORAGE)


def save_local_storage(data):
    """
    Save the given data dictionary to the local storage JSON file on disk.
    """
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[FinPath Storage] Error saving to local storage file: {e}")
        return False


def get_stored_item(key, default=None):
    """
    Retrieve a specific item from local storage.
    """
    data = load_local_storage()
    return data.get(key, default if default is not None else DEFAULT_STORAGE.get(key))


def set_stored_item(key, value):
    """
    Set a specific item in local storage and save to disk.
    """
    data = load_local_storage()
    data[key] = value
    save_local_storage(data)


def log_activity(category, action, details=""):
    """
    Log a user interaction or site activity with timestamp and details.
    Preserves up to the last 100 activities.
    """
    data = load_local_storage()
    log = data.get("activity_log", [])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "timestamp": now_str,
        "category": str(category),
        "action": str(action),
        "details": str(details)
    }

    # Avoid duplicate consecutive logs with exact same action and category
    if not log or log[-1].get("action") != entry["action"] or log[-1].get("category") != entry["category"]:
        log.append(entry)
        data["activity_log"] = log[-100:]
        save_local_storage(data)

    return entry


def get_activity_log():
    """
    Get all recorded user activities.
    """
    data = load_local_storage()
    return data.get("activity_log", [])


def clear_local_storage():
    """
    Reset local storage to defaults and write default data to disk.
    """
    defaults = dict(DEFAULT_STORAGE)
    save_local_storage(defaults)
    return defaults


def sync_to_browser_local_storage(key, value):
    """
    Injects JavaScript to write to the browser's window.localStorage.
    Ensures data is present in browser inspection / client storage.
    """
    if components is None:
        return

    try:
        json_val = json.dumps(value)
        js_code = f"""
        <script>
        (function() {{
            try {{
                const key = {json.dumps(key)};
                const val = {json.dumps(json_val)};
                localStorage.setItem(key, val);
                if (window.parent && window.parent.localStorage) {{
                    window.parent.localStorage.setItem(key, val);
                }}
            }} catch (err) {{
                console.warn("[FinPath] LocalStorage write error:", err);
            }}
        }})();
        </script>
        """
        components.html(js_code, height=0, width=0)
    except Exception as e:
        print(f"[FinPath Storage] Error syncing to browser localStorage: {e}")


def clear_browser_local_storage(keys=None):
    """
    Injects JavaScript to clear items from the browser's window.localStorage.
    """
    if components is None:
        return

    if keys is None:
        keys = ["finpath_profile", "finpath_currency", "finpath_chat_messages", "finpath_checklists", "finpath_journey_twin", "finpath_activity_log"]
    try:
        js_code = f"""
        <script>
        (function() {{
            try {{
                const keys = {json.dumps(keys)};
                keys.forEach(k => {{
                    localStorage.removeItem(k);
                    if (window.parent && window.parent.localStorage) {{
                        window.parent.localStorage.removeItem(k);
                    }}
                }});
            }} catch (err) {{
                console.warn("[FinPath] LocalStorage clear error:", err);
            }}
        }})();
        </script>
        """
        components.html(js_code, height=0, width=0)
    except Exception as e:
        print(f"[FinPath Storage] Error clearing browser localStorage: {e}")
