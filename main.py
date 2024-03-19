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

ptn = PTN()


def parse(name):
    return ptn.parse(name)


class BluChecker:
    def __init__(self):
        # Directories where your movies are stored
        # Format ['/home/torrents', '/home/media'] windows: ['C:\\torrents\\movies']
        self.directories = [""]
        # https://www.themoviedb.org/settings/api
        self.tmdb_key = ""
        # https://blutopia.cc/users/{YOUR_USERNAME}/apikeys
        self.blu_key = ""
        # If you plan to export l4g batch file
        self.L4G_path = "/example/Upload-Assistant/"
        self.blu_cooldown = (
            5  # idk what this should be, but definitely don't wanna spam the api
        )
        # If you want to check for specific qualities and resolutions
        self.allow_dupes = True
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

        # Groups banned on blu, you could also add groups like blu internals here to not search stuff probably already on blu
        self.banned_groups = [
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
        ]
        self.data_json = {}
        self.data_blu = {
            "safe": {},  # These are movies where there were no results searching blu for tmdb id and or a given resolution. Probably safe.
            "risky": {},  # These are movies that exist on blu but the quality [web-dl, remux, etc.] don't exist. These should definitely be checked manually.
            "danger": {},  # These movies exist on blu, but the input file didn't provide a quality. Probably not even worth the time to check manually.
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
        # loop through provided directories
        for dir in self.directories:
            # check if the directory has previously scanned data
            if dir in self.data_json:
                dir_data = self.data_json[dir]
            else:
                dir_data = {}
            print("Scanning Directories")
            # get all .mkv files in current directory
            for f in glob.glob(f"{dir}**\\*.mkv", recursive=True):
                file_location = f
                file_name = self.extract_filename.match(f).group(1)
                file_size = self.convert_size(os.path.getsize(f))
                # check if file exists in our database already
                if file_name in dir_data:
                    continue
                parsed = parse(file_name)
                # ignore television
                if "season" in parsed or "episode" in parsed:
                    continue
                group = re.sub(r"(\..*)", "", parsed["group"])
                banned = False
                if group in self.banned_groups:
                    banned = True
                year = str(parsed["year"]) if "year" in parsed else ""
                title = parsed["title"] + " " + year
                quality = parsed["quality"] if "quality" in parsed else None
                resolution = parsed["resolution"] if "resolution" in parsed else None

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
        for dir in self.data_json:
            for key, value in self.data_json[dir].items():
                if value["banned"]:
                    continue
                # if value["tmdb"]:
                #     continue
                title = value["title"]
                print(f"Searching TMDB for {title}")
                year = f'&year={value['year']}' if value["year"] else ""
                test = re.search(r" \d{4}$", title)
                # Extract the year from the title if PTN didn't work properly hopefully this doesn't ruin movies with a year in the title like 2001 a space...
                # but I noticed a lot of failed parses in my testing.
                if test and not year:
                    year = test.group().strip()
                rm_year = re.sub(r"[\d]{4}", "", title)
                clean_title = re.sub(r"[^a-zA-Z]", " ", rm_year)
                query = clean_title.replace(" ", "%20")
                url = f"https://api.themoviedb.org/3/search/movie?query={query}&include_adult=false&language=en-US&page=1&api_key={self.tmdb_key}{year}"
                res = requests.get(url)
                data = json.loads(res.content)
                results = data["results"] if data["results"] else []
                for result in results:
                    tmdb_title = result["title"]
                    match = fuzz.ratio(tmdb_title, clean_title)
                    if match >= 85:
                        id = result["id"] if "id" in result else 0
                        value["tmdb"] = id
                        value["tmdb_title"] = tmdb_title
                        break
        self.save_database()

    # Search blu
    def search_blu(self):
        for dir in self.data_json:
            for key, value in self.data_json[dir].items():
                # Don't search for banned releases
                if value["banned"]:
                    continue
                # Don't research the api
                if "blu" in value:
                    continue
                print(f"Searching Blu for {value["title"]}")
                tmdb = value["tmdb"]
                quality = (
                    re.sub(r"[^a-zA-Z]", "", value["quality"])
                    if value["quality"]
                    else None
                )
                resolution = value["resolution"] if value["resolution"] else None

                blu_resolution = (
                    self.resolution_map.get(resolution) if resolution else None
                )
                reso_query = (
                    f"&resolutions[0]={blu_resolution}" if blu_resolution else ""
                )

                if tmdb != "0":
                    url = f"https://blutopia.cc/api/torrents/filter?tmdbId={tmdb}&categories[]=1&api_token={self.blu_key}{reso_query}"
                    response = requests.get(url)
                res_data = json.loads(response.content)
                results = res_data["data"] if res_data["data"] else None

                if results and self.allow_dupes:
                    if quality:
                        for result in results:
                            info = result["attributes"]
                            blu_quality = re.sub(r"[^a-zA-Z]", "", info["type"])
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

    def create_blu_data(self):
        print("Creating Blu data.")
        for dir in self.data_json:
            for key, value in self.data_json[dir].items():
                if value["banned"]:
                    continue
                title = value["title"]
                file_location = value["file_location"]
                file_size = value["file_size"]
                quality = value["quality"]
                resolution = value["resolution"]
                tmdb = value["tmdb"]
                blu = value["blu"]
                message = (
                    "Either not on Blu or new resolution."
                    if blu is False
                    else "Dupe!"
                    if blu is True
                    else blu
                )

                info = {
                    "file_location": file_location,
                    "quality": quality,
                    "resolution": resolution,
                    "tmdb": tmdb,
                    "blu_message": message,
                    "file_size": file_size
                }

                if not value["blu"]:
                    self.data_blu["safe"][title] = info
                elif value["blu"] is True:
                    continue
                else:
                    if "not found" in value["blu"]:
                        self.data_blu["risky"][title] = info
                    else:
                        self.data_blu["danger"][title] = info
        self.save_blu_data()

    def save_database(self):
        with open(self.database_location, "w") as of:
            json.dump(self.data_json, of)

    def save_blu_data(self):
        with open(self.blu_data_location, "w") as of:
            json.dump(self.data_blu, of)

    def export_l4g(self):
        # L4G Flags for commands -m recomended if you haven't manually checked blu already
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

    def export_all(self):
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
                tmdb_search = f"https://www.themoviedb.org/movie/{tmdb}"
                blu_tmdb = f"https://blutopia.cc/torrents?view=list&tmdbId={tmdb}"
                blu_query = f"https://blutopia.cc/torrents?view=list&name={url_query}"
                line = f"""
    Movie Title: {title},
    Quality: {quality},
    File Location: {file_location},
    File Size: {file_size},
    Blu TMDB Search: {blu_tmdb},
    Blu String Search: {blu_query},
    TMDB: {tmdb_search},
    Blu Search Info: {blu_info}
    """
                with open("manual.txt", "a") as f:
                    f.write(line + "\n")
        print("Manual info saved to manual.txt")
    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])


ch = BluChecker()

# ch.scan_directories()
# ch.get_tmdb()
# ch.search_blu()
# ch.create_blu_data()
# ch.export_l4g()
# ch.export_all()
