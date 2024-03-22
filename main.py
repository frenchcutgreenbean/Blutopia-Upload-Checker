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
from settings import Settings


class BluChecker:
    def __init__(self):
        self.settings = Settings()
        self.update_settings()
        self.RESOLUTION_MAP = {
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
        self.term_size = os.get_terminal_size()
        self.extract_filename = re.compile(r"^.*[\\\/](.*)")
        try:
            if not os.path.exists("database.json"):
                with open("database.json", "w") as outfile:
                    json.dump({}, outfile)
            if not os.path.exists("blu_data.json"):
                with open("blu_data.json", "w") as outfile:
                    json.dump(self.data_blu, outfile)
            self.database_location = "database.json"
            self.blu_data_location = "blu_data.json"
        except Exception as e:
            print("Error initializing json files: ", e)

        try:
            # Fill with cached data
            if os.path.getsize(self.database_location) > 10:
                with open(self.database_location, "r") as file:
                    self.data_json = json.load(file)
            if os.path.getsize(self.blu_data_location) > 10:
                with open(self.blu_data_location, "r") as file:
                    self.data_blu = json.load(file)
        except Exception as e:
            print("Error loading json files: ", e)

    # Scan given directories
    def scan_directories(self, verbose=False):
        try:
            if not self.directories or not self.directories[0]:
                print("Please update directories in main.py")
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
                    if verbose:
                        print("=" * self.term_size.columns)
                        print(f"Scanning: {f}")
                    file_location = f
                    file_name = self.extract_filename.match(f).group(1)
                    bytes = os.path.getsize(f)
                    file_size = self.convert_size(bytes)
                    if verbose:
                        print("File size: ", file_size)
                    # check if file exists in our database already
                    if file_name in dir_data:
                        if verbose:
                            print(file_name, "Already exists in database.")
                        continue
                    parsed = parse_file(file_name)
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
                        print("Year manually added from title: ", title, year)
                    quality = (
                        re.sub(r"[^a-zA-Z]", "", parsed["quality"]).strip()
                        if "quality" in parsed
                        else None
                    )
                    quality = quality.lower() if quality else None
                    if quality == "bluray":
                        quality = "encode"
                    elif quality == "web":
                        quality = "webrip"
                    resolution = (
                        parsed["resolution"].strip() if "resolution" in parsed else None
                    )
                    # Set these to banned so they're saved in our database and we don't re-scan every time.
                    if group in self.banned_groups:
                        if verbose:
                            print(group, "Is flagged for banning. Banned")
                        banned = True
                    elif bytes < (self.minimum_size * 1024) * 1024:
                        if verbose:
                            print(file_size, "Is below accepted size. Banned")
                        banned = True
                    elif "season" in parsed or "episode" in parsed:
                        if verbose:
                            print(file_name, "Is flagged as tv. Banned")
                        banned = True
                    elif quality and (quality in self.ignore_qualities):
                        if verbose:
                            print(quality, "Is flagged for banning. Banned")
                        banned = True
                    if "excess" in parsed:
                        for kw in self.ignore_keywords:
                            if kw.lower() in (
                                excess.lower() for excess in parsed["excess"]
                            ):
                                if verbose:
                                    print(
                                        "Keyword ", kw, "Is flagged for banning. Banned"
                                    )
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
                    if verbose and not banned:
                        print(dir_data[file_name])
                self.data_json[dir] = dir_data
                self.save_database()
        except Exception as e:
            print("Error scanning directories: ", e)

    # Get the tmdbId
    def get_tmdb(self, verbose=False):
        try:
            if not self.data_json:
                print("Please scan directories first")
                return
            for dir in self.data_json:
                if verbose:
                    print("Searching files from: ", dir)
                for key, value in self.data_json[dir].items():
                    if value["banned"]:
                        continue
                    if value["tmdb"]:
                        if value["tmdb"] and verbose:
                            print(value["title"], " Already searched on TMDB.")
                        continue
                    if verbose:
                        print("=" * self.term_size.columns)
                    title = value["title"]
                    print(f"Searching TMDB for {title}")
                    year = value["year"] if value["year"] else ""
                    year_url = f"&year={year}" if year else ""
                    if year_url and verbose:
                        print("Searching: ", title, "without year.")
                    else:
                        print("Searching: ", title, "with year.", year)
                    # This seems possibly problematic
                    clean_title = re.sub(r"[^a-zA-Z]", " ", title)
                    query = clean_title.replace(" ", "%20")
                    try:
                        url = f"https://api.themoviedb.org/3/search/movie?query={query}&include_adult=false&language=en-US&page=1&api_key={self.tmdb_key}{year_url}"
                        res = requests.get(url)
                        data = json.loads(res.content)
                        results = data["results"] if "results" in data else None
                        # So we don't keep searching queries with no results
                        if not results:
                            if verbose:
                                print("No results, Banning.")
                            value["banned"] = True
                            self.save_database()
                            continue
                        for r in results:
                            # This definitely isn't a great solution but I was noticing improper matches. ex: Mother 2009
                            if "vote_count" in r and (
                                r["vote_count"] == 0 or r["vote_count"] <= 5
                            ):
                                value["banned"] = True
                                self.save_database()
                                continue

                            tmdb_title = r["title"]
                            tmdb_year = (
                                re.search(r"\d{4}", r["release_date"]).group().strip()
                                if r["release_date"]
                                else None
                            )
                            match = fuzz.ratio(tmdb_title, clean_title)
                            if verbose:
                                print(
                                    "attempting to match result: ",
                                    tmdb_title,
                                    "with: ",
                                    title,
                                )
                            if match >= 85:
                                id = r["id"]
                                value["tmdb"] = id
                                value["tmdb_title"] = tmdb_title
                                value["tmdb_year"] = tmdb_year
                                if verbose:
                                    print("Match successful")
                                break
                        if verbose and not value["tmdb"]:
                            print("Couldn't find a match.")
                    except Exception as e:
                        print(
                            f"Something went wrong when searching TMDB for {title}", e
                        )
                self.save_database()
            self.save_database()
        except Exception as e:
            print("Error searching TMDB: ", e)

    # Search blu
    def search_blu(self, verbose=False):
        try:
            print("Searching Blu")
            for dir in self.data_json:
                for key, value in self.data_json[dir].items():
                    # Skip unnecessary searches.
                    if value["banned"]:
                        continue
                    if "blu" in value:
                        continue
                    if value["tmdb"] is None:
                        continue
                    if verbose:
                        print("=" * self.term_size.columns)
                        print(f"Searching Blu for {value['title']}")
                    tmdb = value["tmdb"]
                    quality = value["quality"] if value["quality"] else None
                    resolution = value["resolution"] if value["resolution"] else None
                    blu_resolution = (
                        self.RESOLUTION_MAP.get(resolution) if resolution else None
                    )
                    reso_query = (
                        f"&resolutions[0]={blu_resolution}" if blu_resolution else ""
                    )
                    try:
                        url = f"https://blutopia.cc/api/torrents/filter?tmdbId={tmdb}&categories[]=1&api_token={self.blu_key}{reso_query}"
                        response = requests.get(url)
                        res_data = json.loads(response.content)
                        results = res_data["data"] if res_data["data"] else None
                        resolution_msg = f" at {resolution} " if resolution else ""
                        if resolution and verbose:
                            print("Resolution detected: ", resolution)
                        blu_message = None
                        if results and self.allow_dupes:
                            if quality:
                                for result in results:
                                    info = result["attributes"]
                                    blu_quality = re.sub(
                                        r"[^a-zA-Z]", "", info["type"]
                                    ).strip()
                                    if blu_quality.lower() == quality.lower():
                                        blu_message = True
                                        value["blu"] = blu_message
                                        break
                                    else:
                                        blu_message = f"On Blu{resolution_msg}, but quality [{quality}] was not found, double check to make sure."
                                        value["blu"] = blu_message
                            elif blu_resolution:
                                blu_message = f"Source was found on Blu at {resolution}, but couldn't determine input source quality. Manual search required."
                                value["blu"] = blu_message
                            else:
                                blu_message = "Source was found on Blu, but couldn't determine input source quality or resolution. Manual search required."
                                value["blu"] = blu_message
                        elif resolution:
                            blu_message = f"Not on Blu{resolution_msg}"
                            value["blu"] = blu_message
                        else:
                            blu_message = False
                            value["blu"] = blu_message
                        if verbose:
                            if blu_message is True:
                                print("Already on Blu")
                            elif blu_message is False:
                                print("Not on Blu")
                            else:
                                print(blu_message)
                    except Exception as e:
                        print(
                            f"Something went wrong searching blu for {value['title']} ",
                            e,
                        )
                    time.sleep(self.blu_cooldown)
                    self.save_database()
            self.save_database()
        except Exception as e:
            print("Error searching blu: ", e)

    # Create blu_data.json
    def create_blu_data(self, mediainfo=True):
        try:
            print("Creating Blu data.")
            for dir in self.data_json:
                for key, value in self.data_json[dir].items():
                    if value["banned"]:
                        continue
                    if "blu" not in value:
                        continue
                    blu = value["blu"]
                    if blu is True:
                        continue
                    title = value["title"]
                    year = value["year"]
                    file_location = value["file_location"]
                    file_size = value["file_size"]
                    quality = value["quality"]
                    resolution = value["resolution"]
                    tmdb = value["tmdb"]
                    tmdb_year = value["tmdb_year"]
                    extra_info = (
                        "TMDB Release year and given year are different this might mean improper match manual search required"
                        if (year != tmdb_year)
                        else ""
                    )
                    message = (
                        "Not on Blu"
                        if blu is False
                        else "Dupe!"
                        if blu is True
                        else blu
                    )
                    media_info = {}
                    if mediainfo is True:
                        audio_language, subtitles, video_info, audio_info = (
                            get_media_info(file_location)
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
                    if " No English subtitles found in media info" in extra_info:
                        self.data_blu["danger"][title] = info
                        continue
                    elif tmdb_year == year:
                        if blu is False:
                            self.data_blu["safe"][title] = info
                            continue
                        elif "Not on Blu" in blu:
                            self.data_blu["safe"][title] = info
                            continue
                    elif blu is False:
                        self.data_blu["risky"][title] = info
                        continue
                    elif "not found" in blu:
                        self.data_blu["risky"][title] = info
                        continue
                    else:
                        self.data_blu["danger"][title] = info
            self.save_blu_data()
        except Exception as e:
            print("Error creating blu_data.json", e)

    # Update database.json
    def save_database(self):
        try:
            with open(self.database_location, "w") as of:
                json.dump(self.data_json, of)
        except Exception as e:
            print("Error writing to database.json: ", e)

    # Update blu_data.json
    def save_blu_data(self):
        try:
            with open(self.blu_data_location, "w") as of:
                json.dump(self.data_blu, of)
        except Exception as e:
            print("Error writing to blu_data.json: ", e)

    # Empty json files
    def clear_data(self):
        try:
            with open(self.blu_data_location, "w") as of:
                json.dump({}, of)
            with open(self.database_location, "w") as of:
                json.dump({}, of)
            print("Data cleared!")
        except Exception as e:
            print("Error clearing json data: ", e)

    # Run main functions
    def run_all(self, mediainfo=True, verbose = False):
        self.scan_directories(verbose)
        self.get_tmdb(verbose)
        self.search_blu(verbose)
        self.create_blu_data(mediainfo)
        self.export_l4g()
        self.export_manual()

    # Export l4g commands to l4g.txt
    def export_l4g(self):
        try:
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
        except Exception as e:
            print("Error writing l4g.txt: ", e)

    # Export possible uploads to manual.txt
    def export_manual(self):
        try:
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
                    blu_query = (
                        f"https://blutopia.cc/torrents?view=list&name={url_query}"
                    )
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
        except Exception as e:
            print("Error writing manual.txt: ", e)

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


ptn = PTN()


def parse_file(name):
    return ptn.parse(name)


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
    default=True,
)
parser.add_argument(
    "--target",
    "-t",
    help="Specify the target setting to update. Valid targets: directories, tmdb_key, blu_key, l4g_path, blu_cooldown, min_file_size, allow_dupes, banned_groups, ignored_qualities, ignored_keywords",
)
parser.add_argument("--set", "-s", help="Specify the new value for the target setting")

parser.add_argument(
    "--verbose", "-v", action="store_true", help="Enable verbose output. Only works with [scan, tmdb, search, and run-all]", default=False
)


args = parser.parse_args()

# Get the appropriate function based on the command
func = FUNCTION_MAP[args.command]
func_args = {}

# Check if the function accepts mediainfo argument, and if yes, include it
if "mediainfo" in BluChecker.create_blu_data.__code__.co_varnames:
    if args.command in {"run-all", "blu"}:
        func_args["mediainfo"] = args.mediainfo

# Include other specific arguments based on the command
if args.command == "setting":
    func_args["target"] = args.target
if args.command == "add-setting":
    func_args["value"] = args.set
    func_args["target"] = args.target
if args.command in {"scan", "tmdb", "search", "run-all"}:
    func_args["verbose"] = args.verbose

# Call the function with appropriate arguments
func(**func_args)
