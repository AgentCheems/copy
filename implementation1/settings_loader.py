# pyright: strict
import json, sys

def load_settings(path: str = "settings.json"):
    try:
        with open(path, "r") as f:
            settings = json.load(f)
    except Exception:
        print("Error in settings.json")
        sys.exit(1)

    num_required = {
        "soft_block_percent": (0, 100),
        "powerup_percent": (0, 100),
        "timer_seconds": (30, 600),
        "human_player_number": (1, 2), # only player 1 and 2 can be human
        "total_player_number": (2, 4),
        "rounds_to_win": (1, 4) #placeholder lang
        }

    str_required = {"bot_types": ("hostile", "careful", "greedy")}

    for key, (min, max) in num_required.items():
        if key not in settings:
            print(f"Error: No '{key}'.")
            sys.exit(1)

        int_value: int = settings[key]

        if type(int_value) is not int:
            print(f"Error: '{key}' must be an integer.")
            sys.exit(1)

        if not (min <= int_value <= max):
            print(f"Error: '{key}' must be between {min} and {max}, inclusive.")
            sys.exit(1)

    for key, lis in str_required.items():
        if key not in settings:
            print(f"Error: No '{key}'.")
            sys.exit(1)

        lis_value: list[str] = settings[key]

        if type(lis_value) is not list:
            print(f"Error: '{key}' must be a list.")
            sys.exit(1)

        if len(lis_value) != settings["total_player_number"] - settings["human_player_number"]:
            print(f"Error: Length of {key} must be equal to {settings["total_player_number"] - settings["human_player_number"]}.")
            sys.exit(1)

        for typ in lis_value:
            if type(typ) is not str:
                print(f"Error: '{key}' must contain only strings.")
                sys.exit(1)
            if typ not in lis:
                print(f"Error: '{key}' must contain only types from {lis}.")
                sys.exit(1)

        if not (1 <= settings["rounds_to_win"] <= 4) :
            print("Error: 'rounds_to_win' must be between 1 and 4, inclusive.")
            sys.exit(1)

    return settings
