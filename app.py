from __future__ import annotations

import csv
import base64
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import streamlit as st
from PIL import Image


DATA_DIR = Path("data")
RESTAURANT_LIST_PATH = DATA_DIR / "restaurants.txt"
CHOICE_IMAGE_DIR = Path("assets/food_choices")
BRAND_IMAGE_PATH = Path("assets/brand/leita-dining-decider.jpg")


@dataclass(frozen=True)
class Option:
    label: str
    traits: dict[str, int]
    image: str


@dataclass(frozen=True)
class Question:
    prompt: str
    options: tuple[Option, Option, Option]


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
    types: tuple[str, ...]
    menu_hint: str


@dataclass(frozen=True)
class SubmittedDiner:
    name: str
    profile: dict[str, int]
    reasons: list[str]
    types: tuple[str, ...]


@dataclass
class Score:
    value: int = 0
    reasons: list[str] = field(default_factory=list)


QUESTIONS = [
    Question(
        "Which one feels more right for dinner?",
        (
            Option("Cozy", {"comfort": 5, "hearty": 3, "familiar": 1}, "q01_a.jpg"),
            Option("Fresh", {"fresh": 5, "light": 3, "acidic": 2}, "q01_b.jpg"),
            Option("Brothy", {"brothy": 5, "comfort": 2, "umami": 2, "light": 1}, "q01_c.jpg"),
        ),
    ),
    Question(
        "What texture are you chasing?",
        (
            Option("Crispy", {"crunchy": 5, "fast": 2, "handheld": 3}, "q02_a.jpg"),
            Option("Saucy", {"saucy": 5, "comfort": 2, "umami": 2}, "q02_b.jpg"),
            Option("Creamy", {"creamy": 5, "comfort": 3, "saucy": 2, "indulgent": 2}, "q02_c.jpg"),
        ),
    ),
    Question(
        "What kind of flavor energy sounds better?",
        (
            Option("Spicy", {"spicy": 5, "acidic": 3, "adventurous": 1}, "q03_a.jpg"),
            Option("Savory", {"umami": 4, "comfort": 2, "familiar": 2}, "q03_b.jpg"),
            Option("Smoky", {"smoky": 5, "hearty": 3, "protein": 2}, "q03_c.jpg"),
        ),
    ),
    Question(
        "What food format has the right vibe?",
        (
            Option("Handheld", {"handheld": 5, "fast": 3, "familiar": 1}, "q04_a.jpg"),
            Option("Bowl", {"bowl": 4, "saucy": 2, "balanced": 2}, "q04_b.jpg"),
            Option("Small bites", {"snacky": 5, "variety": 3, "shareable": 2}, "q04_c.jpg"),
        ),
    ),
    Question(
        "Where should the meal get its weight?",
        (
            Option("Carby", {"carby": 5, "comfort": 3, "hearty": 2}, "q05_a.jpg"),
            Option("Protein", {"protein": 5, "balanced": 2, "hearty": 1}, "q05_b.jpg"),
            Option("Veggie-heavy", {"vegetable": 5, "fresh": 3, "balanced": 4, "light": 2}, "q05_c.jpg"),
        ),
    ),
    Question(
        "How do you want to feel after?",
        (
            Option("Light", {"light": 5, "fresh": 3, "balanced": 2}, "q06_a.jpg"),
            Option("Indulgent", {"indulgent": 5, "hearty": 4, "comfort": 2}, "q06_b.jpg"),
            Option("Brunchy", {"breakfast": 5, "comfort": 3, "familiar": 2}, "q06_c.jpg"),
        ),
    ),
    Question(
        "Tonight is more of a...",
        (
            Option("Familiar", {"familiar": 5, "comfort": 2, "fast": 1}, "q07_a.jpg"),
            Option("Adventurous", {"adventurous": 5, "spicy": 1, "umami": 1}, "q07_b.jpg"),
            Option("Cheesy", {"cheesy": 5, "comfort": 3, "indulgent": 2}, "q07_c.jpg"),
        ),
    ),
    Question(
        "Which flavor finish sounds better?",
        (
            Option("Glazed", {"sweet_savory": 5, "umami": 3, "comfort": 1}, "q08_a.jpg"),
            Option("Herby", {"acidic": 5, "fresh": 3, "light": 1}, "q08_b.jpg"),
            Option("Garlicky", {"garlic": 5, "umami": 3, "saucy": 1}, "q08_c.jpg"),
        ),
    ),
    Question(
        "What is the ordering strategy?",
        (
            Option("Reliable", {"fast": 5, "budget": 4, "familiar": 2}, "q09_a.jpg"),
            Option("Special", {"premium": 5, "adventurous": 2, "indulgent": 1}, "q09_b.jpg"),
            Option("Sweet finish", {"dessert": 5, "sweet_savory": 3, "indulgent": 2}, "q09_c.jpg"),
        ),
    ),
]


RESTAURANT_TYPES = {
    "🇲🇽 Mexican": {"type_mexican": 14, "spicy": 2, "handheld": 2, "bowl": 1},
    "🍝 Italian": {"type_italian": 14, "carby": 3, "saucy": 2, "comfort": 2},
    "🍔 Burgers": {"type_burgers": 14, "beef": 4, "handheld": 2, "indulgent": 2},
    "🥙 Greek": {"type_greek": 14, "fresh": 3, "acidic": 2, "protein": 2, "vegetable": 2},
    "🌶️ Thai": {"type_thai": 14, "spicy": 3, "fresh": 2, "saucy": 2, "adventurous": 1},
    "🍟 Fast Food": {"type_fast_food": 14, "fast": 5, "familiar": 2, "budget": 2},
    "🍕 Pizza": {"type_pizza": 14, "carby": 3, "cheesy": 4, "shareable": 2},
    "🍣 Japanese": {"type_japanese": 14, "fresh": 2, "umami": 3, "brothy": 1, "premium": 1},
    "🥡 Chinese": {"type_chinese": 14, "umami": 3, "saucy": 2, "shareable": 2},
    "🔥 Grill": {"type_grill": 14, "smoky": 5, "protein": 3, "hearty": 2},
    "🍽️ American": {"type_american": 14, "familiar": 4, "comfort": 2, "fast": 1},
    "🍳 Breakfast": {"type_breakfast": 14, "breakfast": 5, "comfort": 2, "familiar": 2},
    "🥪 Subs": {"type_subs": 14, "sandwich": 5, "handheld": 4, "fast": 2},
}


TYPE_NAMES = tuple(RESTAURANT_TYPES.keys())


FOOD_STYLES = [
    FoodStyle(
        "Thai or Vietnamese",
        "Bright, aromatic, saucy when needed, and great for fresh-spicy cravings.",
        "pad see ew, pho, banh mi, vermicelli bowls, green curry",
        {"fresh": 4, "spicy": 3, "adventurous": 3, "light": 2, "acidic": 3, "saucy": 2, "umami": 3, "brothy": 2, "garlic": 2},
    ),
    FoodStyle(
        "Indian",
        "Warming, saucy, spiced, filling, and very good when dinner needs to feel decisive.",
        "butter chicken, chana masala, biryani, dal, paneer tikka",
        {"comfort": 4, "spicy": 4, "hearty": 4, "saucy": 4, "creamy": 3, "adventurous": 3, "umami": 3},
    ),
    FoodStyle(
        "Mexican",
        "Flexible, high-satisfaction, easy to share, and strong on handheld or bowl formats.",
        "tacos, burrito bowls, quesadillas, enchiladas, elote",
        {"comfort": 3, "spicy": 3, "hearty": 3, "handheld": 4, "cheesy": 2, "familiar": 3, "budget": 4, "fast": 4},
    ),
    FoodStyle(
        "Japanese",
        "Clean, savory, precise, and good when calm food with texture sounds right.",
        "sushi, ramen, donburi, teriyaki, udon",
        {"fresh": 3, "umami": 5, "light": 3, "comfort": 2, "protein": 3, "premium": 2, "bowl": 2, "brothy": 3, "seafood": 2},
    ),
    FoodStyle(
        "Mediterranean",
        "Fresh, balanced, herby, and filling without landing too heavily.",
        "shawarma bowls, falafel, kebabs, hummus plates, Greek salads",
        {"fresh": 4, "light": 4, "acidic": 4, "protein": 3, "shareable": 3, "balanced": 4, "vegetable": 3, "budget": 2},
    ),
    FoodStyle(
        "Italian",
        "Cozy, familiar, carb-forward, and especially good for comfort-seeking groups.",
        "pizza, pasta, risotto, chicken parm, caprese sandwiches",
        {"comfort": 5, "carby": 5, "hearty": 4, "familiar": 5, "saucy": 3, "shareable": 3, "cheesy": 4, "creamy": 2},
    ),
    FoodStyle(
        "Korean",
        "Bold, savory, spicy, crunchy, and satisfying when you want contrast.",
        "bibimbap, bulgogi, Korean fried chicken, kimchi stew, japchae",
        {"spicy": 4, "umami": 5, "adventurous": 3, "hearty": 3, "crunchy": 3, "sweet_savory": 3, "garlic": 3},
    ),
    FoodStyle(
        "American Comfort",
        "Direct, familiar, filling, and convenient when the goal is an easy yes.",
        "burgers, fried chicken, mac and cheese, sandwiches, barbecue",
        {"comfort": 4, "hearty": 5, "crunchy": 3, "familiar": 5, "budget": 3, "fast": 4, "indulgent": 4, "smoky": 2, "breakfast": 2, "beef": 2, "chicken": 2},
    ),
    FoodStyle(
        "Chinese",
        "Savory, shareable, reliable, and good when leftovers are part of the fantasy.",
        "dumplings, noodles, fried rice, mapo tofu, orange chicken",
        {"umami": 5, "comfort": 3, "hearty": 3, "shareable": 4, "saucy": 3, "sweet_savory": 3, "budget": 3, "snacky": 2, "garlic": 2},
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


KNOWN_RESTAURANTS = {
    "chicken salad chick": (
        {"fresh": 7, "light": 6, "protein": 5, "creamy": 4, "salad": 7, "sandwich": 3, "soup": 2, "familiar": 3},
        ("salad cafe", "chicken salad", "sandwiches"),
        "chicken salad scoops, sandwiches, soups, sides, pimento cheese, salads",
    ),
    "chick-fil-a": (
        {"chicken": 8, "handheld": 5, "fast": 6, "familiar": 5, "crunchy": 3, "salad": 2},
        ("chicken", "quick service"),
        "chicken sandwiches, nuggets, salads, waffle fries",
    ),
    "panera": (
        {"soup": 5, "salad": 5, "sandwich": 5, "fresh": 3, "familiar": 4, "fast": 3},
        ("cafe", "soups", "salads"),
        "soups, salads, sandwiches, mac and cheese, bakery items",
    ),
    "cava": (
        {"fresh": 7, "bowl": 6, "vegetable": 5, "protein": 4, "acidic": 3, "light": 3},
        ("Mediterranean", "bowls"),
        "Mediterranean bowls, greens, grains, dips, grilled proteins",
    ),
    "sweetgreen": (
        {"fresh": 8, "salad": 8, "vegetable": 6, "light": 5, "balanced": 5},
        ("salads", "bowls"),
        "salads, warm bowls, greens, grains, vegetables",
    ),
    "chipotle": (
        {"bowl": 6, "handheld": 4, "hearty": 4, "budget": 4, "fast": 5, "spicy": 2},
        ("Mexican", "bowls"),
        "burritos, bowls, tacos, rice, beans, grilled proteins",
    ),
    "jersey mike": (
        {"sandwich": 8, "handheld": 7, "fast": 5, "familiar": 4},
        ("subs", "sandwiches"),
        "cold and hot subs, chips, cookies",
    ),
    "subway": (
        {"sandwich": 8, "handheld": 7, "fast": 6, "budget": 4, "familiar": 4},
        ("subs", "sandwiches"),
        "subs, wraps, salads, cookies",
    ),
    "tropical smoothie": (
        {"fresh": 5, "light": 4, "smoothie": 8, "handheld": 3, "salad": 2},
        ("smoothies", "wraps"),
        "smoothies, wraps, flatbreads, salads",
    ),
    "first watch": (
        {"breakfast": 8, "fresh": 4, "comfort": 4, "familiar": 3},
        ("breakfast", "brunch"),
        "breakfast, brunch, eggs, pancakes, salads, sandwiches",
    ),
    "panda express": (
        {"Chinese": 4, "sweet_savory": 5, "umami": 4, "fast": 6, "bowl": 4, "chicken": 3},
        ("Chinese", "quick service"),
        "orange chicken, chow mein, fried rice, bowls, plates",
    ),
    "five guys": (
        {"burger": 8, "beef": 7, "handheld": 5, "indulgent": 5, "familiar": 5},
        ("burgers", "fries"),
        "burgers, hot dogs, fries, shakes",
    ),
    "shake shack": (
        {"burger": 8, "beef": 6, "handheld": 5, "indulgent": 5, "premium": 2},
        ("burgers", "fries"),
        "burgers, chicken sandwiches, fries, shakes",
    ),
    "wingstop": (
        {"wing": 8, "chicken": 8, "crunchy": 5, "spicy": 4, "shareable": 5},
        ("wings", "chicken"),
        "wings, tenders, fries, dips",
    ),
    "zaxby": (
        {"chicken": 8, "crunchy": 5, "handheld": 3, "salad": 2, "fast": 4},
        ("chicken", "salads"),
        "chicken fingers, wings, sandwiches, salads, fries",
    ),
}


KNOWN_RESTAURANT_TYPES = {
    "chicken salad chick": ("🍽️ American", "🥪 Subs"),
    "chick-fil-a": ("🍟 Fast Food", "🍽️ American"),
    "panera": ("🍽️ American", "🥪 Subs", "🍳 Breakfast"),
    "cava": ("🥙 Greek",),
    "sweetgreen": ("🍽️ American",),
    "chipotle": ("🇲🇽 Mexican", "🍟 Fast Food"),
    "jersey mike": ("🥪 Subs",),
    "subway": ("🥪 Subs", "🍟 Fast Food"),
    "tropical smoothie": ("🍽️ American", "🥪 Subs"),
    "first watch": ("🍳 Breakfast", "🍽️ American"),
    "panda express": ("🥡 Chinese", "🍟 Fast Food"),
    "five guys": ("🍔 Burgers", "🍟 Fast Food", "🍽️ American"),
    "shake shack": ("🍔 Burgers", "🍟 Fast Food", "🍽️ American"),
    "wingstop": ("🍟 Fast Food", "🍽️ American"),
    "zaxby": ("🍟 Fast Food", "🍽️ American"),
}


TYPE_KEYWORDS = {
    "🇲🇽 Mexican": ["mexican", "taco", "burrito", "quesadilla", "taqueria", "cantina", "chipotle", "salsa"],
    "🍝 Italian": ["italian", "pasta", "trattoria", "risotto", "parm", "lasagna"],
    "🍔 Burgers": ["burger", "burgers", "five guys", "shake shack"],
    "🥙 Greek": ["greek", "gyro", "falafel", "shawarma", "hummus", "pita", "mediterranean", "kebab", "kebob"],
    "🌶️ Thai": ["thai", "pad thai", "curry", "basil", "lemongrass"],
    "🍟 Fast Food": ["express", "fast", "drive", "mcdonald", "wendy", "taco bell", "popeyes", "kfc", "zaxby"],
    "🍕 Pizza": ["pizza", "pizzeria"],
    "🍣 Japanese": ["japanese", "sushi", "ramen", "hibachi", "teriyaki", "poke", "udon"],
    "🥡 Chinese": ["chinese", "wok", "szechuan", "sichuan", "dumpling", "fried rice", "panda"],
    "🔥 Grill": ["grill", "grille", "bbq", "barbecue", "steak", "smokehouse", "kebab", "kebob"],
    "🍽️ American": ["american", "diner", "chicken salad", "wing", "wings", "chicken", "bar", "cafe"],
    "🍳 Breakfast": ["breakfast", "brunch", "egg", "pancake", "waffle", "biscuit", "first watch"],
    "🥪 Subs": ["sub", "subs", "sandwich", "deli", "hoagie", "jersey mike", "subway"],
}


MENU_KEYWORDS = {
    "pizza": ({"carby": 5, "comfort": 4, "shareable": 3, "familiar": 3}, "pizza, pasta, cheesy comfort"),
    "pasta": ({"carby": 5, "saucy": 4, "comfort": 4}, "pasta, sauces, Italian comfort"),
    "pho": ({"brothy": 5, "fresh": 3, "light": 2, "umami": 3}, "pho, brothy noodles, herbs"),
    "ramen": ({"brothy": 5, "umami": 5, "comfort": 3, "bowl": 3}, "ramen, broth, noodles"),
    "sushi": ({"fresh": 4, "light": 3, "premium": 3, "protein": 3, "seafood": 5, "raw_fish": 4}, "sushi, rolls, raw or cooked fish"),
    "poke": ({"fresh": 5, "light": 4, "protein": 3, "bowl": 4, "seafood": 5, "raw_fish": 3}, "poke bowls, fresh fish, rice"),
    "taco": ({"handheld": 5, "spicy": 3, "budget": 3, "fast": 3}, "tacos, salsas, handheld bites"),
    "burrito": ({"handheld": 4, "hearty": 4, "budget": 4, "fast": 3}, "burritos, bowls, beans, rice"),
    "burger": ({"familiar": 5, "hearty": 4, "indulgent": 4, "fast": 3, "beef": 4}, "burgers, fries, American comfort"),
    "wing": ({"crunchy": 4, "spicy": 3, "shareable": 4, "indulgent": 3, "chicken": 5}, "wings, sauces, shareable fried food"),
    "chicken": ({"protein": 4, "familiar": 3, "fast": 2, "chicken": 5}, "chicken plates, sandwiches, bowls"),
    "bbq": ({"smoky": 5, "hearty": 5, "indulgent": 3, "shareable": 2, "beef": 2, "pork": 3}, "barbecue, smoked meats, hearty sides"),
    "barbecue": ({"smoky": 5, "hearty": 5, "indulgent": 3, "shareable": 2, "beef": 2, "pork": 3}, "barbecue, smoked meats, hearty sides"),
    "salad": ({"fresh": 5, "light": 5, "balanced": 3}, "salads, greens, lighter bowls"),
    "soup": ({"soup": 5, "brothy": 3, "comfort": 2, "light": 1}, "soups and brothy comfort"),
    "chicken salad": ({"salad": 8, "fresh": 6, "light": 5, "protein": 4, "creamy": 3}, "chicken salad, scoops, sandwiches, light sides"),
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
    "egg": ({"breakfast": 5, "comfort": 2, "protein": 2}, "eggs and breakfast-for-dinner options"),
    "brunch": ({"breakfast": 5, "comfort": 2, "familiar": 2}, "brunch plates and breakfast comfort"),
    "cheese": ({"cheesy": 5, "comfort": 2, "indulgent": 2}, "cheesy comfort options"),
    "quesadilla": ({"cheesy": 5, "handheld": 3, "comfort": 2}, "quesadillas and melty handhelds"),
    "garlic": ({"garlic": 5, "umami": 2, "saucy": 1}, "garlicky savory dishes"),
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


def restaurant_text_value(names: list[str]) -> str:
    return "\n".join(names)


def add_profiles(base: dict[str, int], extra: dict[str, int], multiplier: int = 1) -> dict[str, int]:
    combined = dict(base)
    for trait, value in extra.items():
        combined[trait] = combined.get(trait, 0) + value * multiplier
    return combined


def infer_restaurant_types(lower_name: str) -> tuple[str, ...]:
    types: list[str] = []

    for known_name, known_types in KNOWN_RESTAURANT_TYPES.items():
        if known_name in lower_name:
            types.extend(known_types)
            break

    for restaurant_type, keywords in TYPE_KEYWORDS.items():
        if any(keyword in lower_name for keyword in keywords):
            types.append(restaurant_type)

    return tuple(dict.fromkeys(types))


def infer_restaurant(raw_name: str) -> Restaurant:
    parts = [normalize_name(part) for part in re.split(r"\s+[|–—-]\s+|;", raw_name, maxsplit=1)]
    name = parts[0]
    details = " ".join(parts)
    lower_name = details.lower()
    profile: dict[str, int] = {"familiar": 1, "fast": 1}
    tags: list[str] = []
    menu_hints: list[str] = []
    restaurant_types = infer_restaurant_types(lower_name)

    for restaurant_type in restaurant_types:
        profile = add_profiles(profile, RESTAURANT_TYPES[restaurant_type], multiplier=3)

    for known_name, (traits, known_tags, known_hint) in KNOWN_RESTAURANTS.items():
        if known_name in lower_name:
            profile = add_profiles(profile, traits, multiplier=4)
            tags.extend(known_tags)
            menu_hints.append(known_hint)
            break

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
    if not restaurant_types:
        restaurant_types = ("🍽️ American",)
        profile = add_profiles(profile, RESTAURANT_TYPES["🍽️ American"])

    return Restaurant(
        name=name,
        profile=profile,
        tags=tuple(dict.fromkeys(tags)),
        types=restaurant_types,
        menu_hint="; ".join(dict.fromkeys(menu_hints[:3])),
    )


def default_diner_names() -> list[str]:
    return ["Molly", "Jayme", "Benji", "Diner 4", "Diner 5", "Diner 6"]


def initialize_state() -> None:
    st.session_state.setdefault("diner_count", 3)
    st.session_state.setdefault("diner_names", default_diner_names())
    st.session_state.setdefault("submitted_diners", {})
    st.session_state.setdefault("editing_diners", {})


def reset_diner_choices() -> None:
    st.session_state["submitted_diners"] = {}
    st.session_state["editing_diners"] = {}
    for key in list(st.session_state.keys()):
        if re.match(r"^diner_\d+_", key):
            del st.session_state[key]


def calculate_diner_profile(diner_id: int, diner_name: str) -> tuple[dict[str, int], list[str]]:
    profile: dict[str, int] = {}
    reasons: list[str] = []

    selected_types = [
        restaurant_type
        for restaurant_type in TYPE_NAMES
        if st.session_state.get(f"diner_{diner_id}_type_{restaurant_type}", False)
    ]
    for restaurant_type in selected_types:
        profile = add_profiles(profile, RESTAURANT_TYPES[restaurant_type], multiplier=4)

    if selected_types:
        clean_types = ", ".join(restaurant_type.split(" ", 1)[1] for restaurant_type in selected_types)
        reasons.append(f"{diner_name}'s top restaurant types are {clean_types}.")

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
    if "Too greasy/fried" in hard_nos:
        profile = add_profiles(profile, {"crunchy": -4, "indulgent": -4, "fast": -2})
    if "Seafood" in hard_nos:
        profile = add_profiles(profile, {"seafood": -12, "raw_fish": -8, "premium": -2})
    if "Raw fish/sushi" in hard_nos:
        profile = add_profiles(profile, {"raw_fish": -12, "seafood": -3, "premium": -3})
    if "Beef" in hard_nos:
        profile = add_profiles(profile, {"beef": -10, "hearty": -1, "smoky": -2})
    if "Pork" in hard_nos:
        profile = add_profiles(profile, {"pork": -10, "smoky": -2})
    if "Chicken" in hard_nos:
        profile = add_profiles(profile, {"chicken": -10, "protein": -1})
    if "Dairy-heavy" in hard_nos:
        profile = add_profiles(profile, {"creamy": -6, "cheesy": -6, "indulgent": -2})
    if "Noodles or rice" in hard_nos:
        profile = add_profiles(profile, {"carby": -4, "bowl": -2, "brothy": -2})
    if "Sandwiches/handhelds" in hard_nos:
        profile = add_profiles(profile, {"handheld": -7, "fast": -1})
    if "Expensive" in hard_nos:
        profile = add_profiles(profile, {"premium": -5, "budget": 4})
    if "Too adventurous" in hard_nos:
        profile = add_profiles(profile, {"adventurous": -5, "familiar": 3})

    for index, question in enumerate(QUESTIONS, start=1):
        answer = st.session_state[f"diner_{diner_id}_question_{index}"]
        selected = next(option for option in question.options if option.label == answer)
        profile = add_profiles(profile, selected.traits)
        reasons.append(f"{diner_name} chose {selected.label.lower()}.")

    return profile, reasons


def diner_form(diner_id: int, diner_name: str) -> tuple[dict[str, int], list[str]] | None:
    submitted_diners = st.session_state["submitted_diners"]
    editing_diners = st.session_state["editing_diners"]
    submitted = submitted_diners.get(diner_id)
    is_editing = editing_diners.get(diner_id, False)

    if submitted and not is_editing:
        st.markdown(
            f"""
            <div class="done-card">
                <strong>{diner_name} has made their choices.</strong>
                <span>Ready for the group match.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Edit", key=f"edit_diner_{diner_id}", type="primary"):
            editing_diners[diner_id] = True
            st.rerun()
        return submitted["profile"], submitted["reasons"]

    label = (
        f"Editing {diner_name}'s choices"
        if is_editing
        else f"{diner_name}, what are you craving to eat?"
    )

    with st.expander(label, expanded=is_editing):
        with st.form(f"diner_{diner_id}_form"):
            st.markdown("#### Pick 3 restaurant types")
            picked_count = sum(
                1 for restaurant_type in TYPE_NAMES if st.session_state.get(f"diner_{diner_id}_type_{restaurant_type}")
            )
            type_columns = st.columns(3)
            for index, restaurant_type in enumerate(TYPE_NAMES):
                key = f"diner_{diner_id}_type_{restaurant_type}"
                is_checked = st.session_state.get(key, False)
                with type_columns[index % 3]:
                    st.checkbox(
                        restaurant_type,
                        key=key,
                        disabled=not is_checked and picked_count >= 3,
                    )
            st.caption("Pick up to 3. These carry the most weight.")

            st.radio(
                "Dinner mood",
                ["Tired", "Stressed", "Happy", "Restless", "Focused", "Indulgent"],
                horizontal=True,
                key=f"diner_{diner_id}_mood",
            )
            st.slider("How hungry are you?", 1, 5, 3, key=f"diner_{diner_id}_hunger")
            st.multiselect(
                "Hard no's tonight",
                [
                    "Too spicy",
                    "Too heavy",
                    "Too greasy/fried",
                    "Seafood",
                    "Raw fish/sushi",
                    "Beef",
                    "Pork",
                    "Chicken",
                    "Dairy-heavy",
                    "Noodles or rice",
                    "Sandwiches/handhelds",
                    "Expensive",
                    "Too adventurous",
                ],
                key=f"diner_{diner_id}_nos",
            )

            st.markdown("#### Quick photo picks")
            for index, question in enumerate(QUESTIONS, start=1):
                with st.container(border=True):
                    st.markdown('<div class="tight-photo-picks"></div>', unsafe_allow_html=True)
                    st.caption(question.prompt)
                    cols = st.columns(3)
                    for column, option in zip(cols, question.options):
                        image_path = CHOICE_IMAGE_DIR / option.image
                        with column:
                            if image_path.exists():
                                st.markdown('<div class="choice-img">', unsafe_allow_html=True)
                                st.image(str(image_path), width="stretch")
                                st.markdown("</div>", unsafe_allow_html=True)
                    st.radio(
                        question.prompt,
                        [option.label for option in question.options],
                        horizontal=True,
                        key=f"diner_{diner_id}_question_{index}",
                        label_visibility="collapsed",
                    )

            if st.form_submit_button(f"Submit {diner_name}'s picks", width="stretch"):
                profile, reasons = calculate_diner_profile(diner_id, diner_name)
                selected_types = tuple(
                    restaurant_type
                    for restaurant_type in TYPE_NAMES
                    if st.session_state.get(f"diner_{diner_id}_type_{restaurant_type}", False)
                )
                submitted_diners[diner_id] = {
                    "name": diner_name,
                    "profile": profile,
                    "reasons": reasons,
                    "types": selected_types,
                }
                editing_diners[diner_id] = False
                st.rerun()

    refreshed = submitted_diners.get(diner_id)
    if refreshed:
        return refreshed["profile"], refreshed["reasons"]

    return None


def dot_score(want: dict[str, int], offer: dict[str, int]) -> int:
    raw = sum(want_value * offer.get(trait, 0) for trait, want_value in want.items())
    offer_strength = sum(value * value for value in offer.values() if value > 0) ** 0.5
    want_strength = sum(value * value for value in want.values() if value > 0) ** 0.5
    if not offer_strength or not want_strength:
        return raw

    # Normalize so broad menus do not always beat specific craving matches.
    return round(100 * raw / (offer_strength * want_strength))


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


def type_match_summary(submitted_diners: list[SubmittedDiner]) -> None:
    type_counts: dict[str, int] = {}
    for diner in submitted_diners:
        for restaurant_type in diner.types:
            type_counts[restaurant_type] = type_counts.get(restaurant_type, 0) + 1

    shared_types = [
        restaurant_type
        for restaurant_type, _count in sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))
        if type_counts[restaurant_type] > 1
    ]

    st.markdown('<div class="type-summary">', unsafe_allow_html=True)
    st.markdown("#### Group type overlap")
    if shared_types:
        st.markdown("".join(f'<span class="type-chip">{restaurant_type}</span>' for restaurant_type in shared_types), unsafe_allow_html=True)
    else:
        st.caption("No exact overlap yet; the app is looking for restaurants that bridge the individual picks.")

    for diner in submitted_diners:
        pieces = []
        for restaurant_type in diner.types:
            clean_type = restaurant_type.split(" ", 1)[1]
            pieces.append(f"<mark>{clean_type}</mark>" if restaurant_type in shared_types else clean_type)
        picks = ", ".join(pieces) if pieces else "no type picks"
        st.markdown(f'<div class="diner-type-row"><strong>{diner.name}:</strong> {picks}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


page_icon = Image.open(BRAND_IMAGE_PATH) if BRAND_IMAGE_PATH.exists() else "🍽️"
st.set_page_config(page_title="Leita Dining Decider", page_icon=page_icon, layout="centered")
initialize_state()

st.markdown(
    """
    <meta property="og:title" content="Leita Dining Decider">
    <meta property="og:description" content="A visual craving compass for group dinner decisions.">
    <style>
    .done-card {
        background: #176c3a;
        border: 1px solid #35b36d;
        border-radius: 10px;
        color: white;
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
        margin: 0.45rem 0 0.25rem;
        padding: 0.85rem 0.95rem;
    }
    .done-card span {
        color: #d5f7e2;
        font-size: 0.9rem;
    }
    div[data-testid="stExpander"] details summary p {
        font-size: 1.05rem;
        font-weight: 700;
    }
    .hero-img {
        border-radius: 14px;
        display: block;
        margin: 0 auto 1rem;
        width: 100%;
    }
    .choice-img img {
        aspect-ratio: 1.25 / 1;
        border-radius: 10px;
        object-fit: cover;
        width: 100%;
    }
    div[data-testid="stVerticalBlock"]:has(.tight-photo-picks) div[data-testid="stRadio"] {
        margin-top: -0.75rem;
    }
    div[data-testid="stVerticalBlock"]:has(.tight-photo-picks) div[data-testid="stRadio"] > label {
        display: none;
    }
    .type-summary {
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 10px;
        margin-bottom: 0.75rem;
        padding: 0.75rem;
    }
    .type-chip {
        background: rgba(255, 75, 75, 0.14);
        border: 1px solid rgba(255, 75, 75, 0.55);
        border-radius: 999px;
        display: inline-block;
        font-size: 0.86rem;
        font-weight: 700;
        margin: 0.12rem 0.2rem 0.12rem 0;
        padding: 0.12rem 0.5rem;
    }
    .diner-type-row {
        font-size: 0.9rem;
        margin-top: 0.2rem;
    }
    .diner-type-row mark {
        border-radius: 999px;
        padding: 0.05rem 0.32rem;
    }
    div[data-testid="stImage"] img {
        border-radius: 10px;
        max-height: 92px;
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

if BRAND_IMAGE_PATH.exists():
    hero_image = base64.b64encode(BRAND_IMAGE_PATH.read_bytes()).decode("ascii")
    st.markdown(
        f'<img class="hero-img" src="data:image/jpeg;base64,{hero_image}" alt="Leita Dining Decider">',
        unsafe_allow_html=True,
    )

st.title("Leita Dining Decider")
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
submitted_diner_models: list[SubmittedDiner] = []

st.header("Diner picks")
st.caption("Only submitted diners count toward the results.")
if st.button("Reset diner choices", type="secondary", width="stretch"):
    reset_diner_choices()
    st.rerun()

for diner in range(1, diner_count + 1):
    diner_name = diner_names[diner - 1] or f"Diner {diner}"
    submitted = diner_form(diner, diner_name)
    if submitted:
        profile, reasons = submitted
        submitted_record = st.session_state["submitted_diners"][diner]
        group_profile = add_profiles(group_profile, profile)
        group_reasons.extend(reasons)
        submitted_profiles.append(profile)
        submitted_diner_models.append(
            SubmittedDiner(
                name=submitted_record["name"],
                profile=profile,
                reasons=reasons,
                types=tuple(submitted_record.get("types", ())),
            )
        )

restaurants = [infer_restaurant(name) for name in restaurant_names]

st.header("Results")
if not submitted_profiles:
    st.info("Have at least one diner tap Submit before the app recommends restaurants.")
else:
    type_match_summary(submitted_diner_models)

    hits = three_hits(restaurants, group_profile, submitted_profiles)
    for title, explanation, restaurant, score in hits:
        with st.container(border=True):
            st.markdown(f"#### {title}")
            st.subheader(restaurant.name)
            st.caption(explanation)
            st.write(f"Match score: {score}")
            if restaurant.types:
                st.write(f"Types: {', '.join(restaurant_type.split(' ', 1)[1] for restaurant_type in restaurant.types)}")
            st.write(f"Likely menu: {restaurant.menu_hint}")
            st.write(f"Signals: {', '.join(restaurant.tags)}")

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
