import streamlit as st
import random

# App title
st.title("🍽️ DoorDash Decider")

# Question 1: Meals already eaten
st.header("Tell us about your day!")
meals = st.multiselect(
    "What have you had so far today?",
    ["Breakfast", "Brunch", "Lunch", "Snacks", "Dinner", "Nothing yet"]
)

# Question 2: Mood
mood = st.radio(
    "How’s your mood right now?",
    ["Excited", "Tired", "Stressed", "Lazy", "Happy", "Adventurous"]
)

# Question 3: Cravings
cuisine = st.multiselect(
    "What are you craving?",
    ["Chinese", "Italian", "Mexican", "Indian", "American", "Japanese", "Mediterranean", "Surprise me!"]
)

# Question 4: Budget
budget = st.slider("What’s your budget for this meal?", 5, 50, 20)

# Logic: Recommend a cuisine
st.header("Here’s what we think you might like:")
if "Nothing yet" in meals or not meals:
    st.write("It sounds like you’re ready for your first meal of the day!")
elif "Surprise me!" in cuisine or not cuisine:
    suggested_cuisine = random.choice(["Chinese", "Italian", "Mexican", "Indian", "American", "Japanese", "Mediterranean"])
    st.write(f"How about trying **{suggested_cuisine}**?")
else:
    suggested_cuisine = random.choice(cuisine)
    st.write(f"How about **{suggested_cuisine}** cuisine? 🍴")

st.write("Enjoy your meal!")