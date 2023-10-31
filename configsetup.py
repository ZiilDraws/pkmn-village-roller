import configparser
from constants import USERSETTINGS_VERSION

def update_config(link):
    try:
        oldconfig = configparser.ConfigParser(allow_no_value="True")
        oldconfig.read(link, encoding="utf-16")
    except:
        oldconfig = configparser.ConfigParser(allow_no_value="True")
        oldconfig.read(link, encoding="utf-8")

    config = configparser.ConfigParser(allow_no_value="True")

    config.add_section("Settings")
    config.set("Settings", "# True bypasses \"add to inventory\" prompt and adds item immediately to sheet.")
    config["Settings"]["auto_add_to_inventory"] = "False" if not oldconfig.has_option("Settings", "auto_add_to_inventory") else oldconfig.get("Settings", "auto_add_to_inventory")
    config.set("Settings", "# ")
    config.set("Settings", "# True bypasses \"add to inventory\" prompt and does not add item to sheet.")
    config["Settings"]["auto_deny_updating_sheet"] = "False" if not oldconfig.has_option("Settings", "auto_deny_updating_sheet") else oldconfig.get("Settings", "auto_deny_updating_sheet")
    config.set("Settings", "#  ")
    config.set("Settings", "# Copy roll messages to clipboard after roll")
    config["Settings"]["roll_messages_to_clipboard"] = "False" if not oldconfig.has_option("Settings", "roll_messages_to_clipboard") else oldconfig.get("Settings", "roll_messages_to_clipboard")
    config.set("Settings", "#   ")
    config.set("Settings", "# Save changes to a log file in the logs folder")
    config["Settings"]["save_changes_done_to_file"] = "True" if not oldconfig.has_option("Settings", "save_changes_done_to_file") else oldconfig.get("Settings", "save_changes_done_to_file")
    config.set("Settings", "#    ")
    config.set("Settings", "# Write rolls without item outcome into the log files")
    config["Settings"]["write_misses_to_file"] = "True" if not oldconfig.has_option("Settings", "write_misses_to_file") else oldconfig.get("Settings", "write_misses_to_file")
    config.set("Settings", "#     ")
    config.set("Settings", "# Change the printed name of the primary currency (Pokedollars)")
    config["Settings"]["currency_name"] = "₱" if not oldconfig.has_option("Settings", "currency_name") else oldconfig.get("Settings", "currency_name")

    config.add_section("Version")
    config.set("Version", "# Do not change this value.")
    config["Version"]["version"] = USERSETTINGS_VERSION

    print("Updated UserSettings")
    # Save the updated config file
    with open(link, 'w', encoding="utf-16") as configfile:
        config.write(configfile)