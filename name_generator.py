# name_generator.py
import random

adjectives = [
    "creeping", "cursed", "dark", "electric", "forgotten",
    "gloomy", "haunted", "lonely", "mad", "nocturnal",
    "phantom", "restless", "shadow", "twisted", "undead",
    "weeping", "silent", "ancient", "crimson", "vengeful"
]
nouns = [
    "victor", "clara", "dalek", "igorr", "tardis",
    "frankenstein", "monster", "cyberman", "angel",
    "silurian", "zygon", "sontaran", "river", "melody",
    "smith", "adric", "romana", "k9", "omega", "rasta"
]

def generate_name():
    return f"{random.choice(adjectives)}-{random.choice(nouns)}"