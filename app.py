from flask import Flask, request, jsonify
import config

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Visitor tracker is running"
    })


@app.route("/visitor", methods=["POST"])
def visitor():
    data = request.get_json()

    if not data or "ip" not in data:
        return jsonify({"error": "No IP provided"}), 400

    ip   = data.get("ip", "")
    page = data.get("page", "unknown")

    print(f"[VISITOR] IP: {ip} | Page: {page}")

    return jsonify({"status": "received", "ip": ip})


if __name__ == "__main__":
    app.run(debug=True)
