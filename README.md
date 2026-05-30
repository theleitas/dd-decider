# dd-decider

DoorDash lunch/dinner decider.

This Streamlit app helps a group choose dinner when nobody can name what they
want yet.

The app uses compact photo-based "this or that" choices to turn vague cravings
into a sensory profile: fresh vs. comforting, crispy vs. saucy, familiar vs.
adventurous, reliable vs. special, and more. It combines only submitted diner
answers into one group profile and recommends three restaurant hits from a saved
DoorDash restaurant list:

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
- The reset button clears diner choices without touching the saved restaurant
  list.
- Restaurant profiles are inferred from name, cuisine keywords, and any pasted
  menu hints.

Future versions can replace the name-based matcher with richer DoorDash/menu
metadata, pricing, ratings, delivery time, and restaurant photos.
