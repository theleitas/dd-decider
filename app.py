from dataclasses import dataclass, field

import streamlit as st


@dataclass(frozen=True)
class FoodStyle:
    name: str
    description: str
    examples: str
    traits: dict[str, int]


@dataclass
class Score:
    value: int = 0
    reasons: list[str] = field(default_factory=list)


FOOD_STYLES = [
    FoodStyle(
        "Thai or Vietnamese",
        "Bright, aromatic, a little punchy, and easy to tune lighter or richer.",
        "pad see ew, pho, banh mi, vermicelli bowls, green curry",
        {
            "fresh": 4,
            "spicy": 3,
            "adventurous": 3,
            "light": 2,
            "umami": 3,
            "comfort": 1,
            "budget": 2,
            "fast": 2,
        },
    ),
    FoodStyle(
        "Indian",
        "Deeply flavorful, warming, filling, and great when you want dinner to feel decisive.",
        "butter chicken, chana masala, biryani, dal, paneer tikka",
        {
            "comfort": 4,
            "spicy": 4,
            "hearty": 4,
            "adventurous": 3,
            "umami": 3,
            "budget": 2,
        },
    ),
    FoodStyle(
        "Mexican",
        "Flexible, satisfying, and good for big flavor without overthinking the order.",
        "tacos, burrito bowls, quesadillas, enchiladas, elote",
        {
            "comfort": 3,
            "spicy": 3,
            "hearty": 3,
            "crunchy": 2,
            "familiar": 3,
            "budget": 4,
            "fast": 4,
        },
    ),
    FoodStyle(
        "Japanese",
        "Clean, savory, precise, and especially good when you want calm food with texture.",
        "sushi, ramen, donburi, teriyaki, udon",
        {
            "fresh": 3,
            "umami": 4,
            "light": 3,
            "comfort": 2,
            "familiar": 2,
            "adventurous": 2,
            "fast": 2,
        },
    ),
    FoodStyle(
        "Mediterranean",
        "Fresh, balanced, filling without feeling heavy, and friendly to mixed cravings.",
        "shawarma bowls, falafel, kebabs, hummus plates, Greek salads",
        {
            "fresh": 4,
            "light": 4,
            "hearty": 2,
            "familiar": 2,
            "budget": 3,
            "fast": 3,
        },
    ),
    FoodStyle(
        "Italian",
        "Cozy, familiar, and carb-forward when the evening calls for comfort.",
        "pizza, pasta, risotto, chicken parm, caprese sandwiches",
        {
            "comfort": 5,
            "hearty": 4,
            "familiar": 5,
            "umami": 2,
            "budget": 2,
        },
    ),
    FoodStyle(
        "Korean",
        "Bold, savory, spicy, and highly satisfying when you want contrast and heat.",
        "bibimbap, bulgogi, fried chicken, kimchi stew, japchae",
        {
            "spicy": 4,
            "umami": 5,
            "adventurous": 3,
            "hearty": 3,
            "crunchy": 2,
        },
    ),
    FoodStyle(
        "American Comfort",
        "Direct, familiar, and satisfying when convenience is doing real work.",
        "burgers, fried chicken, mac and cheese, sandwiches, barbecue",
        {
            "comfort": 4,
            "hearty": 5,
            "crunchy": 3,
            "familiar": 5,
            "budget": 3,
            "fast": 4,
        },
    ),
    FoodStyle(
        "Chinese",
        "Savory, shareable, reliable, and great when you want strong flavor plus leftovers.",
        "dumplings, noodles, fried rice, mapo tofu, orange chicken",
        {
            "umami": 5,
            "comfort": 3,
            "hearty": 3,
            "familiar": 3,
            "spicy": 2,
            "budget": 3,
            "fast": 3,
        },
    ),
]


PAIRWISE_QUESTIONS = [
    {
        "label": "Right now, would you rather eat something...",
        "left": "Cozy and grounding",
        "right": "Bright and fresh",
        "left_traits": {"comfort": 4, "hearty": 2},
        "right_traits": {"fresh": 4, "light": 2},
    },
    {
        "label": "Which sounds better?",
        "left": "Soft, saucy, fork-and-bowl food",
        "right": "Crispy, crunchy, handheld food",
        "left_traits": {"comfort": 2, "umami": 2, "hearty": 1},
        "right_traits": {"crunchy": 4, "fast": 2},
    },
    {
        "label": "Your ideal flavor direction is...",
        "left": "Savory and umami",
        "right": "Spicy and tangy",
        "left_traits": {"umami": 4, "comfort": 1},
        "right_traits": {"spicy": 4, "fresh": 2},
    },
    {
        "label": "How should dinner leave you feeling?",
        "left": "Light, clean, and still mobile",
        "right": "Full, settled, and done for the night",
        "left_traits": {"light": 4, "fresh": 2},
        "right_traits": {"hearty": 4, "comfort": 2},
    },
    {
        "label": "Tonight feels like a night for...",
        "left": "A familiar favorite",
        "right": "A little adventure",
        "left_traits": {"familiar": 4, "comfort": 1},
        "right_traits": {"adventurous": 4, "spicy": 1},
    },
]


def add_traits(scores: dict[str, Score], traits: dict[str, int], reason: str) -> None:
    for style in FOOD_STYLES:
        contribution = sum(style.traits.get(trait, 0) * weight for trait, weight in traits.items())
        if contribution:
            scores[style.name].value += contribution
            scores[style.name].reasons.append(reason)


def add_craving(scores: dict[str, Score], craving: str) -> None:
    craving_traits = {
        "Fresh": {"fresh": 3, "light": 2},
        "Spicy": {"spicy": 4},
        "Comforting": {"comfort": 4, "hearty": 2},
        "Crunchy": {"crunchy": 4},
        "Savory": {"umami": 4},
        "Light": {"light": 4, "fresh": 2},
        "Filling": {"hearty": 4},
        "Surprise me": {"adventurous": 3},
    }
    traits = craving_traits.get(craving)
    if traits:
        add_traits(scores, traits, f"You said {craving.lower()} sounds good.")


def score_budget(scores: dict[str, Score], budget: int) -> None:
    if budget <= 15:
        add_traits(scores, {"budget": 4, "fast": 2}, "Your budget points toward high-value delivery options.")
    elif budget <= 28:
        add_traits(scores, {"budget": 2}, "Your budget leaves room for most casual dinner options.")
    else:
        add_traits(scores, {"adventurous": 1, "umami": 1}, "Your budget can support a more specific craving.")


def score_day_context(scores: dict[str, Score], meals: list[str], mood: str, energy: int) -> None:
    if "Nothing yet" in meals or not meals:
        add_traits(scores, {"hearty": 3, "comfort": 2}, "You may need something substantial.")
    elif "Snacks" in meals and "Dinner" not in meals:
        add_traits(scores, {"hearty": 2, "umami": 1}, "Snacks are not dinner, despite their confidence.")

    mood_traits = {
        "Tired": {"comfort": 3, "fast": 2},
        "Stressed": {"comfort": 3, "familiar": 2},
        "Happy": {"fresh": 2, "adventurous": 1},
        "Restless": {"adventurous": 3, "spicy": 1},
        "Focused": {"light": 2, "fresh": 1},
        "Indulgent": {"hearty": 3, "comfort": 2},
    }
    add_traits(scores, mood_traits[mood], f"Your mood reads as {mood.lower()}.")

    if energy <= 2:
        add_traits(scores, {"fast": 3, "familiar": 2, "comfort": 1}, "Low energy favors easy decisions.")
    elif energy >= 4:
        add_traits(scores, {"adventurous": 2, "fresh": 1}, "Higher energy makes novelty more appealing.")


def ranked_results(
    meals: list[str],
    mood: str,
    energy: int,
    cravings: list[str],
    budget: int,
    choices: list[dict[str, int]],
) -> list[tuple[FoodStyle, Score]]:
    scores = {style.name: Score() for style in FOOD_STYLES}

    score_day_context(scores, meals, mood, energy)
    score_budget(scores, budget)

    for craving in cravings:
        add_craving(scores, craving)

    for answer in choices:
        add_traits(scores, answer["traits"], answer["reason"])

    return sorted(
        ((style, scores[style.name]) for style in FOOD_STYLES),
        key=lambda result: result[1].value,
        reverse=True,
    )


st.set_page_config(page_title="DoorDash Decider", page_icon="🍽️")

st.title("🍽️ DoorDash Decider")
st.caption("A dinner narrowing tool for the moment when everything sounds possible and nothing sounds obvious.")

st.header("First, what kind of day are we dealing with?")

meals = st.multiselect(
    "What have you had so far today?",
    ["Breakfast", "Brunch", "Lunch", "Snacks", "Dinner", "Nothing yet"],
)

left, right = st.columns(2)
with left:
    mood = st.radio(
        "What is the current dinner mood?",
        ["Tired", "Stressed", "Happy", "Restless", "Focused", "Indulgent"],
    )

with right:
    energy = st.slider("How much ordering energy do you have?", 1, 5, 3)
    budget = st.slider("Budget for this meal", 8, 60, 24)

cravings = st.multiselect(
    "Any cravings already floating around?",
    ["Fresh", "Spicy", "Comforting", "Crunchy", "Savory", "Light", "Filling", "Surprise me"],
)

st.header("Now choose between these")

pairwise_answers = []
for index, question in enumerate(PAIRWISE_QUESTIONS, start=1):
    answer = st.radio(
        question["label"],
        [question["left"], question["right"]],
        key=f"pairwise_{index}",
        horizontal=True,
    )
    if answer == question["left"]:
        pairwise_answers.append(
            {
                "traits": question["left_traits"],
                "reason": f"You chose {question['left'].lower()}.",
            }
        )
    else:
        pairwise_answers.append(
            {
                "traits": question["right_traits"],
                "reason": f"You chose {question['right'].lower()}.",
            }
        )

results = ranked_results(meals, mood, energy, cravings, budget, pairwise_answers)
winner, winner_score = results[0]

st.header("Your dinner direction")

st.subheader(winner.name)
st.write(winner.description)
st.write(f"Good targets: {winner.examples}.")

with st.expander("Why this matched"):
    for reason in list(dict.fromkeys(winner_score.reasons))[:5]:
        st.write(f"- {reason}")

runner_ups = ", ".join(style.name for style, _score in results[1:4])
st.write(f"Runner-ups: {runner_ups}.")

st.divider()
st.caption("Next version: swap these food styles for actual DoorDash restaurants near you.")
