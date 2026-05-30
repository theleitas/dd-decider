from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import streamlit as st


DATA_DIR = Path("data")
RESTAURANT_LIST_PATH = DATA_DIR / "restaurants.txt"
QUESTION_IMAGE_DIR = Path("assets/food_questions")


@dataclass(frozen=True)
class Option:
    label: str
    traits: dict[str, int]


@dataclass(frozen=True)
class Question:
    prompt: str
    image: str
    left: Option
    right: Option


@dataclass(frozen=True)
class FoodStyle:
    name: str
    description: str
    examples: str
    traits: dict[str, int]


@dataclass(frozen=True)
class Restaurant:
    name: str
    profile: dict[str, int]
    tags: tuple[str, ...]
    menu_hint: str


@dataclass
class Score:
    value: int = 0
    reasons: list[str] = field(default_factory=list)


QUESTIONS = [
    Question(
        "Which one feels more right for dinner?",
        "01_comfort_fresh.png",
        Option("Cozy and grounding", {"comfort": 5, "hearty": 3, "familiar": 1}),
        Option("Bright and fresh", {"fresh": 5, "light": 3, "acidic": 2}),
    ),
    Question(
        "What texture are you chasing?",
        "02_crispy_saucy.png",
        Option("Crispy, crunchy, handheld", {"crunchy": 5, "fast": 2, "handheld": 3}),
        Option("Soft, saucy, fork-and-bowl", {"saucy": 5, "comfort": 2, "umami": 2}),
    ),
    Question(
        "What kind of flavor energy sounds better?",
        "03_spicy_savory.png",
        Option("Spicy and tangy", {"spicy": 5, "acidic": 3, "adventurous": 1}),
        Option("Gentle and savory", {"umami": 4, "comfort": 2, "familiar": 2}),
    ),
    Question(
        "What food format has the right vibe?",
        "04_handheld_bowl.png",
        Option("Handheld and easy", {"handheld": 5, "fast": 3, "familiar": 1}),
        Option("Bowl or plate", {"bowl": 4, "saucy": 2, "balanced": 2}),
    ),
    Question(
        "Where should the meal get its weight?",
        "05_carby_protein.png",
        Option("Carby and comforting", {"carby": 5, "comfort": 3, "hearty": 2}),
        Option("Protein-forward", {"protein": 5, "balanced": 2, "hearty": 1}),
    ),
    Question(
        "How do you want to feel after?",
        "06_light_indulgent.png",
        Option("Light and clean", {"light": 5, "fresh": 3, "balanced": 2}),
        Option("Indulgent and satisfied", {"indulgent": 5, "hearty": 4, "comfort": 2}),
    ),
    Question(
        "Tonight is more of a...",
        "07_familiar_adventurous.png",
        Option("Familiar favorite", {"familiar": 5, "comfort": 2, "fast": 1}),
        Option("Little adventure", {"adventurous": 5, "spicy": 1, "umami": 1}),
    ),
    Question(
        "Which flavor finish sounds better?",
        "08_glazed_herby.png",
        Option("Sweet-savory and glazed", {"sweet_savory": 5, "umami": 3, "comfort": 1}),
        Option("Acidic, herby, and zippy", {"acidic": 5, "fresh": 3, "light": 1}),
    ),
    Question(
        "What kind of table are you imagining?",
        "09_shareable_individual.png",
        Option("Shareable spread", {"shareable": 5, "social": 3, "variety": 2}),
        Option("My own perfect order", {"individual": 5, "focused": 2, "balanced": 1}),
    ),
    Question(
        "What is the ordering strategy?",
        "10_reliable_special.png",
        Option("Fast, cheap, reliable", {"fast": 5, "budget": 4, "familiar": 2}),
        Option("Special treat", {"premium": 5, "adventurous": 2, "indulgent": 1}),
    ),
]


FOOD_STYLES = [
    FoodStyle(
        "Thai or Vietnamese",
        "Bright, aromatic, saucy when needed, and great for fresh-spicy cravings.",
        "pad see ew, pho, banh mi, vermicelli bowls, green curry",
        {"fresh": 4, "spicy": 3, "adventurous": 3, "light": 2, "acidic": 3, "saucy": 2, "umami": 3},
    ),
    FoodStyle(
        "Indian",
        "Warming, saucy, spiced, filling, and very good when dinner needs to feel decisive.",
        "butter chicken, chana masala, biryani, dal, paneer tikka",
        {"comfort": 4, "spicy": 4, "hearty": 4, "saucy": 4, "adventurous": 3, "umami": 3},
    ),
    FoodStyle(
        "Mexican",
        "Flexible, high-satisfaction, easy to share, and strong on handheld or bowl formats.",
        "tacos, burrito bowls, quesadillas, enchiladas, elote",
        {"comfort": 3, "spicy": 3, "hearty": 3, "handheld": 4, "familiar": 3, "budget": 4, "fast": 4},
    ),
    FoodStyle(
        "Japanese",
        "Clean, savory, precise, and good when calm food with texture sounds right.",
        "sushi, ramen, donburi, teriyaki, udon",
        {"fresh": 3, "umami": 5, "light": 3, "comfort": 2, "protein": 3, "premium": 2, "bowl": 2},
    ),
    FoodStyle(
        "Mediterranean",
        "Fresh, balanced, herby, and filling without landing too heavily.",
        "shawarma bowls, falafel, kebabs, hummus plates, Greek salads",
        {"fresh": 4, "light": 4, "acidic": 4, "protein": 3, "shareable": 3, "balanced": 4, "budget": 2},
    ),
    FoodStyle(
        "Italian",
        "Cozy, familiar, carb-forward, and especially good for comfort-seeking groups.",
        "pizza, pasta, risotto, chicken parm, caprese sandwiches",
        {"comfort": 5, "carby": 5, "hearty": 4, "familiar": 5, "saucy": 3, "shareable": 3},
    ),
    FoodStyle(
        "Korean",
        "Bold, savory, spicy, crunchy, and satisfying when you want contrast.",
        "bibimbap, bulgogi, Korean fried chicken, kimchi stew, japchae",
        {"spicy": 4, "umami": 5, "adventurous": 3, "hearty": 3, "crunchy": 3, "sweet_savory": 3},
    ),
    FoodStyle(
        "American Comfort",
        "Direct, familiar, filling, and convenient when the goal is an easy yes.",
        "burgers, fried chicken, mac and cheese, sandwiches, barbecue",
        {"comfort": 4, "hearty": 5, "crunchy": 3, "familiar": 5, "budget": 3, "fast": 4, "indulgent": 4},
    ),
    FoodStyle(
        "Chinese",
        "Savory, shareable, reliable, and good when leftovers are part of the fantasy.",
        "dumplings, noodles, fried rice, mapo tofu, orange chicken",
        {"umami": 5, "comfort": 3, "hearty": 3, "shareable": 4, "saucy": 3, "sweet_savory": 3, "budget": 3},
    ),
]


CUISINE_KEYWORDS = {
    "Thai or Vietnamese": [
        "thai",
        "vietnam",
        "pho",
        "banh",
        "pad thai",
        "noodle",
        "curry",
        "boba",
    ],
    "Indian": ["indian", "curry", "biryani", "tandoor", "masala", "naan", "punjab", "bombay"],
    "Mexican": ["mexican", "taco", "burrito", "quesadilla", "taqueria", "cantina", "chipotle"],
    "Japanese": ["japanese", "sushi", "ramen", "teriyaki", "hibachi", "poke", "udon", "donburi"],
    "Mediterranean": ["mediterranean", "greek", "gyro", "falafel", "shawarma", "kebab", "hummus", "pita"],
    "Italian": ["italian", "pizza", "pasta", "trattoria", "parm", "risotto"],
    "Korean": ["korean", "kimchi", "bulgogi", "bibimbap", "k-bbq", "bbq chicken"],
    "American Comfort": [
        "burger",
        "chicken",
        "wing",
        "sandwich",
        "bbq",
        "barbecue",
        "diner",
        "grill",
        "sub",
        "cheesesteak",
    ],
    "Chinese": ["chinese", "dumpling", "wok", "szechuan", "sichuan", "noodle", "fried rice", "panda"],
}


MENU_KEYWORDS = {
    "pizza": ({"carby": 5, "comfort": 4, "shareable": 3, "familiar": 3}, "pizza, pasta, cheesy comfort"),
    "pasta": ({"carby": 5, "saucy": 4, "comfort": 4}, "pasta, sauces, Italian comfort"),
    "pho": ({"brothy": 5, "fresh": 3, "light": 2, "umami": 3}, "pho, brothy noodles, herbs"),
    "ramen": ({"brothy": 5, "umami": 5, "comfort": 3, "bowl": 3}, "ramen, broth, noodles"),
    "sushi": ({"fresh": 4, "light": 3, "premium": 3, "protein": 3}, "sushi, rolls, raw or cooked fish"),
    "poke": ({"fresh": 5, "light": 4, "protein": 3, "bowl": 4}, "poke bowls, fresh fish, rice"),
    "taco": ({"handheld": 5, "spicy": 3, "budget": 3, "fast": 3}, "tacos, salsas, handheld bites"),
    "burrito": ({"handheld": 4, "hearty": 4, "budget": 4, "fast": 3}, "burritos, bowls, beans, rice"),
    "burger": ({"familiar": 5, "hearty": 4, "indulgent": 4, "fast": 3}, "burgers, fries, American comfort"),
    "wing": ({"crunchy": 4, "spicy": 3, "shareable": 4, "indulgent": 3}, "wings, sauces, shareable fried food"),
    "chicken": ({"protein": 4, "familiar": 3, "fast": 2}, "chicken plates, sandwiches, bowls"),
    "bbq": ({"smoky": 5, "hearty": 5, "indulgent": 3, "shareable": 2}, "barbecue, smoked meats, hearty sides"),
    "barbecue": ({"smoky": 5, "hearty": 5, "indulgent": 3, "shareable": 2}, "barbecue, smoked meats, hearty sides"),
    "salad": ({"fresh": 5, "light": 5, "balanced": 3}, "salads, greens, lighter bowls"),
    "vegan": ({"fresh": 4, "light": 3, "adventurous": 2, "balanced": 3}, "plant-based bowls and plates"),
    "falafel": ({"fresh": 4, "acidic": 3, "crunchy": 3, "budget": 2}, "falafel, hummus, pita, herbs"),
    "shawarma": ({"protein": 4, "fresh": 3, "saucy": 2, "handheld": 3}, "shawarma, pita, rice plates"),
    "dumpling": ({"umami": 4, "shareable": 4, "comfort": 3}, "dumplings, noodles, shareable plates"),
    "noodle": ({"saucy": 3, "umami": 4, "bowl": 3, "comfort": 2}, "noodles, bowls, savory sauces"),
    "curry": ({"saucy": 5, "spicy": 3, "comfort": 4, "hearty": 3}, "curries, rice, warming sauces"),
    "biryani": ({"spicy": 3, "hearty": 5, "carby": 3, "umami": 3}, "biryani, rice dishes, Indian spices"),
    "sandwich": ({"handheld": 5, "fast": 4, "familiar": 3}, "sandwiches, subs, easy handheld orders"),
    "deli": ({"handheld": 4, "fast": 4, "familiar": 3}, "deli sandwiches, salads, quick plates"),
    "bakery": ({"indulgent": 4, "sweet_savory": 3, "comfort": 2}, "baked goods, sandwiches, treats"),
    "dessert": ({"indulgent": 5, "sweet_savory": 4, "premium": 1}, "desserts and sweet treats"),
}


SAMPLE_RESTAURANTS = [
    "Tony's Pizza & Pasta",
    "Pho Saigon Noodle House",
    "Tandoori Kitchen",
    "Sushi Garden",
    "Taqueria El Camino",
    "Mediterranean Grill",
    "Seoul Korean Chicken",
    "Golden Wok Chinese",
    "Main Street Burgers",
]


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


def parse_restaurant_text(text: str, filename: str = "restaurants.txt") -> list[str]:
    if filename.lower().endswith(".csv") or "," in text:
        rows = list(csv.DictReader(io.StringIO(text)))
        if rows:
            name_key = next((key for key in rows[0] if key and key.lower() in {"name", "restaurant", "restaurant name"}), None)
            if name_key:
                return [normalize_name(row.get(name_key, "")) for row in rows if normalize_name(row.get(name_key, ""))]

        return [
            normalize_name(row[0])
            for row in csv.reader(io.StringIO(text))
            if row and normalize_name(row[0]).lower() not in {"name", "restaurant", "restaurant name"}
        ]

    return [normalize_name(line) for line in text.splitlines() if normalize_name(line)]


def save_restaurant_names(names: list[str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    RESTAURANT_LIST_PATH.write_text("\n".join(dict.fromkeys(names)) + "\n", encoding="utf-8")


def load_restaurant_names() -> list[str]:
    if RESTAURANT_LIST_PATH.exists():
        names = [normalize_name(line) for line in RESTAURANT_LIST_PATH.read_text(encoding="utf-8").splitlines()]
        return [name for name in names if name]

    return SAMPLE_RESTAURANTS


def restaurant_text_value(names: list[str]) -> str:
    return "\n".join(names)


def add_profiles(base: dict[str, int], extra: dict[str, int], multiplier: int = 1) -> dict[str, int]:
    combined = dict(base)
    for trait, value in extra.items():
        combined[trait] = combined.get(trait, 0) + value * multiplier
    return combined


def infer_restaurant(raw_name: str) -> Restaurant:
    parts = [normalize_name(part) for part in re.split(r"\s+[|–—-]\s+|;", raw_name, maxsplit=1)]
    name = parts[0]
    details = " ".join(parts)
    lower_name = details.lower()
    profile: dict[str, int] = {"familiar": 1, "fast": 1}
    tags: list[str] = []
    menu_hints: list[str] = []

    for style in FOOD_STYLES:
        keywords = CUISINE_KEYWORDS.get(style.name, [])
        hits = sum(1 for keyword in keywords if keyword in lower_name)
        if hits:
            profile = add_profiles(profile, style.traits, multiplier=2 + hits)
            tags.append(style.name)
            menu_hints.append(style.examples)

    for keyword, (traits, hint) in MENU_KEYWORDS.items():
        if keyword in lower_name:
            profile = add_profiles(profile, traits, multiplier=2)
            menu_hints.append(hint)

    if any(word in lower_name for word in ["vegan", "salad", "juice", "fresh", "green"]):
        profile = add_profiles(profile, {"fresh": 5, "light": 4, "balanced": 3})
        tags.append("fresh-leaning")
        menu_hints.append("fresh bowls, salads, lighter options")

    if any(word in lower_name for word in ["dessert", "cream", "cookie", "donut", "bakery"]):
        profile = add_profiles(profile, {"indulgent": 5, "sweet_savory": 3, "comfort": 2})
        tags.append("treat")
        menu_hints.append("desserts, baked goods, sweet treats")

    if any(word in lower_name for word in ["express", "cafe", "deli", "market"]):
        profile = add_profiles(profile, {"fast": 3, "budget": 2})
        tags.append("quick")
        menu_hints.append("quick counter-service options")

    if not tags:
        tags.append("needs menu data")
        profile = add_profiles(profile, {"balanced": 2, "individual": 1})
        menu_hints.append("general delivery menu; needs richer menu data")

    return Restaurant(
        name=name,
        profile=profile,
        tags=tuple(dict.fromkeys(tags)),
        menu_hint="; ".join(dict.fromkeys(menu_hints[:3])),
    )


def default_diner_names() -> list[str]:
    return ["Jayme", "Diner 2", "Diner 3", "Diner 4", "Diner 5", "Diner 6"]


def initialize_state() -> None:
    st.session_state.setdefault("diner_count", 2)
    st.session_state.setdefault("diner_names", default_diner_names())
    st.session_state.setdefault("submitted_diners", {})


def calculate_diner_profile(diner_id: int, diner_name: str) -> tuple[dict[str, int], list[str]]:
    profile: dict[str, int] = {}
    reasons: list[str] = []

    mood = st.session_state[f"diner_{diner_id}_mood"]
    mood_traits = {
        "Tired": {"comfort": 3, "fast": 2, "familiar": 1},
        "Stressed": {"comfort": 3, "familiar": 2},
        "Happy": {"fresh": 2, "adventurous": 1},
        "Restless": {"adventurous": 3, "spicy": 1},
        "Focused": {"light": 2, "fresh": 1, "individual": 1},
        "Indulgent": {"hearty": 3, "comfort": 2, "indulgent": 3},
    }
    profile = add_profiles(profile, mood_traits[mood])
    reasons.append(f"{diner_name} is feeling {mood.lower()}.")

    hunger = st.session_state[f"diner_{diner_id}_hunger"]
    if hunger <= 2:
        profile = add_profiles(profile, {"light": 3, "fresh": 1})
        reasons.append(f"{diner_name} wants something lighter.")
    elif hunger >= 4:
        profile = add_profiles(profile, {"hearty": 4, "protein": 2, "comfort": 1})
        reasons.append(f"{diner_name} needs real dinner energy.")

    hard_nos = st.session_state.get(f"diner_{diner_id}_nos", [])
    if "Too spicy" in hard_nos:
        profile = add_profiles(profile, {"spicy": -8})
    if "Too heavy" in hard_nos:
        profile = add_profiles(profile, {"hearty": -5, "indulgent": -5})
    if "Expensive" in hard_nos:
        profile = add_profiles(profile, {"premium": -5, "budget": 4})
    if "Too adventurous" in hard_nos:
        profile = add_profiles(profile, {"adventurous": -5, "familiar": 3})

    for index, question in enumerate(QUESTIONS, start=1):
        answer = st.session_state[f"diner_{diner_id}_question_{index}"]
        selected = question.left if answer == question.left.label else question.right
        profile = add_profiles(profile, selected.traits)
        reasons.append(f"{diner_name} chose {selected.label.lower()}.")

    return profile, reasons


def diner_form(diner_id: int, diner_name: str) -> tuple[dict[str, int], list[str]] | None:
    submitted_diners = st.session_state["submitted_diners"]
    submitted = submitted_diners.get(diner_id)
    label = f"{diner_name} {'- submitted' if submitted else '- waiting'}"

    with st.expander(label, expanded=diner_id == 1 and not submitted):
        with st.form(f"diner_{diner_id}_form"):
            st.radio(
                "Dinner mood",
                ["Tired", "Stressed", "Happy", "Restless", "Focused", "Indulgent"],
                horizontal=True,
                key=f"diner_{diner_id}_mood",
            )
            st.slider("How hungry are you?", 1, 5, 3, key=f"diner_{diner_id}_hunger")
            st.multiselect(
                "Hard no's tonight",
                ["Too spicy", "Too heavy", "Raw fish", "Dairy-heavy", "Expensive", "Too adventurous"],
                key=f"diner_{diner_id}_nos",
            )

            st.markdown("#### Quick photo picks")
            for index, question in enumerate(QUESTIONS, start=1):
                image_path = QUESTION_IMAGE_DIR / question.image
                with st.container(border=True):
                    if image_path.exists():
                        st.image(str(image_path), width=280)
                    st.radio(
                        question.prompt,
                        [question.left.label, question.right.label],
                        horizontal=True,
                        key=f"diner_{diner_id}_question_{index}",
                    )

            if st.form_submit_button(f"Submit {diner_name}'s picks", width="stretch"):
                profile, reasons = calculate_diner_profile(diner_id, diner_name)
                submitted_diners[diner_id] = {
                    "name": diner_name,
                    "profile": profile,
                    "reasons": reasons,
                }
                st.success(f"Got {diner_name}'s picks.")

    refreshed = submitted_diners.get(diner_id)
    if refreshed:
        return refreshed["profile"], refreshed["reasons"]

    return None


def dot_score(want: dict[str, int], offer: dict[str, int]) -> int:
    return sum(want_value * offer.get(trait, 0) for trait, want_value in want.items())


def rank_food_styles(group_profile: dict[str, int]) -> list[tuple[FoodStyle, int]]:
    return sorted(
        ((style, dot_score(group_profile, style.traits)) for style in FOOD_STYLES),
        key=lambda result: result[1],
        reverse=True,
    )


def rank_restaurants(restaurants: list[Restaurant], group_profile: dict[str, int]) -> list[tuple[Restaurant, int]]:
    return sorted(
        ((restaurant, dot_score(group_profile, restaurant.profile)) for restaurant in restaurants),
        key=lambda result: result[1],
        reverse=True,
    )


def best_consensus(restaurants: list[Restaurant], diner_profiles: list[dict[str, int]]) -> tuple[Restaurant, int]:
    def score(restaurant: Restaurant) -> int:
        diner_scores = [dot_score(profile, restaurant.profile) for profile in diner_profiles]
        return min(diner_scores) * 2 + sum(diner_scores)

    return max(((restaurant, score(restaurant)) for restaurant in restaurants), key=lambda result: result[1])


def best_craving_match(restaurants: list[Restaurant], group_profile: dict[str, int]) -> tuple[Restaurant, int]:
    return max(
        ((restaurant, dot_score(group_profile, restaurant.profile)) for restaurant in restaurants),
        key=lambda result: result[1],
    )


def wildcard_match(
    restaurants: list[Restaurant],
    group_profile: dict[str, int],
    diner_profiles: list[dict[str, int]],
    used_names: set[str],
) -> tuple[Restaurant, int]:
    def score(restaurant: Restaurant) -> int:
        diner_scores = [dot_score(profile, restaurant.profile) for profile in diner_profiles]
        consensus_floor = min(diner_scores)
        curiosity_bonus = (
            restaurant.profile.get("adventurous", 0) * 8
            + restaurant.profile.get("premium", 0) * 4
            + restaurant.profile.get("variety", 0) * 5
            + restaurant.profile.get("spicy", 0) * 2
        )
        return dot_score(group_profile, restaurant.profile) + curiosity_bonus + consensus_floor

    candidates = [restaurant for restaurant in restaurants if restaurant.name not in used_names] or restaurants
    return max(((restaurant, score(restaurant)) for restaurant in candidates), key=lambda result: result[1])


def three_hits(restaurants: list[Restaurant], group_profile: dict[str, int], diner_profiles: list[dict[str, int]]) -> list[tuple[str, str, Restaurant, int]]:
    consensus_restaurant, consensus_score = best_consensus(restaurants, diner_profiles)
    used = {consensus_restaurant.name}

    craving_candidates = [restaurant for restaurant in restaurants if restaurant.name not in used] or restaurants
    craving_restaurant, craving_score = best_craving_match(craving_candidates, group_profile)
    used.add(craving_restaurant.name)

    wildcard_restaurant, wildcard_score = wildcard_match(restaurants, group_profile, diner_profiles, used)

    return [
        ("Best consensus", "Everyone likely says yes.", consensus_restaurant, consensus_score),
        ("Best craving match", "Strongest sensory fit.", craving_restaurant, craving_score),
        ("Wildcard", "A slightly more adventurous option that still fits.", wildcard_restaurant, wildcard_score),
    ]


st.set_page_config(page_title="DoorDash Decider", page_icon="🍽️", layout="centered")
initialize_state()

st.markdown(
    """
    <style>
    div[data-testid="stExpander"] details summary p {
        font-size: 1.05rem;
        font-weight: 700;
    }
    div[data-testid="stImage"] img {
        border-radius: 10px;
        max-height: 160px;
        object-fit: cover;
    }
    div[data-testid="stRadio"] label {
        padding-bottom: 0.1rem;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("DoorDash Decider")
st.caption("A visual craving compass for groups that know they want dinner but do not know what dinner is yet.")

with st.container(border=True):
    st.subheader("How this works")
    st.write(
        "This app treats craving as something people discover through comparison, not something they can always "
        "name up front. Instead of asking everyone to pick a cuisine from a giant list, it shows quick food-photo "
        "tradeoffs: cozy or fresh, crispy or saucy, familiar or adventurous, reliable or special."
    )
    st.write(
        "Each submitted diner's choices build a lightweight sensory profile. The app combines submitted diners only, "
        "then matches that group profile against your saved restaurant list."
    )

restaurant_names = load_restaurant_names()
diner_count = st.session_state["diner_count"]
diner_names = st.session_state["diner_names"]

group_profile: dict[str, int] = {}
group_reasons: list[str] = []
submitted_profiles: list[dict[str, int]] = []

st.header("Diner picks")
st.caption("Only submitted diners count toward the results.")
for diner in range(1, diner_count + 1):
    diner_name = diner_names[diner - 1] or f"Diner {diner}"
    submitted = diner_form(diner, diner_name)
    if submitted:
        profile, reasons = submitted
        group_profile = add_profiles(group_profile, profile)
        group_reasons.extend(reasons)
        submitted_profiles.append(profile)

restaurants = [infer_restaurant(name) for name in restaurant_names]

st.header("Group hits")
if not submitted_profiles:
    st.info("Have at least one diner tap Submit before the app recommends restaurants.")
else:
    style_results = rank_food_styles(group_profile)
    top_style, _style_score = style_results[0]
    st.subheader(top_style.name)
    st.write(top_style.description)
    st.write(f"Food targets: {top_style.examples}.")

    hits = three_hits(restaurants, group_profile, submitted_profiles)
    for title, explanation, restaurant, score in hits:
        with st.container(border=True):
            st.markdown(f"#### {title}")
            st.subheader(restaurant.name)
            st.caption(explanation)
            st.write(f"Match score: {score}")
            st.write(f"Likely menu: {restaurant.menu_hint}")
            st.write(f"Signals: {', '.join(restaurant.tags)}")

    with st.expander("Why the app leaned this way"):
        for reason in group_reasons[-12:]:
            st.write(f"- {reason}")

    with st.expander("Group taste profile"):
        meaningful_traits = sorted(group_profile.items(), key=lambda item: item[1], reverse=True)
        for trait, value in meaningful_traits:
            if value > 0:
                st.write(f"- {trait.replace('_', ' ')}: {value}")

st.divider()
with st.expander("Admin", expanded=False):
    st.write("Paste one restaurant per line. Add rough menu clues after a dash if you have them.")
    st.caption("Example: Sushi Garden - sushi, ramen, bento")

    with st.form("admin_form"):
        updated_restaurants = st.text_area(
            "Restaurant list",
            value=restaurant_text_value(restaurant_names),
            height=220,
        )
        updated_count = st.number_input(
            "Number of diners",
            min_value=1,
            max_value=6,
            value=st.session_state["diner_count"],
            step=1,
        )

        updated_names: list[str] = []
        for index in range(6):
            updated_names.append(
                st.text_input(
                    f"Diner {index + 1} name",
                    value=st.session_state["diner_names"][index],
                    key=f"admin_name_{index}",
                )
            )

        clear_submissions = st.checkbox("Clear submitted diner picks", value=False)

        if st.form_submit_button("Save admin settings", width="stretch"):
            names = parse_restaurant_text(updated_restaurants)
            if names:
                save_restaurant_names(names)
                st.success(f"Saved {len(names)} restaurants.")
            else:
                st.error("I could not find restaurant names in the pasted list.")

            old_count = st.session_state["diner_count"]
            old_names = st.session_state["diner_names"]
            st.session_state["diner_count"] = int(updated_count)
            st.session_state["diner_names"] = [name or f"Diner {index + 1}" for index, name in enumerate(updated_names)]

            if clear_submissions or old_count != int(updated_count) or old_names != st.session_state["diner_names"]:
                st.session_state["submitted_diners"] = {}

            st.rerun()

    st.caption(
        "Prototype note: restaurant matching is menu-aware by inference. It reads cuisine and dish clues from names "
        "or pasted details, then maps them to sensory traits."
    )
