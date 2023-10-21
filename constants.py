from datetime import datetime

LOG_FILE_NAME = log_file_name = datetime.now().strftime("added_%H_%M_%d_%m_%Y.log")

# Test Mastersheet https://docs.google.com/spreadsheets/d/1-ptD2YT_NjTY2AAi5yqBbDkcy7-Om54JHNoujwQVl2g/edit#gid=1947086225
# Real Mastersheet https://docs.google.com/spreadsheets/d/14-y_966nX3GxakL5YF7YhTp-94hVFT5samJ6Pdxfxh8/edit#gid=1947086225
MASTERSHEET_URL = "https://docs.google.com/spreadsheets/d/14-y_966nX3GxakL5YF7YhTp-94hVFT5samJ6Pdxfxh8/edit#gid=1947086225"
MASTERSHEET_WORKSHEET_ID = 1947086225
MASTERSHEET_HEADERS = [
    "Nickname",
    "Discord Username",
    "Discord ID",
    "Sheet link",
    "Native Fruit",
    "Bug Net Tier",
    "Fishing Rod Tier",
    "Shovel Tier",
    "Slingshot Tier",
    "Wailmer Pail",
    "Pokemon Count",
    "Village Max",
    "Boosting Server?"
]

POSITIONS_FILE = "reqs/positions.txt"

TOOL_IDS = ("bug net", "fishing rod", "shovel", "slingshot", "wailmer pail")
TOOLS_TIER = ("none", "basic", "silver", "golden")
TOOL_HEADERS = ("Bug Net Tier", "Fishing Rod Tier", "Shovel Tier", "Slingshot Tier", "Wailmer Pail")
TOOL_WORKNAMES = ("bug", "fish", "dig", "shoot")
TOOL_FILE_NAMES = ("bug.txt", "fish.txt", "dig.txt", "shoot.txt")

EXTRA_FILE_NAME = "rolls/extra_rolls.txt"

MISS_LABEL = "none"

# Also used for knowing whether to check left cell or not
VALUES_WITHOUT_X_PREFIX = ["money", "pokedollar", "pokedollars", "poke", "gct", "gctoken", "gctokens", "$"]

GAMBLE_PROMPT_FILE_NAME = "gamble.txt"

ITEM_LOOT_ROLL_FOLDER = "rolls/items/"

SEED_TYPES = ["cosmos", "hyacinth", "lily", "mum", "pansy", "rose", "tulip", "windflower"]
SEED_COLOURS = ["red", "white", "yellow"]
SEED_WIND_COLOURS = ["red", "orange", "white"]

QUEST_ROLL_FOLDER = "rolls/quest/"
QUEST_FILE_NAMES = ["quest_normal.txt", "quest_oos.txt"]
QUEST_CURRENCY_AMOUNT = 100

RECIPE_NAMES = ["cook", "nature"]
RECIPE_FILES = ["recipes/cooking.txt", "recipes/nature_supply.txt"]

BATTLE_REWARD_FILE = "rolls/battle_rewards.txt"

POKEMON_TYPES = ["normal", "fire", "water", "electric", "grass", "ice",
                 "fighting", "poison", "ground", "flying", "psychic",
                 "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"]
TYPE_DAMAGE_ARRAY = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0, 1, 1, 0.5, 1],
                 [1, 0.5, 0.5, 1, 2, 2, 1, 1, 1, 1, 1, 2, 0.5, 1, 0.5, 1, 2, 1],
                 [1, 2, 0.5, 1, 0.5, 1, 1, 1, 2, 1, 1, 1, 2, 1, 0.5, 1, 1, 1],
                 [1, 1, 2, 0.5, 0.5, 1, 1, 1, 0, 2, 1, 1, 1, 1, 0.5, 1, 1, 1],
                 [1, 0.5, 2, 1, 0.5, 1, 1, 0.5, 2, 0.5, 1, 0.5, 2, 1, 0.5, 1, 0.5, 1],
                 [1, 0.5, 0.5, 1, 2, 0.5, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 0.5, 1],
                 [2, 1, 1, 1, 1, 2, 1, 0.5, 1, 0.5, 0.5, 0.5, 2, 0, 1, 2, 2, 0.5],
                 [1, 1, 1, 1, 2, 1, 1, 0.5, 0.5, 1, 1, 1, 0.5, 0.5, 1, 1, 0, 2],
                 [1, 2, 1, 2, 0.5, 1, 1, 2, 1, 0, 1, 0.5, 2, 1, 1, 1, 2, 1],
                 [1, 1, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 0.5, 1],
                 [1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 0.5, 1, 1, 1, 1, 0, 0.5, 1],
                 [1, 0.5, 1, 1, 2, 1, 0.5, 0.5, 1, 0.5, 2, 1, 1, 0.5, 1, 2, 0.5, 0.5],
                 [1, 2, 1, 1, 1, 2, 0.5, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 0.5, 1],
                 [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 1, 1],
                 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0.5, 0],
                 [1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 1, 0.5],
                 [1, 0.5, 0.5, 0.5, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0.5, 2],
                 [1, 0.5, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 1, 1, 1, 2, 2, 0.5, 1]]
