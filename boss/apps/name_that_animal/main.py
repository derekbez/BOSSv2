"""Name That Animal mini-app.

Shows a random animal name + diet from Zoo Animal API with fallback data.
"""
from __future__ import annotations
import time
import random
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://zoo-animal-api.herokuapp.com/animals/rand"

# Fallback animal data for when the API is unavailable
FALLBACK_ANIMALS = [
    {"name": "Lion", "diet": "Carnivore - primarily hunts large ungulates like zebras, wildebeest, and buffalo. An apex predator that lives in social groups called prides."},
    {"name": "Elephant", "diet": "Herbivore - feeds on grasses, bark, fruits, and leaves. Can consume up to 300 pounds of vegetation daily."},
    {"name": "Penguin", "diet": "Carnivore - primarily fish, krill, and squid. Excellent swimmers that hunt underwater."},
    {"name": "Giraffe", "diet": "Herbivore - mainly acacia leaves from tall trees. Their long necks allow them to reach food other animals cannot."},
    {"name": "Panda", "diet": "Herbivore - 99% bamboo, though they occasionally eat other plants, fish, and small animals."},
    {"name": "Cheetah", "diet": "Carnivore - primarily small to medium-sized antelopes. The fastest land animal, capable of reaching 70 mph."},
    {"name": "Koala", "diet": "Herbivore - almost exclusively eucalyptus leaves. Very selective, eating only certain species of eucalyptus."},
    {"name": "Polar Bear", "diet": "Carnivore - primarily seals, especially ringed seals. Also fish, seabirds, and whale carcasses."},
    {"name": "Orangutan", "diet": "Omnivore - mainly fruits, also bark, insects, and occasionally bird eggs. Spends most time in trees."},
    {"name": "Sea Turtle", "diet": "Omnivore - varies by species; some eat jellyfish and soft-bodied animals, others eat seagrasses and algae."},
    {"name": "Wolf", "diet": "Carnivore - large ungulates like deer, elk, and moose. Pack hunters with complex social structures."},
    {"name": "Hummingbird", "diet": "Omnivore - primarily nectar from flowers, also small insects and spiders for protein. Extremely high metabolism."},
    {"name": "Octopus", "diet": "Carnivore - crabs, fish, mollusks, and shrimp. Highly intelligent with excellent camouflage abilities."},
    {"name": "Kangaroo", "diet": "Herbivore - grasses, herbs, and shrubs. Well-adapted to arid environments with efficient water conservation."},
    {"name": "Tiger", "diet": "Carnivore - large prey including deer, wild boar, and buffalo. Solitary hunters unlike lions."}
]


def fetch_animal(timeout: float = 6.0):
    """Fetch animal data from API, with fallback to local data."""
    # Try API first
    if requests is not None:
        try:
            r = requests.get(API_URL, timeout=timeout)
            if r.status_code == 200:
                d = r.json()
                name = d.get("name") or "?"
                diet = d.get("diet") or "?"
                return name, diet
        except Exception:
            # API failed, fall through to fallback
            pass
    
    # Use fallback data
    animal = random.choice(FALLBACK_ANIMALS)
    return animal["name"], animal["diet"]


def run(stop_event, api):
    api.log_info("name_that_animal starting")
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 1800))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Animal"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        try:
            name, diet = fetch_animal(timeout=timeout)
            api.screen.display_text(f"{title}\n\n{name}\n\n" + shorten(diet, width=200, placeholder="…"), align="left")
        except Exception as e:
            api.log_error(f"Failed to fetch animal data: {e}")
            api.screen.display_text(f"{title}\n\n(error/no data)", align="left")

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            last_fetch = time.time()
            show()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show()
        last_fetch = time.time()
        while not stop_event.is_set():
            if time.time() - last_fetch >= refresh_seconds:
                last_fetch = time.time()
                show()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
    
    api.log_info("name_that_animal stopping")
