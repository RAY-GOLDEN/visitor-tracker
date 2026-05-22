from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
MIN_TITLE_KEYWORDS = ["ceo", "owner", "founder", "director", "vp", "president"]


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

    print(f"[LEAD] {lead}")
    return jsonify({"status": "matched", "lead": lead})


if __name__ == "__main__":
    app.run(debug=True)