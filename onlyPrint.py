import sys
import random
import gspread
import constants
from oauth2client.service_account import ServiceAccountCredentials

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
        with open(filename, 'r') as file:
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


# Deprecated Function
def get_sheet_and_tier(id, tool_column):
    # Find the row with the matching ID
    for row in mastersheet_data[1:]:  # Exclude header row
        if row[id_column] == id:
            # Open the linked sheet
            linked_sheet = gc.open_by_url(row[sheet_link_column])
            # Get the desired value from the linked sheet (e.g., cell A1)
            tool_value = constants.TOOLS_TIER.index(row[tool_column].lower())
            print(row)
            return linked_sheet, tool_value

    return None  # ID not found


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


# Perform a standard activity roll
def standard_activity_roll(tool_id):
    loot_table = WeightedTable(constants.TOOL_FILE_NAMES[tool_id])
    tool_column = find_tool_column(tool_id)
    selected_id = 0
    while selected_id != "end":
        selected_id = input("Input Discord ID to roll: ")
        if selected_id == "end":
            return
        member_row = get_member_row(selected_id)
        if member_row is not None:
            tool_tier = constants.TOOLS_TIER.index(member_row[tool_column].lower())
            if tool_tier == 0:
                print(f"{member_row[nick_column]} has no {constants.TOOL_IDS[tool_id]}!")
            else:
                result = loot_table.roll(tool_tier)
                print(f"{member_row[nick_column]} got {result} with {member_row[tool_column]} {constants.TOOL_IDS[tool_id]}! {member_row[sheet_link_column]}")


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


def perchance_roll(tool_id, tier):
    return "None"


def main():

    tool_id = get_tool_id()

    standard_activity_roll(tool_id)


id_column = find_column(constants.MASTERSHEET_HEADERS[2])
sheet_link_column = find_column(constants.MASTERSHEET_HEADERS[3])
nick_column = find_column(constants.MASTERSHEET_HEADERS[0])
extra_roller = WeightedTable(constants.EXTRA_FILE_NAME)

main()
