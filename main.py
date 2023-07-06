import os.path
import sys
import random
import gspread
import constants
import re
import configparser
from oauth2client.service_account import ServiceAccountCredentials
from pyphonetics import Soundex

if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

# Authenticate using credentials
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'env/credentials.json', scope)
gc = gspread.authorize(credentials)

# Open the spreadsheet by URL
spreadsheet = gc.open_by_url(constants.MASTERSHEET_URL)

# Select the worksheet
worksheet = spreadsheet.get_worksheet_by_id(constants.MASTERSHEET_WORKSHEET_ID)

# Get all values from the worksheet
mastersheet_data = worksheet.get_all_values()


class WeightedTable:
    def __init__(self, filename):
        self.tables = []
        self.load_tables(filename)

    def load_tables(self, filename):
        with open(os.path.join(Current_Path, filename), 'r') as file:
            current_table = []

            for line in file:
                line = line.strip()

                if not line:  # Blank row indicates the end of a table
                    if current_table:  # Skip if no items in the table
                        self.tables.append(current_table)
                        current_table = []
                else:
                    if '^' in line:
                        item, weight = line.split('^')
                        current_table.append((item.strip(), float(weight)))
                    else:
                        current_table.append((line, 1.0))

            if current_table:  # Add the last table if not empty
                self.tables.append(current_table)

    def roll(self, table_index):
        if table_index < 1 or table_index > len(self.tables):
            raise IndexError("Invalid table index")

        table = self.tables[table_index - 1]
        items, weights = zip(*table)

        return random.choices(items, weights)[0]


def get_article(word):
    vowels = ['a', 'e', 'i', 'o', 'u']
    soundex = Soundex()
    phonetic_code = soundex.phonetics(word)

    if phonetic_code[0].lower() in vowels:
        return 'an'
    else:
        return 'a'


def replace_placeholders(template, replacements):
    for placeholder, value in replacements.items():
        template = template.replace('{' + placeholder + '}', str(value))
    return template


def gen_item_positions():
    with open(os.path.join(Current_Path, constants.POSITIONS_FILE), 'r', encoding='utf-8') as f:
        lines = f.readlines()

    positions = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(',')
        name = parts[0].lower()
        w_sheet = parts[1].strip()
        pos = parts[2].strip()
        positions.append([name, w_sheet, pos])

    return positions


# Get the row of the member as an array
def get_member_row(id):
    # Find the row with the matching ID
    for row in mastersheet_data[1:]:  # Exclude header row
        if row[id_column] == id:
            return row

    return None  # ID not found


# Find a column from the header name
def find_column(search_string):
    pos = -1
    for i in range(0, len(mastersheet_data[0]) - 1):
        if mastersheet_data[0][i] == search_string:
            pos = i
            break
    if pos == -1:
        sys.exit(f"Could not find {search_string} column.")

    return pos


# Find a tool header from the tool header id
def find_tool_column(header_id):
    return find_column(constants.TOOL_HEADERS[header_id])


def standard_prefix(item):
    if item.lower() in constants.VALUES_WITHOUT_X_PREFIX:
        return ""
    return "x"


def check_if_update_sheet(deny_override=False):
    if not auto_deny_updating_sheet or deny_override:
        if auto_add_to_inventory or input("Do you want to update sheet? (y/n): ").strip() == "y":
            return True
    return False


def generate_tool_loot_message(name, amount, item, tool_id):
    return generate_loot_message(name, amount, item, constants.TOOL_FILE_NAMES[tool_id])


def generate_loot_message(name, amount, item, loot_file_name):
    if amount == 1:
        amount = get_article(item)
    line = read_random_line(os.path.join("prompts", loot_file_name))
    replacements = {"name": name, "amount": amount, "item": item}
    edited_line = replace_placeholders(line, replacements)
    return edited_line


def read_random_line(file_path):
    with open(os.path.join(Current_Path, file_path), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        random_line = random.choice(lines).strip()
        return random_line


def loot_roll(table, tier):
    result = table.roll(tier)
    amount, item = split_string_with_number(result)
    sheet_num, pos = find_position_of_item(item)
    return amount, item, sheet_num, pos


def change_value_of_cell(dx_value, worksheet_id, position, url, prefix="x"):
    member_sheet = gc.open_by_url(url)
    member_worksheet = member_sheet.get_worksheet(worksheet_id)
    old_value = member_worksheet.acell(position).value
    value = False
    if old_value is not None:
        value = re.match(r'^(x?)(\d+(,\d+)*)$', old_value)
    if value:
        new_value = int(value.group(2).replace(",", "")) + dx_value
        cell_value = f"{prefix}{new_value}"
        member_worksheet.update_acell(position, cell_value)
        return cell_value, old_value, member_worksheet.title
    else:
        print(f"The value at position {position} is faulty. Check and add manually!!!")
        return "Faulty position", old_value, None


def log_addition(member_row, item="None", amount=0, old_val=0, new_val=0, position="XX", sheet="X"):
    line = [member_row[id_column], member_row[nick_column], item, amount,
            old_val, new_val, position, sheet, member_row[sheet_link_column]]
    changes_done.append(line)
    if save_changes_done_to_file:
        write_to_log(line)


def write_to_log(line):
    try:
        # Check if the file exists
        with open(os.path.join(Current_Path, log_file), 'a') as file:
            # Append the new line to the log file
            file.write(line.__str__() + '\n')
    except FileNotFoundError:
        # Create the file if it doesn't exist
        with open(os.path.join(Current_Path, log_file), 'w') as file:
            pass
        write_to_log(line)


def find_position_of_item(item_name):
    for item in item_positions:
        if item[0] == item_name.lower():
            return item[1], item[2]
    return None, None


def get_tool_id():
    tool_message = "Select tool ("
    for tool in constants.TOOL_WORKNAMES:
        tool_message += (tool + " / ")
    tool_message = tool_message[0:len(tool_message) - 3]
    tool_message += "): "
    while True:
        selected_tool = input(tool_message)
        tool_id = constants.TOOL_WORKNAMES.index(selected_tool)
        if tool_id != -1:
            return tool_id
        else:
            print(f"{selected_tool} is not a valid option.")


def split_string_with_number(string):
    match = re.match(r'^(x?)(\d+)\s+(.*)$', string)
    if match:
        number = match.group(2)
        remainder = match.group(3)
        return number, remainder
    else:
        return 1, string


def process_list_of_ranges(input_string):
    ranges = input_string.split(",")
    result = []

    for range_str in ranges:
        range_values = range_str.split("-")
        first_num = int(range_values[0].strip())
        second_num = int(range_values[1].strip()) if len(range_values) > 1 else first_num
        result.append((first_num, second_num))

    return result


def process_positive_negative_int(in_data):
    if in_data.strip() == "":
        return 0
    match = re.match(r'^(-?)(\d+)$', in_data.strip())
    if match:
        return int(in_data)
    else:
        return False


# Perform a standard activity roll
def standard_activity_roll(tool_id):
    loot_table = WeightedTable(f"rolls/{constants.TOOL_FILE_NAMES[tool_id]}")
    tool_column = find_tool_column(tool_id)
    selected_id = 0
    while selected_id != "end":
        print("")
        selected_id = input("Input Discord ID to roll (\"end\" to quit): ")
        if selected_id == "end":
            return
        member_row = get_member_row(selected_id)
        if member_row is not None:
            tool_tier = constants.TOOLS_TIER.index(member_row[tool_column].lower())
            if tool_tier == 0:
                print(f"{member_row[nick_column]} has no {constants.TOOL_IDS[tool_id]}!")
            else:
                amount, item, sheet_num, pos = loot_roll(loot_table, tool_tier)
                if sheet_num is None:
                    print(f"m Cannot find {item}!!! MAKE SURE TO ADD MANUALLY !!!!!!!!!!!!!")
                    continue
                elif sheet_num == "n":
                    print(f"Oof, no item :(")
                    if write_misses_to_file:
                        log_addition(member_row)
                    continue
                elif sheet_num == "r":
                    amount, item, sheet_num, pos = loot_roll(loot_table, 4)
                elif sheet_num == "er":
                    amount, item, sheet_num, pos = loot_roll(extra_roller, int(pos))
                print(f"{member_row[nick_column]} got {amount} {item} with {member_row[tool_column]} \
{constants.TOOL_IDS[tool_id]}!")
                if check_if_update_sheet():
                    new_val, old_val, sheet_name = change_value_of_cell(int(amount), int(sheet_num), pos,
                                                                        member_row[sheet_link_column],
                                                                        standard_prefix(item)
                                                                        )
                    log_addition(member_row, item, amount, old_val, new_val, pos, sheet_name)
                else:
                    log_addition(member_row, item, amount, "Autoadd Disabled")
                print("")
                print(generate_tool_loot_message(member_row[nick_column], amount, item, tool_id))
        else:
            print(f"Could not find ID {selected_id}")


def dice_gamble_roll():
    dice_max = config.getint("GameCorner", "standard_dice_max")
    gamble_value_ranges = process_list_of_ranges(config.get("GameCorner", "dice_value_ranges"))
    gamble_reward_ranges = process_list_of_ranges(config.get("GameCorner", "dice_reward_ranges"))
    sheet_num, pos = find_position_of_item("gct")
    selected_id = 0
    while selected_id != "end":
        print("")
        selected_id = input("Input Discord ID of gamer (\"end\" to quit): ")
        if selected_id == "end":
            return
        member_row = get_member_row(selected_id)
        if member_row is not None:
            modifier = process_positive_negative_int(input("Input modifier value: "))
            if modifier != 0 and not modifier:
                print(f"Input is not a digit")
                continue
            dice_roll = random.randint(1, dice_max)
            dice_roll_mod = max(1, dice_roll + modifier)
            reward = "ERROR"
            for index, value_range in enumerate(gamble_value_ranges):
                if value_range[0] <= dice_roll_mod <= value_range[1]:
                    reward = random.randint(gamble_reward_ranges[index][0], gamble_reward_ranges[index][1])
            print(f"{member_row[nick_column]} won {reward} GCT with a roll of {dice_roll_mod} ({dice_roll}+{modifier})")

            if check_if_update_sheet(True) and reward != "ERROR":
                new_val, old_val, sheet_name = change_value_of_cell(reward, int(sheet_num), pos,
                                                                    member_row[sheet_link_column], "")
                log_addition(member_row, "gct", reward, old_val, new_val, pos, sheet_name)
            else:
                log_addition(member_row, "gct", reward, "Autoadd Disabled")

            print(generate_loot_message(member_row[nick_column], reward, "GCT", constants.GAMBLE_PROMPT_FILE_NAME))

        else:
            print(f"Could not find ID {selected_id}")


def add_item_loop():
    selected_id = 0
    while selected_id != "end":
        print("")
        selected_id = input("Input Discord ID to add item to (\"end\" to quit): ")
        if selected_id == "end":
            return
        member_row = get_member_row(selected_id)
        if member_row is not None:
            item = input("Input item name (Spelling needs to be the same as used in the sheet): ")
            sheet_num, pos = find_position_of_item(item)
            if sheet_num is None:
                print(f"Cannot find {item}!")
                print(member_row[sheet_link_column])
                continue
            amount = process_positive_negative_int(input(f"Input amount of {item}: "))
            if amount != 0 and not amount:
                print(f"Input is not an integer.")
                print(member_row[sheet_link_column])
                continue
            if check_if_update_sheet(True):
                new_val, old_val, sheet_name = change_value_of_cell(int(amount), int(sheet_num), pos,
                                                                    member_row[sheet_link_column],
                                                                    standard_prefix(item)
                                                                    )
                log_addition(member_row, item, amount, old_val, new_val, pos, sheet_name)
        else:
            print(f"Could not find ID {selected_id}")


def link_loop():
    selected_id = 0
    while selected_id != "end":
        print("")
        selected_id = input("Input Discord ID to get URL (\"end\" to quit): ")
        if selected_id == "end":
            return
        member_row = get_member_row(selected_id)
        if member_row is not None:
            print(f"{member_row[nick_column]}'s URL is {member_row[sheet_link_column]}")
        else:
            print(f"Could not find ID {selected_id}")


def main():
    end = False
    while not end:
        option = input("""What do you wish to do? 
            -- type one of the following options
            -- "tool" for standard tool activity rolls
            -- "gamble" for dice game corner roll with modifier
            -- "add" to add items to specific inventories
            -- "link" to get sheet URL 
            -- "end" to end program
            """).lower()
        if option == "tool":
            tool_id = get_tool_id()
            standard_activity_roll(tool_id)
        elif option == "gamble":
            dice_gamble_roll()
        elif option == "add":
            add_item_loop()
        elif option == "link":
            link_loop()
        elif option == "end":
            end = True
        else:
            print(f"{option} is not a valid option")
    print("Good Bye!")

config = configparser.ConfigParser()
config.read('config.ini')

auto_add_to_inventory = config.getboolean('Settings', 'auto_add_to_inventory')
auto_deny_updating_sheet = config.getboolean('Settings', 'auto_deny_updating_sheet')
save_changes_done_to_file = config.getboolean('Settings', 'save_changes_done_to_file')
write_misses_to_file = config.getboolean('Settings', 'write_misses_to_file')

os.makedirs("logs", exist_ok=True)
log_file = os.path.join("logs", constants.LOG_FILE_NAME)

item_positions = gen_item_positions()

id_column = find_column(constants.MASTERSHEET_HEADERS[2])
sheet_link_column = find_column(constants.MASTERSHEET_HEADERS[3])
nick_column = find_column(constants.MASTERSHEET_HEADERS[0])
extra_roller = WeightedTable(constants.EXTRA_FILE_NAME)
changes_done = []

main()
