import os
import json

class Settings:
    def __init__(self):
        self.default_settings = {
            "directories": [],
            "tmdb_key": "",  # https://www.themoviedb.org/settings/api
            "blu_key": "",  # https://blutopia.cc/users/{YOUR_USERNAME}/apikeys
            "l4g_path": "",
            "blu_cooldown": 5,  # In seconds. Anything less than 3 isn't recommended. 30 requests per minute is max before hit rate limits. - HDVinnie
            "min_file_size": 800,  # In MB
            "allow_dupes": True,  # If false only check for completely unique movies
            "banned_groups": [
                # Groups banned on blu by default.
                # Add any you like, blu internals is probably a good idea too.
                "[Oj]",
                "3LTON",
                "4yEo",
                "ADE",
                "AFG",
                "AniHLS",
                "AnimeRG",
                "AniURL",
                "AROMA",
                "aXXo",
                "Brrip",
                "CHD",
                "CM8",
                "CrEwSaDe",
                "d3g",
                "DeadFish",
                "DNL",
                "ELiTE",
                "eSc",
                "FaNGDiNG0",
                "FGT",
                "Flights",
                "FRDS",
                "FUM",
                "HAiKU",
                "HD2DVD",
                "HDS",
                "HDTime",
                "Hi10",
                "ION10",
                "iPlanet",
                "JIVE",
                "KiNGDOM",
                "Leffe",
                "LEGi0N",
                "LOAD",
                "MeGusta",
                "mHD",
                "mSD",
                "NhaNc3",
                "nHD",
                "nikt0",
                "NOIVTC",
                "nSD",
                "PiRaTeS",
                "playBD",
                "PlaySD",
                "playXD",
                "PRODJi",
                "RAPiDCOWS",
                "RARBG",
                "RetroPeeps",
                "RDN",
                "REsuRRecTioN",
                "RMTeam",
                "SANTi",
                "SicFoI",
                "SPASM",
                "SPDVD",
                "STUTTERSHIT",
                "Telly",
                "TM",
                "TRiToN",
                "UPiNSMOKE",
                "URANiME",
                "WAF",
                "x0r",
                "xRed",
                "XS",
                "YIFY",
                "ZKBL",
                "ZmN",
                "ZMNT",
            ],
            "ignored_qualities": [
                "dvdrip",
                "webrip",
                "bdrip",
                "cam",
                "ts",
                "telesync",
                "hdtv",
            ],  # See patterns.py for valid options, note "bluray" get's changed to encode in scan_directories()
            "ignored_keywords": [
                "10bit"
            ],  # This could be anything that would end up in the excess of parsed filename.
        }
        self.current_settings = None

        try:
            # Creating settings.json with default settings
            if (
                not os.path.exists("settings.json")
                or os.path.getsize("settings.json") < 10
            ):
                with open("settings.json", "w") as outfile:
                    json.dump(self.default_settings, outfile)
            # Load settings.json
            if os.path.getsize("settings.json") > 10:
                with open("settings.json", "r") as file:
                    self.current_settings = json.load(file)
                    self.validate_directories()
            if not self.current_settings:
                self.current_settings = self.default_settings
        except Exception as e:
            print("Error initializing settings: ", e)

    def validate_directories(self):
        try:
            print("Validating Directories")
            directories = self.current_settings["directories"]
            clean = []
            for dir in directories:
                if os.path.exists(dir):
                    trailing = os.path.join(dir, "")
                    clean.append(trailing)
                else:
                    print(dir, "Does not exist, removing")
            clean = list(set(clean))
            self.current_settings["directories"] = clean
            self.write_settings()
        except Exception as e:
            print("Error Validating Directories: ", e)

    def update_setting(self, target, value):
        try:
            settings = self.current_settings
            if target in settings:
                if isinstance(settings[target], str):
                    settings[target] = value
                    print(value, " Successfully added to ", target)
                elif isinstance(settings[target], list):
                    if target == "directories":
                        # Ensure trailing slashes
                        path = os.path.join(value, "")
                        if os.path.exists(path) and path not in settings[target]:
                            settings[target].append(path)
                            print(value, " Successfully added to ", target)
                        elif path in settings[target]:
                            print(value, " Already in ", target)
                        else:
                            print("Path not found")
                    else:
                        settings[target].append(value)
                        print(value, " Successfully added to ", target)
                elif isinstance(settings[target], bool):
                    if "t" in value.lower():
                        settings[target] = True
                        print(target, " Set to True")
                    elif "f" in value.lower():
                        settings[target] = False
                        print(target, " Set to False")
                    else:
                        print(
                            "Value ", value, " Not recognized, try False, F or True, T"
                        )
                elif isinstance(settings[target], int):
                    settings[target] = int(value)
                    print(value, " Successfully added to ", target)

            self.current_settings = settings
            self.write_settings()
        except Exception as e:
            print("Error updating setting", e)

    def return_setting(self, target):
        try:
            if target in self.current_settings:
                return self.current_settings[target]
            else:
                return (target, " Not found in current settings.")
        except Exception as e:
            print("Error returning settings: ", e)

    def write_settings(self):
        try:
            with open("settings.json", "w") as outfile:
                json.dump(self.current_settings, outfile)
        except Exception as e:
            print("Error writing settings: ", e)

    def reset_settings(self):
        try:
            with open("settings.json", "w") as outfile:
                json.dump(self.default_settings, outfile)
        except Exception as e:
            print("Error resetting settings: ", e)
