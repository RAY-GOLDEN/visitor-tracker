from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)
CORS(app)

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDS_JSON", "")
MIN_TITLE_KEYWORDS = ["ceo", "owner", "founder", "director", "vp", "president"]

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def lookup_ip(ip):
    try:
        url = "https://api.apollo.io/api/v1/people/match"
        headers = {"x-api-key": APOLLO_API_KEY, "Content-Type": "application/json"}
        payload = {"ip_address": ip, "reveal_personal_emails": False}
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        person = data.get("person")
        if not person:
            return None
        title = (person.get("title") or "").lower()
        if not any(k in title for k in MIN_TITLE_KEYWORDS):
            return None
        org = person.get("organization") or {}
        return {
            "name":    person.get("name", ""),
            "title":   person.get("title", ""),
            "email":   person.get("email", ""),
            "phone":   person.get("phone_numbers", [{}])[0].get("raw_number", "") if person.get("phone_numbers") else "",
            "linkedin": person.get("linkedin_url", ""),
            "company": org.get("name", ""),
        }
    except Exception as e:
        print(f"[APOLLO ERROR] {e}")
        return None

def save_to_sheet(lead, page):
    try:
        sheet = get_sheet()
        existing = sheet.col_values(2)
        if lead["company"] in existing:
            row_num = existing.index(lead["company"]) + 1
            sheet.update_cell(row_num, 1, datetime.now().strftime("%Y-%m-%d %H:%M"))
            print(f"[SHEET] Updated existing: {lead['company']}")
            return "updated"
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            lead["company"],
            lead["name"],
            lead["title"],
            lead["email"],
            lead["phone"],
            lead["linkedin"],
            page,
            "New",
            ""
        ])
        print(f"[SHEET] Added new: {lead['company']}")
        return "added"
    except Exception as e:
        print(f"[SHEET ERROR] {e}")
        return "error"

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Visitor tracker is running"})

@app.route("/visitor", methods=["POST"])
def visitor():
    data = request.get_json()
    if not data or "ip" not in data:
        return jsonify({"error": "No IP provided"}), 400
    ip   = data.get("ip", "")
    page = data.get("page", "unknown")
    print(f"[VISITOR] IP: {ip} | Page: {page}")
    lead = lookup_ip(ip)
    if not lead:
        print(f"[SKIP] No match for IP: {ip}")
        return jsonify({"status": "no_match"})
    result = save_to_sheet(lead, page)
    print(f"[LEAD] {lead}")
    return jsonify({"status": "matched", "sheet": result, "lead": lead})

if __name__ == "__main__":
    app.run(debug=True)
