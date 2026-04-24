# Hong Kong Travel Planner Agent
# Modules: Constraint Parser → Weather Forecast → Profile Builder → Data Retrieval → Itinerary Engine → Budget & Hotel Recommender → Output Generator

import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from data import HK_ATTRACTIONS, HK_HOTELS, BUDGET_TIERS, TRANSPORT, HK_WEATHER_BY_MONTH
from food_rag import (
    ensure_food_database,
    ensure_hotel_database,
    ensure_poi_database,
    search_food_places,
    search_hotel_places,
    search_poi_places,
)

load_dotenv(Path(__file__).parent / ".env")

MODEL = "gpt-4o"

# ── WMO weather code → (description, emoji) ──────────────────────────────────

WMO_CONDITIONS = {
    0:  ("Clear Sky",           "☀️"),
    1:  ("Mainly Clear",        "🌤️"),
    2:  ("Partly Cloudy",       "⛅"),
    3:  ("Overcast",            "☁️"),
    45: ("Foggy",               "🌫️"),
    48: ("Rime Fog",            "🌫️"),
    51: ("Light Drizzle",       "🌦️"),
    53: ("Drizzle",             "🌦️"),
    55: ("Dense Drizzle",       "🌦️"),
    61: ("Light Rain",          "🌧️"),
    63: ("Moderate Rain",       "🌧️"),
    65: ("Heavy Rain",          "🌧️"),
    80: ("Light Showers",       "🌦️"),
    81: ("Moderate Showers",    "🌧️"),
    82: ("Heavy Showers",       "🌧️"),
    95: ("Thunderstorm",        "⛈️"),
    96: ("Thunderstorm",        "⛈️"),
    99: ("Severe Thunderstorm", "⛈️"),
}


# ── Tool definitions (OpenAI function-calling format) ─────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "parse_constraints",
            "description": (
                "Parse raw user preferences into a structured traveler profile. "
                "Extracts budget level, interests, constraints, group info, and mobility needs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_days": {"type": "integer", "description": "Number of trip days"},
                    "budget_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "low = student budget, medium = moderate spend, high = luxury",
                    },
                    "group_size": {"type": "integer", "description": "Total number of travellers including the user"},
                    "traveler_ages": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Age of each traveller",
                    },
                    "interests": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "culture", "history", "scenic_views", "photography",
                                "local_food", "shopping", "relaxation", "hidden_gems", "social_trendy",
                            ],
                        },
                    },
                    "constraints": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "avoid_long_walking", "avoid_many_location_changes",
                                "avoid_crowds", "avoid_packed_schedule",
                                "avoid_outdoor_heavy", "avoid_expensive",
                            ],
                        },
                    },
                    "special_considerations": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["traveling_with_elderly", "traveling_with_children", "pregnant_traveler"],
                        },
                    },
                    "pace": {
                        "type": "string",
                        "enum": ["relaxed", "moderate", "packed"],
                        "description": "How many activities per day the user wants",
                    },
                },
                "required": ["duration_days", "budget_level", "group_size", "interests", "pace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": (
                "Get a day-by-day weather forecast for Hong Kong for the trip dates. "
                "Uses real Open-Meteo forecast data if within 15 days; otherwise uses seasonal climate averages. "
                "Returns condition, temperature, humidity, rain probability, and practical tips per day."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Trip start date in YYYY-MM-DD format",
                    },
                    "duration_days": {
                        "type": "integer",
                        "description": "Number of trip days to forecast",
                    },
                },
                "required": ["start_date", "duration_days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_attractions",
            "description": (
                "Retrieve and rank Hong Kong attractions that match the traveler profile. "
                "Filters by interests, respects constraints, and flags accessibility issues."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Interest tags to match",
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Constraint tags that restrict certain attractions",
                    },
                    "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "mobility_limited": {
                        "type": "boolean",
                        "description": "True if any traveler has limited mobility",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max number of attractions to return",
                    },
                },
                "required": ["interests", "budget_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hotel_recommendations",
            "description": "Return hotel options matched to budget tier with price breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "nights": {"type": "integer", "description": "Number of nights"},
                    "group_size": {"type": "integer"},
                    "preferred_area": {
                        "type": "string",
                        "description": "Optional preferred district (e.g. Tsim Sha Tsui, Central)",
                    },
                },
                "required": ["budget_level", "nights", "group_size"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": "Calculate total trip budget breakdown per person and for the whole group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "days": {"type": "integer"},
                    "group_size": {"type": "integer"},
                    "hotel_cost_per_night": {"type": "number", "description": "Selected hotel nightly rate in HKD"},
                },
                "required": ["budget_level", "days", "group_size", "hotel_cost_per_night"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transport_info",
            "description": "Get travel time and cost between two Hong Kong districts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_district": {"type": "string"},
                    "to_district": {"type": "string"},
                },
                "required": ["from_district", "to_district"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_food_rag",
            "description": (
                "Search Hong Kong food recommendations from the local Excel-backed RAG database. "
                "Use this to pick concrete meal places aligned with user budget, area, and preferences."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text food intent or cuisine keywords"},
                    "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "preferred_area": {"type": "string", "description": "Optional area/district focus"},
                    "preferred_cuisines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional cuisine names, e.g. Cantonese, Japanese, French",
                    },
                    "top_k": {"type": "integer", "description": "Maximum number of food places to return"},
                },
                "required": ["query", "budget_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_poi_rag",
            "description": (
                "Search attractions/POIs from the local HK 酒店+景点 Excel-backed RAG database. "
                "Use this to get concrete attraction candidates and details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text POI intent or landmark keywords"},
                    "preferred_area": {"type": "string", "description": "Optional area/district focus"},
                    "preferred_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional categories such as sightseeing, museum, nature, shopping",
                    },
                    "top_k": {"type": "integer", "description": "Maximum number of POIs to return"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotel_rag",
            "description": (
                "Search hotels from the local HK 酒店+景点 Excel-backed RAG database. "
                "Use this for concrete hotel suggestions that match budget and area."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text hotel intent keywords"},
                    "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "preferred_area": {"type": "string", "description": "Optional area focus"},
                    "top_k": {"type": "integer", "description": "Maximum number of hotels to return"},
                },
                "required": ["query", "budget_level"],
            },
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

def _parse_constraints(args: dict) -> dict:
    mobility_limited = (
        args.get("mobility_limited", False)
        or "traveling_with_elderly" in args.get("special_considerations", [])
        or "pregnant_traveler" in args.get("special_considerations", [])
    )
    return {
        "duration_days": args["duration_days"],
        "budget_level": args["budget_level"],
        "group_size": args["group_size"],
        "traveler_ages": args.get("traveler_ages", []),
        "interests": args["interests"],
        "constraints": args.get("constraints", []),
        "special_considerations": args.get("special_considerations", []),
        "pace": args["pace"],
        "mobility_limited": mobility_limited,
        "attractions_per_day": {"relaxed": 2, "moderate": 3, "packed": 5}[args["pace"]],
    }


def _build_weather_recommendation(rain_prob: int, uv: int, humidity: int, temp_high: int, temp_low: int) -> str:
    tips = []
    if rain_prob >= 60:
        tips.append("bring an umbrella — high chance of rain")
    elif rain_prob >= 30:
        tips.append("pack a compact umbrella as a precaution")
    if uv >= 9:
        tips.append("UV index is very high — apply SPF 50+ sunscreen")
    elif uv >= 7:
        tips.append("UV index is high — apply sunscreen before heading out")
    if humidity >= 84:
        tips.append("very humid — wear light breathable clothing and stay hydrated")
    elif temp_high >= 30:
        tips.append("hot weather — plan indoor breaks and drink plenty of water")
    elif temp_high <= 16:
        tips.append("bring a warm jacket for outdoor activities")
    elif temp_high <= 20:
        tips.append("light jacket recommended for mornings and evenings")
    if not tips:
        tips.append("comfortable conditions — great for outdoor exploration")
    return ". ".join(t.capitalize() for t in tips) + "."


def _get_weather_forecast(args: dict) -> dict:
    start_date_str = args.get("start_date", "")
    duration_days = max(1, int(args.get("duration_days", 3)))

    # Parse start date
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        start_date = datetime.today() + timedelta(days=14)
        start_date_str = start_date.strftime("%Y-%m-%d")

    end_date = start_date + timedelta(days=duration_days - 1)
    days_until_trip = (start_date - datetime.today()).days

    # ── Real forecast via Open-Meteo (within 15 days) ─────────────────────
    if days_until_trip <= 15:
        try:
            resp = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 22.3193,
                    "longitude": 114.1694,
                    "daily": ",".join([
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_probability_max",
                        "weathercode",
                        "relative_humidity_2m_mean",
                        "uv_index_max",
                    ]),
                    "timezone": "Asia/Hong_Kong",
                    "start_date": start_date_str,
                    "end_date": end_date.strftime("%Y-%m-%d"),
                },
                timeout=8,
            )
            resp.raise_for_status()
            daily = resp.json()["daily"]

            forecasts = []
            for i in range(min(duration_days, len(daily["time"]))):
                wmo = int(daily["weathercode"][i] or 1)
                condition, emoji = WMO_CONDITIONS.get(wmo, ("Partly Cloudy", "⛅"))
                rain_prob = int(daily["precipitation_probability_max"][i] or 0)
                temp_high = round(daily["temperature_2m_max"][i] or 25)
                temp_low  = round(daily["temperature_2m_min"][i] or 20)
                humidity  = round(daily["relative_humidity_2m_mean"][i] or 75)
                uv        = round(daily["uv_index_max"][i] or 5)

                forecasts.append({
                    "day": i + 1,
                    "date": daily["time"][i],
                    "emoji": emoji,
                    "condition": condition,
                    "temp_high_c": temp_high,
                    "temp_low_c": temp_low,
                    "humidity_pct": humidity,
                    "rain_probability_pct": rain_prob,
                    "uv_index": uv,
                    "recommendation": _build_weather_recommendation(rain_prob, uv, humidity, temp_high, temp_low),
                })

            return {
                "source": "live_forecast",
                "note": "Live 15-day forecast from Open-Meteo.",
                "forecasts": forecasts,
            }
        except Exception:
            pass  # fall through to climate data

    # ── Climate averages fallback (trip is far in the future) ─────────────
    month = start_date.month
    monthly = HK_WEATHER_BY_MONTH[month]
    variations = monthly["daily_variations"]

    forecasts = []
    for day_idx in range(duration_days):
        var = variations[day_idx % len(variations)]
        rain_prob = max(0, min(100, monthly["rain_probability_pct"] + var["rain_delta"]))
        temp_high = monthly["temp_high_c"] + var["temp_delta"]
        temp_low  = monthly["temp_low_c"]  + var["temp_delta"]

        condition_emojis = {
            "Sunny": "☀️", "Sunny & Hot": "☀️", "Hot & Sunny": "☀️",
            "Partly Cloudy": "⛅", "Clear & Breezy": "🌤️", "Clear & Cool": "🌤️",
            "Cool & Clear": "🌤️", "Cloudy": "☁️", "Overcast": "☁️",
            "Cloudy & Hot": "☁️", "Hot & Humid": "🌫️", "Misty": "🌫️",
            "Light Rain": "🌦️", "Cloudy with Showers": "🌦️",
            "Occasional Showers": "🌦️", "Overcast with Rain": "🌧️",
            "Heavy Showers": "🌧️", "Heavy Rain": "🌧️",
            "Thunderstorms": "⛈️",
        }
        condition = var["condition"]
        emoji = condition_emojis.get(condition, "⛅")
        date_str = (start_date + timedelta(days=day_idx)).strftime("%Y-%m-%d")

        forecasts.append({
            "day": day_idx + 1,
            "date": date_str,
            "emoji": emoji,
            "condition": condition,
            "temp_high_c": temp_high,
            "temp_low_c": temp_low,
            "humidity_pct": monthly["humidity_pct"],
            "rain_probability_pct": rain_prob,
            "uv_index": monthly["uv_index"],
            "recommendation": _build_weather_recommendation(
                rain_prob, monthly["uv_index"], monthly["humidity_pct"], temp_high, temp_low
            ),
        })

    return {
        "source": "climate_averages",
        "note": f"Seasonal climate averages for {monthly['name']} — {monthly['general_advisory']}",
        "forecasts": forecasts,
    }


def _get_attractions(args: dict) -> list:
    interests = set(args["interests"])
    constraints = set(args.get("constraints", []))
    budget_level = args["budget_level"]
    mobility_limited = args.get("mobility_limited", False)
    max_results = args.get("max_results", 12)

    budget_order = {"low": 0, "medium": 1, "high": 2}
    user_budget_rank = budget_order[budget_level]

    results = []
    for attr in HK_ATTRACTIONS:
        if budget_order[attr["cost_tier"]] > user_budget_rank:
            continue
        if mobility_limited and not attr["mobility_friendly"]:
            continue
        if "avoid_crowds" in constraints and attr["crowd_level"] == "high":
            continue
        overlap = len(set(attr["tags"]) & interests)
        if overlap == 0:
            continue
        results.append({**attr, "_score": overlap})

    results.sort(key=lambda x: x["_score"], reverse=True)
    for r in results:
        r.pop("_score", None)
    return results[:max_results]


def _get_hotel_recommendations(args: dict) -> dict:
    budget_level = args["budget_level"]
    nights = args["nights"]
    group_size = args["group_size"]
    preferred_area = args.get("preferred_area", "").lower()

    matches = [h for h in HK_HOTELS if h["budget_tier"] == budget_level]
    if preferred_area:
        preferred = [h for h in matches if preferred_area in h["area"].lower()]
        if preferred:
            matches = preferred

    options = []
    for h in matches[:3]:
        options.append({
            "name": h["name"],
            "area": h["area"],
            "price_per_night_hkd": h["price_hkd_per_night"],
            "total_hkd": h["price_hkd_per_night"] * nights,
            "mtr_minutes": h["mtr_minutes"],
            "description": h["description"],
        })
    return {"options": options, "note": f"Prices in HKD for {nights} night(s), {group_size} guest(s)."}


def _calculate_budget(args: dict) -> dict:
    tier = BUDGET_TIERS[args["budget_level"]]
    days = args["days"]
    group_size = args["group_size"]
    hotel_cost = args["hotel_cost_per_night"]

    per_person_total = (
        (tier["transport"] + tier["food"] + tier["activities"] + tier["misc"]) * days
        + hotel_cost * days / max(group_size, 1)
    )
    group_total = (
        (tier["transport"] + tier["food"] + tier["activities"] + tier["misc"]) * days * group_size
        + hotel_cost * days
    )
    return {
        "per_person_daily_hkd": tier["total_per_person"],
        "per_person_trip_total_hkd": round(per_person_total),
        "group_trip_total_hkd": round(group_total),
        "breakdown_per_day": {
            "transport": tier["transport"],
            "food": tier["food"],
            "activities": tier["activities"],
            "misc": tier["misc"],
        },
        "hotel_total_hkd": round(hotel_cost * days),
    }


def _get_transport_info(args: dict) -> dict:
    a, b = args["from_district"], args["to_district"]
    info = TRANSPORT.get((a, b)) or TRANSPORT.get((b, a))
    if info:
        return info
    return {
        "mode": "MTR (transfer may be needed)",
        "minutes": 30,
        "cost_hkd": 15,
        "note": "Exact route not in database; use MTR app for real-time directions.",
    }


def _search_food_rag(args: dict) -> dict:
    return search_food_places(
        query=args.get("query", ""),
        budget_level=args.get("budget_level", ""),
        preferred_area=args.get("preferred_area", ""),
        preferred_cuisines=args.get("preferred_cuisines", []),
        top_k=int(args.get("top_k", 8)),
    )


def _search_poi_rag(args: dict) -> dict:
    return search_poi_places(
        query=args.get("query", ""),
        preferred_area=args.get("preferred_area", ""),
        preferred_categories=args.get("preferred_categories", []),
        top_k=int(args.get("top_k", 10)),
    )


def _search_hotel_rag(args: dict) -> dict:
    return search_hotel_places(
        query=args.get("query", ""),
        budget_level=args.get("budget_level", ""),
        preferred_area=args.get("preferred_area", ""),
        top_k=int(args.get("top_k", 6)),
    )


def _run_tool(name: str, args: dict):
    return {
        "parse_constraints":         _parse_constraints,
        "get_weather_forecast":      _get_weather_forecast,
        "get_attractions":           _get_attractions,
        "get_hotel_recommendations": _get_hotel_recommendations,
        "calculate_budget":          _calculate_budget,
        "get_transport_info":        _get_transport_info,
        "search_food_rag":           _search_food_rag,
        "search_poi_rag":            _search_poi_rag,
        "search_hotel_rag":          _search_hotel_rag,
    }[name](args)


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the itinerary planning engine of HK Trip Curator.

Your job is to generate a Hong Kong travel plan that is:
1) constraint-aware
2) tool-augmented
3) explainable

Core input variables (must be reflected in your reasoning and output):
- duration
- budget
- pace
- group_size
- traveler_ages
- special_considerations
- interests
- constraints
- custom_requirements
- traveler_profile
- weather_result
- attraction_candidates
- hotel_area_candidates
- hotel_candidates
- fact_lookup_result

Available tools and recommended call sequence:
1. Call `parse_constraints` to build traveler profile.
2. Call `get_weather_forecast` for trip weather.
3. Call `get_attractions` for base attraction candidates.
4. Call `search_poi_rag` for POI/attraction RAG results.
5. Call `search_food_rag` for restaurant RAG results.
6. Call `search_hotel_rag` for hotel RAG results.
7. Call `get_hotel_recommendations` for structured hotel options.
8. Call `calculate_budget` using the cheapest practical hotel nightly cost.
9. Optionally call `get_transport_info` for key route transfers.
10. Generate final itinerary.

Prompt design principles:
- Understand traveler profile first, then arrange routes.
- Handle constraints first, then add experience highlights.
- Tool-grounded only: do not fabricate attractions/hotels/restaurants/facts.
- Keep output structure fixed for frontend rendering.
- Explanation must align with route, hotel, and budget choices.

Route planning rules:
Rule 1 (area clustering):
- Same-day attractions should be in same or adjacent areas to reduce backtracking.
- Prefer combinations like Central+PMQ+Tai Kwun+Peak, TST+Harbourfront, Mong Kok+Yau Ma Tei+Sham Shui Po.

Rule 2 (low budget):
- Prefer free/low-cost attractions.
- Prioritize MTR/bus/ferry.
- Reduce high-ticket activities and expensive dining.

Rule 3 (mobility constraints):
- If elderly/children/pregnant/avoid_long_walking, reduce long walking and complex transfers.
- Prefer mobility-friendly spots and lower activity count per day.

Rule 4 (pace control):
- relaxed: 2 core activities/day
- moderate: 3 core activities/day
- packed: up to 4 core activities/day

Rule 5 (weather adaptation):
- With high rain/humidity/typhoon risk, prioritize indoor or mixed attractions.
- De-prioritize beach, exposed viewpoints, and full-day remote outdoor trips.

Rule 6 (crowd avoidance):
- If avoid_crowds is selected, place hotspots at off-peak times or replace with alternatives.
- Explain crowd-avoidance logic explicitly.

Rule 7 (hotel area recommendation):
- Recommend area based on multi-day activity distribution, transport convenience, budget, group features, and pace.
- Output one preferred area first, then 2-3 hotel options.

Budget/hotel recommendation logic:
- Recommend hotel area before specific hotels.
- Budget categories must include: Transport, Food, Activities, Hotel, Total.
- Show per-day and trip-total values.
- low: cost efficiency; medium: balanced; high: comfort/quality first.

Required output structure (must follow exactly):
---
## Your Hong Kong Itinerary

Trip: {N} days · {budget} budget · {group_size} travellers · {pace} pace

### Traveler Profile
- Interests: ...
- Constraints: ...
- Special needs: ...

### Day-by-Day Plan
**Day 1 - [Theme]**
[WEATHER] {emoji} {condition} · {date} · {temp_low}–{temp_high}°C · Humidity {humidity}% · ☔ Rain {rain_prob}% — {recommendation}
- 09:00 · [Attraction] — [reason] · [transport] ~X min
- 12:30 · Lunch: [restaurant from search_food_rag]
- 18:30 · Evening: [suggestion]

**Day 2 - [Theme]**
[WEATHER] ...
- ...

### Hotel Area Recommendation
- [Preferred area] — [why it serves whole itinerary]

### Hotel Recommendations
1. [Hotel name from search_hotel_rag/get_hotel_recommendations] — [fit reason]
2. ...
3. ...

### Food Picks from RAG Database
- [Restaurant from search_food_rag] · [Cuisine] · [Area] · [Price] — [why selected]
- ...

### Budget Breakdown (per person, HKD)
| Category | Per Day | Total ({N} days) |
|---|---|---|
| Transport | ... | ... |
| Food | ... | ... |
| Activities | ... | ... |
| Hotel | ... | ... |
| Total | ... | ... |

### Why This Plan Works For You
- Area clustering and reduced backtracking
- Constraint handling details
- Budget and hotel fit
- Style/interest match

### Tips
- 3 to 5 practical travel tips
---

After the closing ---, append a machine-readable map block (STRICT JSON):
```map_data
{"day_1": ["Exact Attraction Name A", "Exact Attraction Name B"], "day_2": ["Exact Attraction Name C"], "day_3": []}
```

Hard requirements:
- Do not invent attractions/hotels/restaurants; use tool outputs.
- Prefer POIs from `get_attractions` and `search_poi_rag`.
- Prefer hotels from `search_hotel_rag` and `get_hotel_recommendations`.
- Prefer restaurants from `search_food_rag`.
- In `map_data`, use exact attraction names from tool outputs.
- The `[WEATHER]` line must be the first line under each day heading.
"""


# ── Main agent loop ───────────────────────────────────────────────────────────

def plan_trip(user_request: str) -> str:
    """Run the travel planner agent and return the formatted itinerary."""
    # Ensure food RAG database is available before planning.
    ensure_food_database()
    ensure_poi_database()
    ensure_hotel_database()
    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_request},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            tools=TOOLS,
            messages=messages,
        )

        msg = response.choices[0].message
        finish = response.choices[0].finish_reason

        assistant_dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_dict)

        if finish == "stop":
            return msg.content or ""

        if finish == "tool_calls":
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                result = _run_tool(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            continue

        break

    return "Agent stopped unexpectedly."
