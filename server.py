from flask import Flask, request, jsonify, send_from_directory
from agent import plan_trip
import os

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/plan", methods=["POST"])
def plan():
    data = request.json
    lines = [
        f"I want to plan a Hong Kong trip. Here are my details:",
        f"- Trip duration: {data.get('days', 3)} days",
        f"- Budget: {data.get('budget', 'medium')}",
        f"- Group size: {data.get('group_size', 1)} person(s), ages: {', '.join(str(a) for a in data.get('ages', [22]))}",
        f"- Travel pace: {data.get('pace', 'moderate')}",
        f"- Interests: {', '.join(data.get('interests', []))}",
        f"- Constraints: {', '.join(data.get('constraints', [])) or 'none'}",
        f"- Special considerations: {', '.join(data.get('special', [])) or 'none'}",
        f"\nPlease generate a complete personalized itinerary for me.",
    ]
    try:
        result = plan_trip("\n".join(lines))
        return jsonify({"ok": True, "itinerary": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, port=5000)
