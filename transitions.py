# app/transitions.py
import random

def get_random_template():
    templates = {
        "classic": ["fade"] * 9,
        "slide": ["slideleft", "slideright", "slideup", "slidedown", "slideleft", "slideright", "slideup", "slidedown", "slideleft"],
        "mix": ["fade", "slideleft", "circlecrop", "rectcrop", "distance", "slideup", "slidedown", "smoothleft", "slideright"],
        "random": random.sample([
            "fade", "slideleft", "slideright", "circlecrop", "rectcrop",
            "distance", "slideup", "slidedown", "smoothleft"
        ], 9)
    }
    chosen = random.choice(list(templates.keys()))
    return templates[chosen], chosen
