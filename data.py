# Static Hong Kong travel data: attractions, hotels, transport

HK_ATTRACTIONS = [
    # ── Hong Kong Island ─────────────────────────────────────────────────────
    {
        "name": "Victoria Peak",
        "district": "The Peak / Central",
        "tags": ["scenic_views", "photography", "culture"],
        "cost_tier": "medium",    # Peak Tram ~HKD 118 return
        "duration_hours": 2.5,
        "mobility_friendly": False,  # steep tram, some walking
        "crowd_level": "high",
        "description": "Iconic hilltop with panoramic city views; take the historic Peak Tram.",
        "opening": "Peak Tram 07:00-23:00 daily",
    },
    {
        "name": "PMQ",
        "district": "Central",
        "tags": ["culture", "photography", "social_trendy", "shopping"],
        "cost_tier": "low",
        "duration_hours": 1.5,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "Former police married quarters turned creative hub with local designer shops and cafés.",
        "opening": "10:00-20:00 daily",
    },
    {
        "name": "Tai Kwun",
        "district": "Central",
        "tags": ["culture", "history", "photography", "social_trendy"],
        "cost_tier": "low",
        "duration_hours": 2.0,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "Restored Central Police Station complex now housing galleries, restaurants, and events.",
        "opening": "11:00-23:00 daily",
    },
    {
        "name": "Hong Kong Palace Museum",
        "district": "West Kowloon",
        "tags": ["culture", "history"],
        "cost_tier": "medium",   # ~HKD 50-120
        "duration_hours": 3.0,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "World-class collection of Chinese art and artefacts from the Palace Museum Beijing.",
        "opening": "10:00-18:00 (closed Tue)",
    },
    {
        "name": "Stanley Market & Promenade",
        "district": "Stanley",
        "tags": ["shopping", "scenic_views", "local_food", "relaxation"],
        "cost_tier": "low",
        "duration_hours": 2.0,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "Charming seaside market village with alfresco dining and harbour views.",
        "opening": "10:00-18:00 daily",
    },
    {
        "name": "Repulse Bay Beach",
        "district": "Repulse Bay",
        "tags": ["scenic_views", "relaxation", "photography"],
        "cost_tier": "low",
        "duration_hours": 2.0,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "Scenic sandy beach with clear water, great for a relaxed afternoon.",
        "opening": "Open 24h",
    },
    {
        "name": "Nan Lian Garden",
        "district": "Diamond Hill",
        "tags": ["culture", "scenic_views", "relaxation", "photography"],
        "cost_tier": "low",
        "duration_hours": 1.5,
        "mobility_friendly": True,
        "crowd_level": "low",
        "description": "Serene Tang-dynasty style garden adjacent to Chi Lin Nunnery.",
        "opening": "07:00-21:00 daily",
    },
    {
        "name": "Kennedy Town Promenade",
        "district": "Kennedy Town",
        "tags": ["local_food", "social_trendy", "scenic_views", "hidden_gems"],
        "cost_tier": "low",
        "duration_hours": 1.5,
        "mobility_friendly": True,
        "crowd_level": "low",
        "description": "Trendy neighbourhood at the western tip of HK Island with cool cafés and sea views.",
        "opening": "Open 24h",
    },

    # ── Kowloon ──────────────────────────────────────────────────────────────
    {
        "name": "Tsim Sha Tsui Promenade (Avenue of Stars)",
        "district": "Tsim Sha Tsui",
        "tags": ["scenic_views", "photography", "relaxation"],
        "cost_tier": "low",
        "duration_hours": 1.5,
        "mobility_friendly": True,
        "crowd_level": "high",
        "description": "Waterfront promenade with Victoria Harbour views and nightly Symphony of Lights show.",
        "opening": "Open 24h (show 20:00 daily)",
    },
    {
        "name": "Mong Kok Street Markets (Ladies Market / Flower Market)",
        "district": "Mong Kok",
        "tags": ["shopping", "local_food", "hidden_gems", "social_trendy"],
        "cost_tier": "low",
        "duration_hours": 2.0,
        "mobility_friendly": True,
        "crowd_level": "high",
        "description": "Bustling street markets for bargain shopping, street food, and local atmosphere.",
        "opening": "12:00-23:00 daily",
    },
    {
        "name": "Yau Ma Tei Temple Street Night Market",
        "district": "Yau Ma Tei",
        "tags": ["local_food", "culture", "hidden_gems", "social_trendy"],
        "cost_tier": "low",
        "duration_hours": 2.0,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "Atmospheric night market with street food, fortune tellers, and Cantonese opera.",
        "opening": "18:00-23:00 daily",
    },
    {
        "name": "Kowloon Walled City Park",
        "district": "Kowloon City",
        "tags": ["history", "culture", "hidden_gems", "relaxation"],
        "cost_tier": "low",
        "duration_hours": 1.5,
        "mobility_friendly": True,
        "crowd_level": "low",
        "description": "Historic park on the site of the former Walled City; peaceful with informative exhibits.",
        "opening": "06:30-23:00 daily",
    },
    {
        "name": "Sham Shui Po Electronics & Fabric Markets",
        "district": "Sham Shui Po",
        "tags": ["shopping", "hidden_gems", "local_food"],
        "cost_tier": "low",
        "duration_hours": 2.0,
        "mobility_friendly": True,
        "crowd_level": "medium",
        "description": "Budget paradise for electronics, fabrics, and local eateries beloved by locals.",
        "opening": "10:00-20:00 daily",
    },

    # ── New Territories & Outlying Islands ──────────────────────────────────
    {
        "name": "Tian Tan Buddha (Big Buddha) & Po Lin Monastery",
        "district": "Lantau Island",
        "tags": ["culture", "history", "scenic_views", "photography"],
        "cost_tier": "medium",   # Ngong Ping 360 cable car ~HKD 235 return
        "duration_hours": 4.0,
        "mobility_friendly": False,  # 268 steps to Buddha
        "crowd_level": "high",
        "description": "World's largest outdoor seated bronze Buddha atop Lantau; stunning mountain scenery.",
        "opening": "Cable car 10:00-17:30; Buddha 10:00-17:00",
    },
    {
        "name": "Tai O Fishing Village",
        "district": "Lantau Island",
        "tags": ["culture", "hidden_gems", "local_food", "photography"],
        "cost_tier": "low",
        "duration_hours": 2.5,
        "mobility_friendly": True,
        "crowd_level": "low",
        "description": "Charming stilt-house village known for shrimp paste, seafood, and pink dolphin boat tours.",
        "opening": "Open daily",
    },
    {
        "name": "Sai Kung Waterfront & Seafood",
        "district": "Sai Kung",
        "tags": ["local_food", "scenic_views", "relaxation", "hidden_gems"],
        "cost_tier": "medium",
        "duration_hours": 3.0,
        "mobility_friendly": True,
        "crowd_level": "low",
        "description": "Picturesque harbour town famed for fresh live seafood restaurants and country park access.",
        "opening": "Open daily",
    },
]

HK_HOTELS = [
    # Low budget (~HKD 200-400/night)
    {
        "name": "Mei Ho House Youth Hostel",
        "area": "Sham Shui Po",
        "budget_tier": "low",
        "price_hkd_per_night": 280,
        "mtr_minutes": 1,
        "description": "Heritage hostel in a restored 1950s estate; great MTR access.",
    },
    {
        "name": "YHA Mei Ho House",
        "area": "Sham Shui Po",
        "budget_tier": "low",
        "price_hkd_per_night": 320,
        "mtr_minutes": 2,
        "description": "Clean, well-located budget option popular with student travellers.",
    },
    {
        "name": "Chungking Mansions Guesthouses",
        "area": "Tsim Sha Tsui",
        "budget_tier": "low",
        "price_hkd_per_night": 250,
        "mtr_minutes": 3,
        "description": "Iconic backpacker location in the heart of TST; basic but central.",
    },
    {
        "name": "Mini Hotel Central",
        "area": "Central",
        "budget_tier": "low",
        "price_hkd_per_night": 380,
        "mtr_minutes": 2,
        "description": "Compact, modern rooms in prime Central location.",
    },
    # Medium budget (~HKD 600-1000/night)
    {
        "name": "Ibis Hong Kong Central & Sheung Wan",
        "area": "Sheung Wan",
        "budget_tier": "medium",
        "price_hkd_per_night": 700,
        "mtr_minutes": 2,
        "description": "Reliable mid-range chain hotel near Central with good transport links.",
    },
    {
        "name": "Hotel Ease Mong Kok",
        "area": "Mong Kok",
        "budget_tier": "medium",
        "price_hkd_per_night": 650,
        "mtr_minutes": 1,
        "description": "Modern hotel in the heart of Mong Kok; excellent for night markets.",
    },
    {
        "name": "Silka Tsuen Wan Hong Kong",
        "area": "Tsuen Wan",
        "budget_tier": "medium",
        "price_hkd_per_night": 600,
        "mtr_minutes": 2,
        "description": "Comfortable hotel slightly outside the centre with great MTR access.",
    },
    {
        "name": "Dorsett Tsuen Wan",
        "area": "Tsim Sha Tsui",
        "budget_tier": "medium",
        "price_hkd_per_night": 850,
        "mtr_minutes": 1,
        "description": "Well-appointed hotel in TST, walking distance to the promenade.",
    },
    # High budget (~HKD 1500+/night)
    {
        "name": "The Peninsula Hong Kong",
        "area": "Tsim Sha Tsui",
        "budget_tier": "high",
        "price_hkd_per_night": 4500,
        "mtr_minutes": 5,
        "description": "Legendary luxury hotel with iconic harbour views and white-glove service.",
    },
    {
        "name": "Mandarin Oriental Hong Kong",
        "area": "Central",
        "budget_tier": "high",
        "price_hkd_per_night": 3800,
        "mtr_minutes": 3,
        "description": "Award-winning luxury in Central with world-class dining.",
    },
    {
        "name": "InterContinental Grand Stanford",
        "area": "Tsim Sha Tsui",
        "budget_tier": "high",
        "price_hkd_per_night": 2200,
        "mtr_minutes": 5,
        "description": "Luxury waterfront hotel with panoramic Victoria Harbour views.",
    },
]

# Daily per-person budget benchmarks (HKD)
BUDGET_TIERS = {
    "low": {
        "transport": 50,    # MTR day pass ~HKD 55
        "food": 100,        # local cha chaan teng + street food
        "activities": 30,   # mostly free attractions
        "misc": 20,
        "total_per_person": 200,
        "hotel_per_night": 300,  # shared/hostel
    },
    "medium": {
        "transport": 80,
        "food": 200,        # mix of local & casual restaurants
        "activities": 150,
        "misc": 70,
        "total_per_person": 500,
        "hotel_per_night": 750,
    },
    "high": {
        "transport": 150,   # taxis + ferry
        "food": 500,        # fine dining
        "activities": 400,
        "misc": 200,
        "total_per_person": 1250,
        "hotel_per_night": 3000,
    },
}

# District-level transport connections (MTR-centric, travel time in minutes)
TRANSPORT = {
    ("Central", "Tsim Sha Tsui"): {"mode": "MTR / Star Ferry", "minutes": 10, "cost_hkd": 10},
    ("Central", "Mong Kok"): {"mode": "MTR", "minutes": 15, "cost_hkd": 12},
    ("Central", "Causeway Bay"): {"mode": "MTR / Tram", "minutes": 12, "cost_hkd": 9},
    ("Central", "The Peak / Central"): {"mode": "Peak Tram", "minutes": 10, "cost_hkd": 59},
    ("Tsim Sha Tsui", "Mong Kok"): {"mode": "MTR", "minutes": 8, "cost_hkd": 8},
    ("Tsim Sha Tsui", "Yau Ma Tei"): {"mode": "MTR", "minutes": 5, "cost_hkd": 6},
    ("Tsim Sha Tsui", "West Kowloon"): {"mode": "Walk / Bus", "minutes": 15, "cost_hkd": 4},
    ("Mong Kok", "Sham Shui Po"): {"mode": "MTR", "minutes": 5, "cost_hkd": 6},
    ("Mong Kok", "Diamond Hill"): {"mode": "MTR", "minutes": 12, "cost_hkd": 10},
    ("Central", "Stanley"): {"mode": "Bus 6/6X", "minutes": 40, "cost_hkd": 10},
    ("Central", "Repulse Bay"): {"mode": "Bus 6/260", "minutes": 35, "cost_hkd": 10},
    ("Tsim Sha Tsui", "Lantau Island"): {"mode": "MTR + Cable Car", "minutes": 60, "cost_hkd": 250},
    ("Central", "Sai Kung"): {"mode": "MTR + Bus", "minutes": 60, "cost_hkd": 20},
    ("Central", "Kennedy Town"): {"mode": "MTR", "minutes": 15, "cost_hkd": 8},
    ("Central", "Kowloon City"): {"mode": "Bus / Ferry", "minutes": 30, "cost_hkd": 15},
    ("Causeway Bay", "Stanley"): {"mode": "Bus 40", "minutes": 30, "cost_hkd": 8},
}

INTEREST_TAGS = [
    "culture",
    "history",
    "scenic_views",
    "photography",
    "local_food",
    "shopping",
    "relaxation",
    "hidden_gems",
    "social_trendy",
]

CONSTRAINT_TAGS = [
    "avoid_long_walking",
    "avoid_many_location_changes",
    "avoid_crowds",
    "avoid_packed_schedule",
    "avoid_outdoor_heavy",
    "avoid_expensive",
]
