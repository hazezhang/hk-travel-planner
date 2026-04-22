from flask import Flask, request, jsonify, send_from_directory
from agent import plan_trip, _get_weather_forecast
from data import HK_ATTRACTIONS

app = Flask(__name__, static_folder="static")

# Static coords lookup from attractions database
ATTRACTION_COORDS = {
    a["name"]: {"lat": a["lat"], "lng": a["lng"]}
    for a in HK_ATTRACTIONS
}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/plan", methods=["POST"])
def plan():
    data = request.json
    start_date = data.get("start_date", "")
    days = int(data.get("days", 3))
    custom = data.get("custom_requirements", {}) or {}

    # Call weather API independently — guarantees structured data for the frontend
    # regardless of how the AI formats its output text.
    weather_data = None
    try:
        weather_data = _get_weather_forecast({"start_date": start_date, "duration_days": days})
    except Exception:
        pass  # frontend degrades gracefully (no weather cards shown)

    lines = [
        "I want to plan a Hong Kong trip. Here are my details:",
        f"- Trip start date: {start_date} (use this for the weather forecast)",
        f"- Trip duration: {days} days",
        f"- Budget: {data.get('budget', 'medium')}",
        f"- Group size: {data.get('group_size', 1)} person(s), ages: {', '.join(str(a) for a in data.get('ages', [22]))}",
        f"- Travel pace: {data.get('pace', 'moderate')}",
        f"- Interests: {', '.join(data.get('interests', []))}",
        f"- Constraints: {', '.join(data.get('constraints', [])) or 'none'}",
        f"- Special considerations: {', '.join(data.get('special', [])) or 'none'}",
        "- Custom requirements from each planning step:",
        f"  - Step 1 (group & dates): {custom.get('step1_group_dates', 'none') or 'none'}",
        f"  - Step 2 (trip shape): {custom.get('step2_trip_shape', 'none') or 'none'}",
        f"  - Step 3 (travel style): {custom.get('step3_travel_style', 'none') or 'none'}",
        f"  - Step 4 (constraints & route): {custom.get('step4_constraints_route', 'none') or 'none'}",
        f"- Regeneration feedback (if user is not satisfied): {custom.get('regeneration_feedback', 'none') or 'none'}",
        "- If regeneration feedback is provided, treat it as a high-priority update and revise the itinerary accordingly.",
        "\nPlease generate a complete personalized itinerary for me.",
    ]
    try:
        result = plan_trip("\n".join(lines))
        return jsonify({
            "ok": True,
            "itinerary": result,
            "weather_data": weather_data,       # structured, guaranteed from real API
            "attraction_coords": ATTRACTION_COORDS,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
