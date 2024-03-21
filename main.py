import os
import re
import glob
from PTN.parse import (
    PTN,
)  # For parsing filenames pip install parse-torrent-name was not working for me
import json
import requests
from thefuzz import fuzz  # For matching titles with tmdb
import time
import math
import argparse
from mediainfo import get_media_info, format_media_info

ptn = PTN()


def parse(name):
    return ptn.parse(name)


class Settings:
    def __init__(self):
        self.default_settings = {
            "directories": [],
            "tmdb_key": "",  # https://www.themoviedb.org/settings/api
            "blu_key": "",  # https://blutopia.cc/users/{YOUR_USERNAME}/apikeys
            "l4g_path": "",
            "blu_cooldown": 5,  # In seconds
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
            ],  # See patterns.py for valid options, note "bluray" get's changed to encode in scan_directories()
            "ignored_keywords": [
                "10bit"
            ],  # This could be anything that would end up in the excess of parsed filename.
        }
        self.current_settings = None
        # Creating settings.json with default settings
        if not os.path.exists("settings.json") or os.path.getsize("settings.json") < 10:
            with open("settings.json", "w") as outfile:
                json.dump(self.default_settings, outfile)
        # Load settings.json
        if os.path.getsize("settings.json") > 10:
            with open("settings.json", "r") as file:
                self.current_settings = json.load(file)

    def update_setting(self, target, value):
        settings = self.current_settings
        if target in settings:
            if isinstance(settings[target], str):
                settings[target] = value
                print(value, " Successfully added to ", target)
            elif isinstance(settings[target], list):
                if target == "directories":
                    if os.path.exists(value) and value not in settings[target]:
                        settings[target].append(value)
                        print(value, " Successfully added to ", target)
                    elif value in settings[target]:
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
                    print("Value ", value, " Not recognized, try False, F or True, T")
            elif isinstance(settings[target], int):
                settings[target] = int(value)
                print(value, " Successfully added to ", target)

        self.current_settings = settings
        self.write_settings()

    def return_setting(self, target):
        if target in self.current_settings:
            return(self.current_settings[target])
        else:
            return(target, " Not found in current settings.")

    def write_settings(self):
        with open("settings.json", "w") as outfile:
            json.dump(self.current_settings, outfile)

    def reset_settings(self):
        with open("settings.json", "w") as outfile:
            json.dump(self.default_settings, outfile)


class BluChecker:
    def __init__(self):
        self.settings = Settings()
        self.update_settings()
        self.resolution_map = {
            "4320p": 11,
            "2160p": 1,
            "1080p": 2,
            "1080i": 3,
            "720p": 5,
            "576p": 6,
            "576i": 7,
            "480p": 8,
            "480i": 9,
        }
        self.data_json = {}
        self.data_blu = {
            "safe": {},  # These are movies where there were no results searching Blu. Probably safe.
            "risky": {},  # These are movies that exist on Blu but the quality [web-dl, remux, etc.] don't exist. These should definitely be checked manually.
            "danger": {},  # These movies exist on Blu, but the input file didn't provide a quality.
        }
        self.extract_filename = re.compile(r"^.*[\\\/](.*)")
        if not os.path.exists("database.json"):
            with open("database.json", "w") as outfile:
                json.dump({}, outfile)
        if not os.path.exists("blu_data.json"):
            with open("blu_data.json", "w") as outfile:
                json.dump(self.data_blu, outfile)
        self.database_location = "database.json"
        self.blu_data_location = "blu_data.json"

        # Fill with cached data
        if os.path.getsize(self.database_location) > 10:
            with open(self.database_location, "r") as file:
                self.data_json = json.load(file)
        if os.path.getsize(self.blu_data_location) > 10:
            with open(self.blu_data_location, "r") as file:
                self.data_blu = json.load(file)

    # Scan given directories
    def scan_directories(self):
        if not self.directories or not self.directories[0]:
            print("Please update add directories in main.py")
            return
        # loop through provided directories
        for dir in self.directories:
            # check if the directory has previously scanned data
            if dir in self.data_json:
                dir_data = self.data_json[dir]
            else:
                dir_data = {}
            print("Scanning Directories")
            # get all .mkv files in current directory
            files = glob.glob(f"{dir}**\\*.mkv", recursive=True) or glob.glob(
                f"{dir}**/*.mkv", recursive=True
            )
            for f in files:
                file_location = f
                file_name = self.extract_filename.match(f).group(1)
                bytes = os.path.getsize(f)
                file_size = self.convert_size(bytes)
                # check if file exists in our database already
                if file_name in dir_data:
                    continue
                parsed = parse(file_name)
                group = (
                    re.sub(r"(\..*)", "", parsed["group"])
                    if "group" in parsed
                    else None
                )
                banned = False

                year = str(parsed["year"]).strip() if "year" in parsed else ""
                title = parsed["title"].strip()
                year_in_title = re.search(r"\d{4}", title)
                # Extract the year from the title if PTN didn't work properly hopefully this doesn't ruin movies with a year in the title like 2001 a space...
                # but I noticed a lot of failed parses in my testing.
                if year_in_title and not year:
                    year = year_in_title.group().strip()
                    # Only remove year from title if parser didn't add year. Hopefully this helps with the above possible problem
                    title = re.sub(r"[\d]{4}", "", title).strip()
                    print("Year manually added to title: ", title, year)
                quality = (
                    re.sub(r"[^a-zA-Z]", "", parsed["quality"]).strip()
                    if "quality" in parsed
                    else None
                )
                quality = quality.lower() if quality else None
                if quality == "bluray":
                    quality = "encode"
                resolution = (
                    parsed["resolution"].strip() if "resolution" in parsed else None
                )
                # Set these to banned so they're saved in our database and we don't re-scan every time.
                if group in self.banned_groups:
                    banned = True
                elif bytes < (self.minimum_size * 1024) * 1024:
                    banned = True
                elif "season" in parsed or "episode" in parsed:
                    banned = True
                elif quality and (quality in self.ignore_qualities):
                    banned = True
                if "excess" in parsed:
                    for kw in self.ignore_keywords:
                        if kw.lower() in (
                            excess.lower() for excess in parsed["excess"]
                        ):
                            banned = True
                            break
                dir_data[file_name] = {
                    "file_location": file_location,
                    "file_name": file_name,
                    "file_size": file_size,
                    "title": title,
                    "quality": quality,
                    "resolution": resolution,
                    "year": year,
                    "tmdb": None,
                    "banned": banned,
                }

            self.data_json[dir] = dir_data
            self.save_database()

    # Get the tmdbId
    def get_tmdb(self):
        if not self.data_json:
            print("Please scan directories first")
            return
        for dir in self.data_json:
            for key, value in self.data_json[dir].items():
                if value["banned"]:
                    continue
                if value["tmdb"]:
                    continue
                title = value["title"]
                print(f"Searching TMDB for {title}")
                year = value["year"] if value["year"] else ""
                year_url = f"&year={year}" if year else ""
                # This seems possibly problematic
                clean_title = re.sub(r"[^a-zA-Z]", " ", title)
                query = clean_title.replace(" ", "%20")
                url = f"https://api.themoviedb.org/3/search/movie?query={query}&include_adult=false&language=en-US&page=1&api_key={self.tmdb_key}{year_url}"
                res = requests.get(url)
                data = json.loads(res.content)
                results = data["results"] if "results" in data else None
                # So we don't keep searching queries with no results
                if not results[0]:
                    value["banned"] = True
                    continue
                for result in results:
                    # This definitely isn't a great solution but I was noticing improper matches. ex: Mother 2009
                    if result["vote_count"] and result["vote_count"] < 10:
                        continue

                    tmdb_title = result["title"]
                    tmdb_year = (
                        re.search(r"\d{4}", result["release_date"]).group().strip()
                        if result["release_date"]
                        else None
                    )
                    match = fuzz.ratio(tmdb_title, clean_title)
                    if match >= 85:
                        id = result["id"]
                        value["tmdb"] = id
                        value["tmdb_title"] = tmdb_title
                        value["tmdb_year"] = tmdb_year
                        break
            self.save_database()
        self.save_database()

    # Search blu
    def search_blu(self):
        for dir in self.data_json:
            for key, value in self.data_json[dir].items():
                # Skip unnecessary searches.
                if value["banned"]:
                    continue
                if "blu" in value:
                    continue
                if value["tmdb"] is None:
                    continue

                print(f"Searching Blu for {value['title']}")
                tmdb = value["tmdb"]
                quality = value["quality"] if value["quality"] else None
                resolution = value["resolution"] if value["resolution"] else None

                blu_resolution = (
                    self.resolution_map.get(resolution) if resolution else None
                )
                reso_query = (
                    f"&resolutions[0]={blu_resolution}" if blu_resolution else ""
                )

                url = f"https://blutopia.cc/api/torrents/filter?tmdbId={tmdb}&categories[]=1&api_token={self.blu_key}{reso_query}"
                response = requests.get(url)
                res_data = json.loads(response.content)
                results = res_data["data"] if res_data["data"] else None

                if results and self.allow_dupes:
                    if quality:
                        for result in results:
                            info = result["attributes"]
                            blu_quality = re.sub(r"[^a-zA-Z]", "", info["type"]).strip()
                            if blu_quality.lower() == quality.lower():
                                value["blu"] = True
                                break
                            else:
                                value["blu"] = (
                                    f"On Blu, but quality [{quality}] was not found, double check to make sure."
                                )
                    elif blu_resolution:
                        value["blu"] = (
                            f"Source was found on Blu at {resolution}, but couldn't determine input source quality. Manual search required."
                        )
                    else:
                        value["blu"] = (
                            "Source was found on Blu, but couldn't determine input source quality or resolution. Manual search required."
                        )
                else:
                    value["blu"] = False
                time.sleep(self.blu_cooldown)
                self.save_database()
        self.save_database()

    # Create blu_data.json
    def create_blu_data(self, mediainfo=True):
        print("Creating Blu data.")
        for dir in self.data_json:
            for key, value in self.data_json[dir].items():
                if value["banned"]:
                    continue
                if "blu" not in value:
                    continue
                title = value["title"]
                year = value["year"]
                file_location = value["file_location"]
                file_size = value["file_size"]
                quality = value["quality"]
                resolution = value["resolution"]
                tmdb = value["tmdb"]
                tmdb_year = value["tmdb_year"]
                blu = value["blu"]
                extra_info = (
                    "TMDB Release year and given year are different this might mean improper match manual search required"
                    if (year != tmdb_year)
                    else ""
                )
                message = (
                    "Either not on Blu or new resolution."
                    if blu is False
                    else "Dupe!"
                    if blu is True
                    else blu
                )
                media_info = {}
                if mediainfo is True:
                    audio_language, subtitles, video_info, audio_info = get_media_info(
                        file_location
                    )
                    if "en" not in audio_language and "en" not in subtitles:
                        extra_info += " No English subtitles found in media info"
                    media_info = {
                        "audio_language(s)": audio_language,
                        "subtitle(s)": subtitles,
                        "video_info": video_info,
                        "audio_info": audio_info,
                    }
                info = {
                    "file_location": file_location,
                    "year": year,
                    "quality": quality,
                    "resolution": resolution,
                    "tmdb": tmdb,
                    "tmdb_year": tmdb_year,
                    "blu_message": message,
                    "file_size": file_size,
                    "extra_info": extra_info,
                    "mediainfo": media_info,
                }

                if not blu and (tmdb_year == year):
                    self.data_blu["safe"][title] = info
                elif blu is True:
                    continue
                elif blu is not False and ("not found" in blu):
                    self.data_blu["risky"][title] = info
                elif "English" in extra_info:
                    self.data_blu["danger"][title] = info
                else:
                    self.data_blu["danger"][title] = info
        self.save_blu_data()

    # Update database.json
    def save_database(self):
        with open(self.database_location, "w") as of:
            json.dump(self.data_json, of)

    # Update blu_data.json
    def save_blu_data(self):
        with open(self.blu_data_location, "w") as of:
            json.dump(self.data_blu, of)

    # Empty json files
    def clear_data(self):
        with open(self.blu_data_location, "w") as of:
            json.dump({}, of)
        with open(self.database_location, "w") as of:
            json.dump({}, of)

    # Run main functions
    def run_all(self, mediainfo=True):
        self.scan_directories()
        self.get_tmdb()
        self.search_blu()
        self.create_blu_data(mediainfo)
        self.export_l4g()
        self.export_manual()

    # Export l4g commands to l4g.txt
    def export_l4g(self):
        with open("l4g.txt", "w") as f:
            f.write("")
        # L4G Flags for commands -m recommended if you haven't manually checked blu already
        flags = ["-m", "-blu"]
        flags = " ".join(flags)
        # 'python3' on linux
        python = "py"
        for key, value in self.data_blu["safe"].items():
            line = (
                python
                + " "
                + self.L4G_path
                + "upload.py"
                + " "
                + flags
                + " "
                + value["file_location"]
            )
            with open("l4g.txt", "a") as f:
                f.write(line + "\n")
        print("L4G lines saved to l4g.txt")

    # Export possible uploads to manual.txt
    def export_manual(self):
        with open("manual.txt", "w") as f:
            f.write("")
        for key, value in self.data_blu.items():
            if value:
                with open("manual.txt", "a") as file:
                    file.write(key + "\n")
            for k, v in self.data_blu[key].items():
                title = k
                url_query = title.replace(" ", "%20")
                file_location = v["file_location"]
                quality = v["quality"]
                tmdb = v["tmdb"]
                blu_info = v["blu_message"]
                file_size = v["file_size"]
                extra_info = v["extra_info"] if v["extra_info"] else ""
                tmdb_year = v["tmdb_year"]
                year = v["year"]
                tmdb_search = f"https://www.themoviedb.org/movie/{tmdb}"
                blu_tmdb = f"https://blutopia.cc/torrents?view=list&tmdbId={tmdb}"
                blu_query = f"https://blutopia.cc/torrents?view=list&name={url_query}"
                media_info = v["mediainfo"] if v["mediainfo"] else "None"
                clean_mi = ""
                if media_info:
                    audio_language, audio_info, subtitles, video_info = (
                        format_media_info(media_info)
                    )
                    clean_mi = f"""
        Language(s): {audio_language}
        Subtitle(s): {subtitles}
        Audio Info: {audio_info}
        Video Info: {video_info}
                    """
                line = f"""
    Movie Title: {title}
    File Year: {year}
    TMDB Year: {tmdb_year}
    Quality: {quality}
    File Location: {file_location}
    File Size: {file_size}
    Blu TMDB Search: {blu_tmdb}
    Blu String Search: {blu_query}
    TMDB: {tmdb_search}
    Blu Search Info: {blu_info}
    Extra Info: {extra_info}
    Media Info: {clean_mi}
    """
                with open("manual.txt", "a") as f:
                    f.write(line + "\n")
        print("Manual info saved to manual.txt")

    # Settings functions
    def update_settings(self):
        self.current_settings = self.settings.current_settings
        self.directories = self.current_settings["directories"]
        self.tmdb_key = self.current_settings["tmdb_key"]
        self.blu_key = self.current_settings["blu_key"]
        self.L4G_path = self.current_settings["l4g_path"]
        self.blu_cooldown = self.current_settings["blu_cooldown"]
        self.minimum_size = self.current_settings["min_file_size"]
        self.allow_dupes = self.current_settings["allow_dupes"]
        self.banned_groups = self.current_settings["banned_groups"]
        self.ignore_qualities = self.current_settings["ignored_qualities"]
        self.ignore_keywords = self.current_settings["ignored_keywords"]

    def update_setting(self, target, value):
        self.settings.update_setting(target, value)
        self.update_settings()

    def get_setting(self, target):
        setting = self.settings.return_setting(target)
        if setting:
            print(setting)
        else:
            print("Not set yet.")

    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])


ch = BluChecker()
parser = argparse.ArgumentParser()

FUNCTION_MAP = {
    "scan": ch.scan_directories,
    "tmdb": ch.get_tmdb,
    "search": ch.search_blu,
    "blu": ch.create_blu_data,
    "l4g": ch.export_l4g,
    "manual": ch.export_manual,
    "run-all": ch.run_all,
    "clear-data": ch.clear_data,
    "add-setting": ch.update_setting,
    "setting": ch.get_setting,
}


parser.add_argument("command", choices=FUNCTION_MAP.keys())

# Add specific flags for the "blu" command
parser.add_argument(
    "-m",
    "--mediainfo",
    action="store_false",
    help="Turn off mediainfo scanning, only works on blu",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Print more things! Note: this don work yet",
)
parser.add_argument(
    "--target", "-t",
    help="Specify the target setting to update. Valid targets: directories, tmdb_key, blu_key, l4g_path, blu_cooldown, min_file_size, allow_dupes, banned_groups, ignored_qualities, ignored_keywords",
)
parser.add_argument("--set", "-s", help="Specify the new value for the target setting")

args = parser.parse_args()

# Get the appropriate function based on the command
func = FUNCTION_MAP[args.command]

# Call the function with appropriate arguments
if args.command == "blu":
    func(mediainfo=args.mediainfo)
elif args.command == "run-all":
    func(mediainfo=args.mediainfo)
elif args.command == "add-setting":
    func(args.target, args.set)
elif args.command == "setting":
    func(args.target)
else:
    func()