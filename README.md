# dd-decider

DoorDash lunch/dinner decider.

This Streamlit app helps a group choose dinner when nobody can name what they
want yet.

The app uses photo-based "this or that" choices to turn vague cravings into a
sensory profile: fresh vs. comforting, crispy vs. saucy, familiar vs.
adventurous, reliable vs. special, and more. It then combines each diner's
answers into one group profile and recommends three matching restaurants from a
saved DoorDash restaurant list.

Restaurant data is currently a prototype layer:

- Upload a `.txt` or `.csv` list of restaurant names in the sidebar.
- The app saves that list locally as `data/restaurants.txt`.
- Until a new list is uploaded, the app keeps using the saved list.
- Restaurant profiles are inferred from name and cuisine keywords for now.

Future versions can replace the name-based matcher with richer DoorDash/menu
metadata, pricing, ratings, delivery time, and restaurant photos.
