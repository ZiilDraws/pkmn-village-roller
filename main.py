import os.path
import sys
import random
import time

import gspread
import constants
import re
import configparser
import clipboard
from oauth2client.service_account import ServiceAccountCredentials
from pyphonetics import Soundex

if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

# Authenticate using credentials
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

try:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'persistent/credentials.json', scope)
except:
    print("An error with the credentials.json file in the 'persistent' folder! Is it missing? Have you followed the tutorial "
          "at https://github.com/ZiilDraws/pkmn-village-roller/blob/main/README.md?")
    input("")
    sys.exit(0)
gc = gspread.authorize(credentials)

# Open the spreadsheet by URL
spreadsheet = gc.open_by_url(constants.MASTERSHEET_URL)

# Select the worksheet
worksheet = spreadsheet.get_worksheet_by_id(constants.MASTERSHEET_WORKSHEET_ID)

# Get all values from the worksheet
mastersheet_data = worksheet.get_all_values()
if len(mastersheet_data) <= 0:
    print("Failed to load mastersheet data, please restart the application")
    sys.exit(0)


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

    def roll(self, table_index=1):
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
    if roll_messages_to_clipboard:
        clipboard.copy(edited_line)
    return edited_line


def read_random_line(file_path):
    with open(os.path.join(Current_Path, file_path), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        random_line = random.choice(lines).strip()
        return random_line


def loot_roll(table, tier=1):
    result = table.roll(tier)
    amount, item = split_string_with_number(result)
    sheet_num, pos = find_position_of_item(item)
    return amount, item, sheet_num, pos


def change_value_of_cell(dx_value, worksheet_id, position, url, item):
    member_sheet = gc.open_by_url(url)
    member_worksheet = member_sheet.get_worksheet(worksheet_id)
    old_value = member_worksheet.acell(position).value
    prefix = standard_prefix(item)
    if prefix == "x":
        item_cell = member_worksheet.acell(decrement_letter(position)).value
        if item_cell.strip().lower() != item.strip().lower():
            print(f"The cell to the left of this cell is {item_cell} instead of {item}.")
            cont = input("Are you sure you wish to continue? (y/n): ")
            if cont.lower() != "y":
                return "Error in position label", old_value, None
    value = False
    if old_value is not None:
        value = re.match(r'^(x?)(\d+(,\d+)*)$', old_value)
    if value:
        new_value = int(value.group(2).replace(",", "")) + dx_value
        if new_value < 0:
            print(f"This member does not have enough {item}, only {old_value}!")
            return "Not enough for edit", old_value, None
        cell_value = f"{prefix}{new_value}"
        member_worksheet.update_acell(position, cell_value)
        return cell_value, old_value, member_worksheet.title
    else:
        print(f"The value at position {position} is faulty. Check and add manually!!!")
        return "Faulty position", old_value, None


def check_to_have_item(dx_value, worksheet_id, position, url):
    member_sheet = gc.open_by_url(url)
    member_worksheet = member_sheet.get_worksheet(worksheet_id)
    old_value = member_worksheet.acell(position).value
    value = False
    if old_value is not None:
        value = re.match(r'^(x?)(\d+(,\d+)*)$', old_value)
    if value:
        new_value = int(value.group(2).replace(",", "")) - dx_value
        if new_value < 0:
            return False
        return True
    else:
        print(f"The value at position {position} is faulty. Please check.")
        return False


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
        return None


def decrement_letter(input_str):
    letter = input_str[0]
    number = input_str[1:]

    # Decrement the letter by one step
    if letter.isalpha():
        letter = chr(ord(letter.upper()) - 1)

        # Wrap around from 'A' to 'Z'
        if letter < 'A':
            letter = 'Z'

    # Return the modified input
    return letter + number


def get_txt_files(folder):
    txt_files = []
    for file in os.listdir(os.path.join(Current_Path, folder)):
        if file.endswith(".txt"):
            txt_files.append(file)
    return txt_files


def get_item_roll_file(txt_files):
    while True:
        print("Available files:")
        for i, file in enumerate(txt_files):
            print(f"{i + 1}. {file[:-4]}")
        selection = input("Enter the number of the file you want to select (0 to exit): ")

        if selection.isdigit():
            selection = int(selection)
            if 0 < selection <= len(txt_files):
                return txt_files[selection - 1]
            elif selection == 0:
                return None

        print("Invalid selection. Please try again.")


def get_input_member_row(message, shop=False):
    sel_id = 0
    while sel_id != "end":
        sel_id = input(message).lower()
        if sel_id == "end":
            return sel_id
        elif shop and sel_id == "shop":
            return "shop"
        elif sel_id == "":
            continue
        member_row = get_member_row(sel_id)
        if member_row is not None:
            return member_row
        else:
            print(f"Could not find ID {sel_id}")


def get_item_from_input(message, allow_none=False):
    item = 0
    while item != "end":
        item = input(message).lower().strip()
        if item == "end":
            return item, None, None
        elif allow_none and item == "":
            return None, None, None
        sheet_num, pos = find_position_of_item(item)
        if sheet_num is None:
            print(f"Cannot find {item}!")
        else:
            return item, sheet_num, pos


def get_amount_from_input(message, allow_zero=False):
    amount = ""
    while amount != "end":
        amount = process_positive_negative_int(input(message))
        if amount == "end":
            return amount
        if (allow_zero and amount is None) or (not allow_zero and (amount == 0 or amount is None)):
            print(f"Input is {'' if allow_zero else '0 or '}not an integer. You can type \"end\" to quit.")
        else:
            return amount


def standard_activity_roll(tool_id):
    loot_table = WeightedTable(f"rolls/tools/{constants.TOOL_FILE_NAMES[tool_id]}")
    extra_roller = WeightedTable(constants.EXTRA_FILE_NAME)
    tool_column = find_tool_column(tool_id)
    member_row = 0
    while member_row != "end":
        print("")
        member_row = get_input_member_row("Input Discord ID to roll (\"end\" to quit): ")
        if member_row == "end":
            return
        tool_tier = constants.TOOLS_TIER.index(member_row[tool_column].lower())
        if tool_tier == 0:
            print(f"{member_row[nick_column]} has no {constants.TOOL_IDS[tool_id]}!")
        else:
            amount, item, sheet_num, pos = loot_roll(loot_table, tool_tier)
            if sheet_num is None:
                print(f"{member_row[nick_column]} got {amount} {item} with {member_row[tool_column]}"
                      f" {constants.TOOL_IDS[tool_id]}!")
                print(f"m Cannot find {item}!!! MAKE SURE TO ADD MANUALLY !!!!!!!!!!!!!")
                continue
            elif sheet_num == "n":
                print(f"{member_row[nick_column]} got no item with their {member_row[tool_column]} "
                      f"{constants.TOOL_IDS[tool_id]}.")
                print(f"Oof, no item :(")
                if roll_messages_to_clipboard:
                    clipboard.copy("Oof, no item :(")
                if write_misses_to_file:
                    log_addition(member_row)
                continue
            elif sheet_num == "r":
                amount, item, sheet_num, pos = loot_roll(loot_table, 4)
            elif sheet_num == "er":
                amount, item, sheet_num, pos = loot_roll(extra_roller, int(pos))
            print(f"{member_row[nick_column]} got {amount} {item} with {member_row[tool_column]}"
                  f" {constants.TOOL_IDS[tool_id]}!")
            if check_if_update_sheet():
                new_val, old_val, sheet_name = change_value_of_cell(int(amount), int(sheet_num), pos,
                                                                    member_row[sheet_link_column],
                                                                    item
                                                                    )
                log_addition(member_row, item, amount, old_val, new_val, pos, sheet_name)
            else:
                log_addition(member_row, item, amount, "Autoadd Disabled")
            print("")
            print(generate_tool_loot_message(member_row[nick_column], amount, item, tool_id))


def dice_gamble_roll():
    rollercfg = configparser.ConfigParser()
    rollercfg.read('rolls.ini')
    guessing_game = rollercfg.getboolean("GameCorner", "guessing_game")
    dice_max = rollercfg.getint("GameCorner", "standard_dice_max")
    enable_modifier = rollercfg.getboolean("GameCorner", "enable_modifier")
    gamble_value_ranges = process_list_of_ranges(rollercfg.get("GameCorner", "dice_value_ranges"))
    gamble_reward_ranges = process_list_of_ranges(rollercfg.get("GameCorner", "dice_reward_ranges"))
    sheet_num, pos = find_position_of_item("gct")
    member_row = 0
    while member_row != "end":
        print("")
        member_row = get_input_member_row("Input Discord ID of gamer (\"end\" to quit): ")
        if member_row == "end":
            return
        if guessing_game:
            guess = get_amount_from_input("Input number guess: ", True)
            if guess == "end":
                continue
        elif enable_modifier:
            modifier = get_amount_from_input("Input modifier value: ", True)
            if modifier == "end":
                continue
        else:
            modifier = 0
        dice_roll = random.randint(1, dice_max)
        dice_roll_mod = max(1, dice_roll + modifier) if not guessing_game else abs(dice_roll - guess)
        reward = "ERROR"
        for index, value_range in enumerate(gamble_value_ranges):
            if value_range[0] <= dice_roll_mod <= value_range[1]:
                reward = random.randint(gamble_reward_ranges[index][0], gamble_reward_ranges[index][1])
        if not guessing_game:
            print(f"{member_row[nick_column]} won {reward} GCT with a roll of {dice_roll_mod} ({dice_roll}+{modifier})")
        else:
            print(f"{member_row[nick_column]} won {reward} GCT with a distance of {dice_roll_mod} ({dice_roll})")

        if check_if_update_sheet(True) and reward != "ERROR":
            new_val, old_val, sheet_name = change_value_of_cell(reward, int(sheet_num), pos,
                                                                member_row[sheet_link_column], "GCT")
            log_addition(member_row, "gct", reward, old_val, new_val, pos, sheet_name)
        else:
            log_addition(member_row, "gct", reward, "Autoadd Disabled")
            print(member_row[sheet_link_column])

        print(generate_loot_message(member_row[nick_column], reward, "GCT", constants.GAMBLE_PROMPT_FILE_NAME))


def item_loot_roll():
    extra_roller = WeightedTable(constants.EXTRA_FILE_NAME)
    member_row = "end"
    txt_files = get_txt_files(constants.ITEM_LOOT_ROLL_FOLDER)
    selected_file = get_item_roll_file(txt_files)
    if selected_file is not None:
        member_row = 0
        loot_table = WeightedTable(os.path.join(constants.ITEM_LOOT_ROLL_FOLDER, selected_file))
    while member_row != "end":
        print("")
        member_row = get_input_member_row("Input Discord ID to roll (\"end\" to quit): ")
        if member_row == "end":
            return
        amount, item, sheet_num, pos = loot_roll(loot_table)
        if sheet_num is None:
            print(f"m Cannot find {item}!!! MAKE SURE TO ADD MANUALLY !!!!!!!!!!!!!")
            continue
        elif sheet_num == "er":
            amount, item, sheet_num, pos = loot_roll(extra_roller, int(pos))
        print(f"{member_row[nick_column]} got {get_article(item) if amount == 1 else amount} {item}!")
        if check_if_update_sheet():
            new_val, old_val, sheet_name = change_value_of_cell(int(amount), int(sheet_num), pos,
                                                                member_row[sheet_link_column],
                                                                item
                                                                )
            log_addition(member_row, item, amount, old_val, new_val, pos, sheet_name)
        else:
            log_addition(member_row, item, amount, "Autoadd Disabled")
        print("")


def trade_shop_loop(only_shop=False):
    member_one_row = 0
    while member_one_row != "end":
        shop = only_shop
        print("")
        member_one_row = get_input_member_row(f"Input Discord ID for {'first' if not shop else ''} trader (\"end\" to "
                                              f"quit): ")
        if member_one_row == "end":
            return
        print(f"Trader {'1' if not shop else ''} is {member_one_row[nick_column]}.")

        if not shop:
            member_two_row = get_input_member_row(f"Input Discord ID for second trader (\"shop\" to shop, \"end\" to "
                                                  f"quit): ", True)
            if member_two_row == "end":
                return
            elif member_two_row == "shop":
                shop = True

        item1, sheet_num1, pos1 = get_item_from_input(f"Input item name for {member_one_row[nick_column]} to "
                                                      f"{f'send to {member_two_row[nick_column]}' if not shop else 'spend'}" 
                                                      f" (Spelling needs to be the same as used in the sheet): ")
        if item1 == "end":
            continue
        amount1 = get_amount_from_input(f"Input amount of {item1} for {member_one_row[nick_column]} to give "
                                        f"(e.g. 5, 32 or -300): ")
        if amount1 == "end":
            continue

        item2, sheet_num2, pos2 = get_item_from_input(f"Input item name for "
                                                      f"{member_two_row[nick_column] if not shop else 'shop'} to send ("
                                                      f"{'Press enter directly for Nothing, ' if not shop else ''}"
                                                      f"Spelling needs to be the same as used in the sheet): ", not shop
                                                      )
        if item2 == "end":
            continue
        if shop or item2 is not None:
            amount2 = get_amount_from_input(f"Input amount of {item2} for "
                                            f"{member_two_row[nick_column] if not shop else 'shop'} to give "
                                            f"(e.g. 5, 32 or -300): ")
            if amount2 == "end":
                continue
            print(f"{member_one_row[nick_column]} gives {member_two_row[nick_column] if not shop else 'shop'} "
                  f"{amount1} {item1} for their {amount2} {item2}.")
        else:
            print(f"{member_one_row[nick_column]} gives {member_two_row[nick_column]} {amount1} {item1} ")

        updateable = check_to_have_item(int(amount1), int(sheet_num1), pos1, member_one_row[sheet_link_column], )
        if not updateable:
            print(f"{member_one_row[nick_column]} does not have {amount1} {item1}! Canceling...")
        if not shop and item2 is not None:
            updateable2 = check_to_have_item(int(amount2), int(sheet_num2), pos2, member_two_row[sheet_link_column], )
            if not updateable2:
                print(f"{member_two_row[nick_column]} does not have {amount2} {item2}! Canceling...")
        else:
            updateable2 = True

        if updateable and updateable2 and check_if_update_sheet():
            new_val, old_val, sheet_name = change_value_of_cell(-int(amount1), int(sheet_num1), pos1,
                                                                member_one_row[sheet_link_column],
                                                                item1
                                                                )
            log_addition(member_one_row, item1, -amount1, old_val, new_val, pos1, sheet_name)
            if not shop:
                new_val, old_val, sheet_name = change_value_of_cell(int(amount1), int(sheet_num1), pos1,
                                                                    member_two_row[sheet_link_column],
                                                                    item1
                                                                    )
                log_addition(member_two_row, item1, amount1, old_val, new_val, pos1, sheet_name)
            if item2 is not None:
                if not shop:
                    new_val, old_val, sheet_name = change_value_of_cell(-int(amount2), int(sheet_num2), pos2,
                                                                        member_two_row[sheet_link_column],
                                                                        item2
                                                                        )
                    log_addition(member_two_row, item2, -amount2, old_val, new_val, pos2, sheet_name)
                new_val, old_val, sheet_name = change_value_of_cell(int(amount2), int(sheet_num2), pos2,
                                                                    member_one_row[sheet_link_column],
                                                                    item2
                                                                    )
                log_addition(member_one_row, item2, amount2, old_val, new_val, pos2, sheet_name)
            print("Trade complete!")


def quest_reward():
    extra_roller = WeightedTable(constants.EXTRA_FILE_NAME)
    quest_normal = WeightedTable(os.path.join(constants.QUEST_ROLL_FOLDER, constants.QUEST_FILE_NAMES[0]))
    quest_oos = WeightedTable(os.path.join(constants.QUEST_ROLL_FOLDER, constants.QUEST_FILE_NAMES[1]))
    member_row = 0
    while member_row != "end":
        print("")
        member_row = get_input_member_row("Input Discord ID to give quest rewards to (\"end\" to quit): ")
        if member_row == "end":
            return
        third_quest = input(f"Is this the third quest {member_row[nick_column]} has done this month? (y/n)")
        while third_quest != "y" and third_quest != "n":
            print("Enter y or n. ")
            third_quest = input(f"Is this the third quest {member_row[nick_column]} has done this month? (y/n)")
        amount, item, sheet_num, pos = loot_roll(quest_normal)
        if sheet_num is None:
            print(f"m Cannot find {item}!!! MAKE SURE TO ADD MANUALLY !!!!!!!!!!!!!")
            continue
        elif sheet_num == "er":
            amount, item, sheet_num, pos = loot_roll(extra_roller, int(pos))
        print(f"{member_row[nick_column]} got {amount} {item}!")
        if third_quest == "y":
            amount2, item2, sheet_num2, pos2 = loot_roll(quest_oos)
            if sheet_num2 is None:
                print(f"Cannot find {item2}!!! MAKE SURE TO ADD MANUALLY !!!!!!!!!!!!!")
                continue
            elif sheet_num2 == "er":
                amount2, item2, sheet_num2, pos2 = loot_roll(extra_roller, int(pos2))
            print(f"{member_row[nick_column]} got {amount2} {item2}!")
        if check_if_update_sheet():
            new_val, old_val, sheet_name = change_value_of_cell(int(amount), int(sheet_num), pos,
                                                                member_row[sheet_link_column],
                                                                item
                                                                )
            log_addition(member_row, item, amount, old_val, new_val, pos, sheet_name)
            if third_quest == "y":
                new_val, old_val, sheet_name = change_value_of_cell(int(amount2), int(sheet_num2), pos2,
                                                                    member_row[sheet_link_column],
                                                                    item2
                                                                    )
                log_addition(member_row, item2, amount2, old_val, new_val, pos2, sheet_name)
            sheet_num, pos = find_position_of_item("money")
            new_val, old_val, sheet_name = change_value_of_cell(constants.QUEST_CURRENCY_AMOUNT, int(sheet_num),
                                                                pos,
                                                                member_row[sheet_link_column],
                                                                "money"
                                                                )
            log_addition(member_row, "money", constants.QUEST_CURRENCY_AMOUNT, old_val, new_val, pos, sheet_name)
        else:
            log_addition(member_row, item, amount, "Autoadd Disabled")

        print(f"You got **{constants.QUEST_CURRENCY_AMOUNT}** :pokedollar: and "
              f"**{get_article(item) if amount == 1 else amount} {item}**!")
        if third_quest == "y":
            print(f"You also get **{get_article(item2) if amount2 == 1 else amount2} {item2}**!")
        print("")


def add_item_loop():
    member_row = 0
    while member_row != "end":
        print("")
        member_row = get_input_member_row("Input Discord ID to add/remove item (\"end\" to quit): ")
        if member_row == "end":
            return
        print(f"Selected user is {member_row[nick_column]}.")
        item, sheet_num, pos = get_item_from_input("Input item name (Spelling needs to be the same as used in the "
                                                   "sheet): ")
        if item == "end":
            continue
        amount = get_amount_from_input(f"Input amount of {item} (e.g. 5, 32 or -300): ")
        if amount == "end":
            continue
        if amount is None or amount == 0:
            print(f"Input is 0 or not an integer.")
            print(member_row[sheet_link_column])
            continue
        if check_if_update_sheet(True):
            new_val, old_val, sheet_name = change_value_of_cell(int(amount), int(sheet_num), pos,
                                                                member_row[sheet_link_column],
                                                                item
                                                                )
            log_addition(member_row, item, amount, old_val, new_val, pos, sheet_name)
            print(f"Added {get_article(item) if amount == 1 else amount} {item} to {member_row[nick_column]}'s "
                  f"inventory!")


def link_loop():
    member_row = 0
    while member_row != "end":
        print("")
        member_row = get_input_member_row("Input Discord ID to get URL (\"end\" to quit): ")
        if member_row == "end":
            return
        print(f"{member_row[nick_column]}'s URL is {member_row[sheet_link_column]}")


def fix_misspelling_in_sheet():
    print("This is a dangerous function, only use if neccessary")
    worksheet_of_cell = input("What is the name of the worksheet? (case sensitive)")
    cell = input("Select cell to fix (e.g. A5)")
    current_word = input("What does the cell currently say? (case sensitive) (enter UPDATE_ANYWAYS to change "
                         "regardless of what the cell says)")
    new_word = input("What to change the word to?")
    for line in mastersheet_data[1:]:
        ms = gc.open_by_url(line[sheet_link_column])
        done = False
        wait = 3
        while not done:
            try:
                mws = ms.worksheet(worksheet_of_cell)
                if current_word != "UPDATE_ANYWAYS":
                    item_cell = mws.acell(cell).value
                if current_word == "UPDATE_ANYWAYS" or item_cell == current_word:
                    mws.update_acell(cell, new_word)
                    print(f"Updated cell for {line[nick_column]}")
                else:
                    print(f"Cell is {item_cell}, didn't update for {line[nick_column]}")
                done = True
                wait = 3
            except gspread.exceptions.APIError:
                print("Waiting for new quota...")
                time.sleep(wait)
                if wait < 10:
                    wait += 1


    print("Done!")


def main():
    end = False
    while not end:
        option = input("""What do you wish to do? 
            -- type one of the following options
            -- "tool" for standard tool activity rolls
            -- "gamble" for game corner functionality
            -- "roll" for different loot rolls
            -- "trade" for player trades/shop trades
            -- "shop" for just shop trades
            -- "quest" to give quest rewards
            -- "modify" to add/remove items in specific inventories
            -- "link" to get sheet URL 
            -- "end" to end program
            """).lower()
        if option == "tool":
            tool_id = get_tool_id()
            standard_activity_roll(tool_id)
        elif option == "gamble":
            dice_gamble_roll()
        elif option == "roll":
            item_loot_roll()
        elif option == "quest":
            quest_reward()
        elif option == "trade":
            trade_shop_loop()
        elif option == "shop":
            trade_shop_loop(True)
        elif option == "modify" or option == "add" or option == "remove":
            add_item_loop()
        elif option == "link":
            link_loop()
        elif option == "end":
            end = True
        elif option == "fix_dangerous":
            fix_misspelling_in_sheet()
        else:
            print(f"{option} is not a valid option")
    print("Good Bye!")


config = configparser.ConfigParser()
config.read('persistent/usersettings.ini')

auto_add_to_inventory = config.getboolean('Settings', 'auto_add_to_inventory')
auto_deny_updating_sheet = config.getboolean('Settings', 'auto_deny_updating_sheet')
save_changes_done_to_file = config.getboolean('Settings', 'save_changes_done_to_file')
write_misses_to_file = config.getboolean('Settings', 'write_misses_to_file')
roll_messages_to_clipboard = config.getboolean('Settings', 'roll_messages_to_clipboard')
if roll_messages_to_clipboard:
    oldclip = clipboard.paste()
    testint = f"{random.randint(0, 1000)}"
    clipboard.copy(testint)
    if testint != clipboard.paste():
        print("Clipboard copying does not work on this computer")
    else:
        clipboard.copy(oldclip)

os.makedirs("logs", exist_ok=True)
log_file = os.path.join("logs", constants.LOG_FILE_NAME)

item_positions = gen_item_positions()

id_column = find_column(constants.MASTERSHEET_HEADERS[2])
sheet_link_column = find_column(constants.MASTERSHEET_HEADERS[3])
nick_column = find_column(constants.MASTERSHEET_HEADERS[0])
changes_done = []

main()
