# Leita Dining Decider

Group dinner decider for DoorDash nights.

This Streamlit app helps a group choose dinner when nobody can name what they
want yet.

The app uses compact three-choice photo questions to turn vague cravings into a
sensory profile: fresh vs. comforting vs. brothy, crispy vs. saucy vs. creamy,
familiar vs. adventurous vs. cheesy, and more. It combines only submitted diner
answers into one group profile and recommends three restaurant hits from a saved
DoorDash restaurant list:

Each diner first picks up to three restaurant types from compact checkbox
buttons. Those type picks carry the most weight, and the photo questions refine
the group consensus.

- Best consensus: everyone likely says yes.
- Best craving match: strongest sensory fit.
- Wildcard: slightly adventurous but still inside the group constraints.

The bottom Admin section controls setup:

- Paste a restaurant list into the Admin section.
- The app saves that list locally as `data/restaurants.txt`.
- Until a new list is uploaded, the app keeps using the saved list.
- Diner names and number of diners are customizable there too.
- Diner cards start collapsed, can be reopened and resubmitted, and only count
  after that diner taps submit.
- Submitted diners show a completed state and can edit their choices.
- Submitted diner choices are shared across phones using server-side app state,
  so one diner can submit from their phone and the group can tap Refresh group
  results to see the latest picks.
- Photo questions start unselected; skipped photos do not affect the algorithm.
- Hard no's use a choose-any grid and only apply after that diner submits.
- The reset button clears diner choices without touching the saved restaurant
  list.
- Restaurant profiles are inferred from name, cuisine keywords, and any pasted
  menu hints.
- Restaurant types are re-inferred every time the Admin restaurant list changes.
- The Leita Dining Decider image is used at the top of the page and as the app
  icon where Streamlit supports it.

Future versions can replace the name-based matcher with richer DoorDash/menu
metadata, pricing, ratings, delivery time, and restaurant photos.
