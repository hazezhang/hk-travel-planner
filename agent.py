# Hong Kong Travel Planner Agent
# Modules: Constraint Parser → Profile Builder → Data Retrieval → Itinerary Engine → Budget & Hotel Recommender → Output Generator

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from data import HK_ATTRACTIONS, HK_HOTELS, BUDGET_TIERS, TRANSPORT

load_dotenv(Path(__file__).parent / ".env")

MODEL = "gpt-4o"

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


def _run_tool(name: str, args: dict):
    return {
        "parse_constraints":       _parse_constraints,
        "get_attractions":         _get_attractions,
        "get_hotel_recommendations": _get_hotel_recommendations,
        "calculate_budget":        _calculate_budget,
        "get_transport_info":      _get_transport_info,
    }[name](args)


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the Hong Kong Travel Planner Agent, designed for university students from the Greater Bay Area visiting Hong Kong.

Your job is to produce a personalized, day-by-day travel itinerary following this pipeline:
1. Call `parse_constraints` to build the traveler profile from user input.
2. Call `get_attractions` to retrieve matching HK attractions.
3. Call `get_hotel_recommendations` to suggest accommodation.
4. Call `calculate_budget` using the cheapest recommended hotel's nightly rate.
5. Optionally call `get_transport_info` for key route segments.
6. Generate the final itinerary.

Output format (use exactly this structure):

---
## Your Hong Kong Itinerary

**Trip:** {N} days · {budget} budget · {group_size} traveller(s) · {pace} pace

### Traveler Profile
- Interests: ...
- Constraints: ...
- Special needs: ...

### Day-by-Day Plan
**Day 1 – [Theme]**
- 09:00 · [Attraction] — [1-line description] · [transport from hotel] ~X min
- 11:30 · ...
- 13:00 · Lunch: [local recommendation]
- ...
- Evening: [suggestion]

**Day 2 – [Theme]**
...

### Hotel Recommendations
1. **[Name]** · [Area] · HKD [price]/night — [why it suits this traveler]
2. ...

### Budget Breakdown (per person, HKD)
| Category | Per Day | Total ({N} days) |
|---|---|---|
| Transport | ... | ... |
| Food | ... | ... |
| Activities | ... | ... |
| Hotel | ... | ... |
| **Total** | ... | ... |

### Tips
- [3-5 practical tips relevant to this specific traveler profile]
---

Rules:
- Only recommend attractions from the tool results; do not invent ones not returned.
- Group geographically close attractions on the same day to minimize transit.
- Respect all constraints (e.g., avoid crowds, avoid long walking).
- Explain briefly WHY each hotel and route was chosen (explainability requirement from the report).
- Keep the tone friendly and practical for university students.
"""


# ── Main agent loop ───────────────────────────────────────────────────────────

def plan_trip(user_request: str) -> str:
    """Run the travel planner agent and return the formatted itinerary."""
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
        messages.append(msg)

        if response.choices[0].finish_reason == "stop":
            return msg.content or ""

        if response.choices[0].finish_reason == "tool_calls":
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
