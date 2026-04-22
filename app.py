#!/usr/bin/env python3
# Hong Kong Travel Planner — interactive CLI
# Usage: python app.py

import sys
from agent import plan_trip


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw if raw else default


def _ask_int(prompt: str, default: int) -> int:
    while True:
        raw = _ask(prompt, str(default))
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a number.")


def _ask_choice(prompt: str, options: list[str], default: str) -> str:
    opts = " / ".join(options)
    while True:
        raw = _ask(f"{prompt} ({opts})", default).lower()
        if raw in [o.lower() for o in options]:
            return raw
        print(f"  Please choose one of: {opts}")


def _ask_multi(prompt: str, options: list[tuple[str, str]]) -> list[str]:
    """Let user pick multiple items from a numbered list."""
    print(f"\n{prompt}")
    for i, (key, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    print("  Enter numbers separated by commas (e.g. 1,3,5), or press Enter to skip.")
    raw = input("  > ").strip()
    if not raw:
        return []
    chosen = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(options):
                chosen.append(options[idx][0])
    return chosen


INTEREST_OPTIONS = [
    ("culture",       "Culture & History"),
    ("scenic_views",  "Scenic Views & Photography"),
    ("local_food",    "Local Food & Dining"),
    ("shopping",      "Shopping"),
    ("relaxation",    "Relaxation & Leisure"),
    ("hidden_gems",   "Hidden Gems / Local Experience"),
    ("social_trendy", "Social / Trendy Spots"),
]

CONSTRAINT_OPTIONS = [
    ("avoid_long_walking",          "Avoid long walking routes"),
    ("avoid_many_location_changes", "Avoid too many location changes in one day"),
    ("avoid_crowds",                "Avoid crowded tourist areas"),
    ("avoid_packed_schedule",       "Avoid a packed schedule"),
    ("avoid_outdoor_heavy",         "Avoid outdoor-heavy activities"),
    ("avoid_expensive",             "Avoid expensive options"),
]

SPECIAL_OPTIONS = [
    ("traveling_with_elderly",   "Traveling with elderly"),
    ("traveling_with_children",  "Traveling with children"),
    ("pregnant_traveler",        "Pregnant traveler"),
]


def collect_preferences() -> str:
    """Walk the user through the onboarding flow and return a prompt string."""
    print("\n" + "=" * 60)
    print("  Welcome to the HK Travel Planner")
    print("  Personalized itineraries for university students")
    print("=" * 60)

    # ── Basic info ────────────────────────────────────────────────
    print("\n── Traveler Info ──────────────────────────────────────────")
    age = _ask_int("Your age", 22)

    group_size = _ask_int("Number of travellers (including you)", 1)
    ages = [age]
    for i in range(2, group_size + 1):
        a = _ask_int(f"Age of traveller {i}", 22)
        ages.append(a)

    special = _ask_multi("Any special considerations?", SPECIAL_OPTIONS)

    # ── Trip details ──────────────────────────────────────────────
    print("\n── Trip Details ──────────────────────────────────────────")
    days = _ask_int("Trip duration (days)", 3)
    budget = _ask_choice("Budget level", ["low", "medium", "high"], "medium")
    pace = _ask_choice("Preferred pace", ["relaxed", "moderate", "packed"], "moderate")

    # ── Interests ─────────────────────────────────────────────────
    interests = _ask_multi("What would you like to experience in Hong Kong?", INTEREST_OPTIONS)
    if not interests:
        interests = ["culture", "local_food", "scenic_views"]
        print(f"  (defaulting to: culture, local food, scenic views)")

    # ── Constraints ───────────────────────────────────────────────
    constraints = _ask_multi("What would you prefer to avoid?", CONSTRAINT_OPTIONS)

    # ── Build natural-language request for the agent ──────────────
    interest_str = ", ".join(interests) if interests else "general sightseeing"
    constraint_str = ", ".join(constraints) if constraints else "no special constraints"
    special_str = ", ".join(special) if special else "none"
    ages_str = ", ".join(str(a) for a in ages)

    request = (
        f"I want to plan a Hong Kong trip. Here are my details:\n"
        f"- Trip duration: {days} days\n"
        f"- Budget: {budget}\n"
        f"- Group size: {group_size} person(s), ages: {ages_str}\n"
        f"- Travel pace: {pace}\n"
        f"- Interests: {interest_str}\n"
        f"- Constraints: {constraint_str}\n"
        f"- Special considerations: {special_str}\n\n"
        f"Please generate a complete personalized itinerary for me."
    )
    return request


def main():
    try:
        user_request = collect_preferences()

        print("\n" + "=" * 60)
        print("  Generating your personalized itinerary...")
        print("=" * 60 + "\n")

        itinerary = plan_trip(user_request)
        print(itinerary)

        # Offer to save
        print("\n" + "-" * 60)
        save = _ask("Save itinerary to a file? (yes/no)", "no").lower()
        if save in ("yes", "y"):
            filename = _ask("Filename", "my_hk_itinerary.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(itinerary)
            print(f"Saved to {filename}")

    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
