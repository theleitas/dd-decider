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


def parse_restaurant_upload(file_bytes: bytes, filename: str) -> list[str]:
    text = file_bytes.decode("utf-8-sig", errors="ignore")
    if filename.lower().endswith(".csv"):
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


def add_profiles(base: dict[str, int], extra: dict[str, int], multiplier: int = 1) -> dict[str, int]:
    combined = dict(base)
    for trait, value in extra.items():
        combined[trait] = combined.get(trait, 0) + value * multiplier
    return combined


def infer_restaurant(name: str) -> Restaurant:
    lower_name = name.lower()
    profile: dict[str, int] = {"familiar": 1, "fast": 1}
    tags: list[str] = []

    for style in FOOD_STYLES:
        keywords = CUISINE_KEYWORDS.get(style.name, [])
        hits = sum(1 for keyword in keywords if keyword in lower_name)
        if hits:
            profile = add_profiles(profile, style.traits, multiplier=2 + hits)
            tags.append(style.name)

    if any(word in lower_name for word in ["vegan", "salad", "juice", "fresh", "green"]):
        profile = add_profiles(profile, {"fresh": 5, "light": 4, "balanced": 3})
        tags.append("fresh-leaning")

    if any(word in lower_name for word in ["dessert", "cream", "cookie", "donut", "bakery"]):
        profile = add_profiles(profile, {"indulgent": 5, "sweet_savory": 3, "comfort": 2})
        tags.append("treat")

    if any(word in lower_name for word in ["express", "cafe", "deli", "market"]):
        profile = add_profiles(profile, {"fast": 3, "budget": 2})
        tags.append("quick")

    if not tags:
        tags.append("needs menu data")
        profile = add_profiles(profile, {"balanced": 2, "individual": 1})

    return Restaurant(name=name, profile=profile, tags=tuple(dict.fromkeys(tags)))


def diner_profile(diner_number: int) -> tuple[dict[str, int], list[str]]:
    profile: dict[str, int] = {}
    reasons: list[str] = []

    with st.expander(f"Diner {diner_number}", expanded=diner_number == 1):
        mood = st.radio(
            "What is your dinner mood?",
            ["Tired", "Stressed", "Happy", "Restless", "Focused", "Indulgent"],
            horizontal=True,
            key=f"diner_{diner_number}_mood",
        )
        mood_traits = {
            "Tired": {"comfort": 3, "fast": 2, "familiar": 1},
            "Stressed": {"comfort": 3, "familiar": 2},
            "Happy": {"fresh": 2, "adventurous": 1},
            "Restless": {"adventurous": 3, "spicy": 1},
            "Focused": {"light": 2, "fresh": 1, "individual": 1},
            "Indulgent": {"hearty": 3, "comfort": 2, "indulgent": 3},
        }
        profile = add_profiles(profile, mood_traits[mood])
        reasons.append(f"Diner {diner_number} is feeling {mood.lower()}.")

        hunger = st.slider("How hungry are you?", 1, 5, 3, key=f"diner_{diner_number}_hunger")
        if hunger <= 2:
            profile = add_profiles(profile, {"light": 3, "fresh": 1})
            reasons.append(f"Diner {diner_number} wants something lighter.")
        elif hunger >= 4:
            profile = add_profiles(profile, {"hearty": 4, "protein": 2, "comfort": 1})
            reasons.append(f"Diner {diner_number} needs real dinner energy.")

        hard_nos = st.multiselect(
            "Hard no's tonight",
            ["Too spicy", "Too heavy", "Raw fish", "Dairy-heavy", "Expensive", "Too adventurous"],
            key=f"diner_{diner_number}_nos",
        )
        if "Too spicy" in hard_nos:
            profile = add_profiles(profile, {"spicy": -8})
        if "Too heavy" in hard_nos:
            profile = add_profiles(profile, {"hearty": -5, "indulgent": -5})
        if "Expensive" in hard_nos:
            profile = add_profiles(profile, {"premium": -5, "budget": 4})
        if "Too adventurous" in hard_nos:
            profile = add_profiles(profile, {"adventurous": -5, "familiar": 3})

        st.markdown("#### This or that")
        for index, question in enumerate(QUESTIONS, start=1):
            image_path = QUESTION_IMAGE_DIR / question.image
            if image_path.exists():
                st.image(str(image_path), width="stretch")

            answer = st.radio(
                question.prompt,
                [question.left.label, question.right.label],
                horizontal=True,
                key=f"diner_{diner_number}_question_{index}",
            )
            selected = question.left if answer == question.left.label else question.right
            profile = add_profiles(profile, selected.traits)
            reasons.append(f"Diner {diner_number} chose {selected.label.lower()}.")

    return profile, reasons


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


st.set_page_config(page_title="DoorDash Decider", page_icon="🍽️", layout="wide")

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
        "Each choice builds a lightweight sensory profile. The group profile is then matched against the restaurants "
        "available to you. Right now restaurant profiles are inferred from restaurant names and cuisine clues; later, "
        "this can get much smarter with menu items, DoorDash metadata, photos, prices, ratings, and delivery time."
    )

with st.sidebar:
    st.header("Restaurant list")
    uploaded_file = st.file_uploader("Upload DoorDash restaurants", type=["txt", "csv"])
    if uploaded_file:
        names = parse_restaurant_upload(uploaded_file.getvalue(), uploaded_file.name)
        if names:
            save_restaurant_names(names)
            st.success(f"Saved {len(names)} restaurants.")
        else:
            st.error("I could not find restaurant names in that file.")

    restaurant_names = load_restaurant_names()
    source = "uploaded list" if RESTAURANT_LIST_PATH.exists() else "sample list"
    st.write(f"Using {len(restaurant_names)} restaurants from the {source}.")
    with st.expander("Preview restaurants"):
        for restaurant_name in restaurant_names[:30]:
            st.write(restaurant_name)
        if len(restaurant_names) > 30:
            st.write(f"...and {len(restaurant_names) - 30} more.")

diners = st.slider("How many people are deciding?", 1, 6, 2)

group_profile: dict[str, int] = {}
group_reasons: list[str] = []
for diner in range(1, diners + 1):
    profile, reasons = diner_profile(diner)
    group_profile = add_profiles(group_profile, profile)
    group_reasons.extend(reasons)

restaurants = [infer_restaurant(name) for name in restaurant_names]
style_results = rank_food_styles(group_profile)
restaurant_results = rank_restaurants(restaurants, group_profile)

st.header("Group match")

top_style, _style_score = style_results[0]
st.subheader(top_style.name)
st.write(top_style.description)
st.write(f"Food targets: {top_style.examples}.")

cols = st.columns(3)
for column, (restaurant, score) in zip(cols, restaurant_results[:3]):
    with column:
        st.metric(restaurant.name, f"{score} match")
        st.write(", ".join(restaurant.tags))

with st.expander("Why the app leaned this way"):
    for reason in group_reasons[-12:]:
        st.write(f"- {reason}")

with st.expander("Group taste profile"):
    meaningful_traits = sorted(group_profile.items(), key=lambda item: item[1], reverse=True)
    for trait, value in meaningful_traits:
        if value > 0:
            st.write(f"- {trait.replace('_', ' ')}: {value}")

st.divider()
st.caption("Prototype note: the current restaurant matcher is name-based. The next leap is menu-aware restaurant profiling.")
