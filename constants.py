from datetime import datetime

LOG_FILE_NAME = log_file_name = datetime.now().strftime("added_%H_%M_%d_%m_%Y.log")

MASTERSHEET_URL = "https://docs.google.com/spreadsheets/d/1-ptD2YT_NjTY2AAi5yqBbDkcy7-Om54JHNoujwQVl2g/edit#gid=1947086225"
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

POSITIONS_FILE = "rolls/positions.txt"

TOOL_IDS = ("bug net", "fishing rod", "shovel", "slingshot", "wailmer pail")
TOOLS_TIER = ("none", "basic", "silver", "golden")
TOOL_HEADERS = ("Bug Net Tier", "Fishing Rod Tier", "Shovel Tier", "Slingshot Tier", "Wailmer Pail")
TOOL_WORKNAMES = ("bug", "fish", "dig", "shoot")
TOOL_FILE_NAMES = ("bug.txt", "fish.txt", "dig.txt", "shoot.txt")

EXTRA_FILE_NAME = "rolls/extra_rolls.txt"

MISS_LABEL = "none"