## Features

- Scan directories for movies (.mkv)
- Parse filenames then search on TMDB
- Use TMDB id + resolution (if found) to search Blutopia for unique movies
- Made for Blutopia, but I don't see why it wouldn't work on any UNIT3D API with the needed editing.
- Ability to ignore groups, qualities, and other keywords.


## Setup

```sh
git clone https://github.com/frenchcutgreenbean/Blutopia-Upload-Checker.git
```
```sh
cd Blutopia-Upload-Checker
```
```sh
pip install -r requirements.txt
```
Edit needed variables:
```py
# Directories where your movies are stored
# Format ['/home/torrents', '/home/media'] windows: ['C:\\torrents\\movies']
self.directories = [""]
# https://www.themoviedb.org/settings/api
self.tmdb_key = ""
# https://blutopia.cc/users/{YOUR_USERNAME}/apikeys
self.blu_key = ""
# If you plan to export l4g batch file
self.L4G_path = "/example/Upload-Assistant/"
```
If you plan to use L4G you might need to change stuff here:

```py   
def export_l4g(self):
    # L4G Flags for commands -m recommended if you haven't manually checked blu already
    flags = ["-m", "-blu"]
    flags = " ".join(flags)
    # 'python3' on linux
    python = "py"
```

## Usage
```sh
python3 main.py run-all
```
Accepted commands:
```
run-all # Scans, Searches and exports possible uploads
cleanup # Empties database.json and blu_data.json

# These should be run in order. They need data from previous functions.
scan # Scans directories in main.py
tmdb # Searches TMDB for found movies  
search # Searches blu by TMDB id       
blu # Creates blu_data.json            
l4g # Creates l4g commands txt file
manual # Creates txt file with useful information for possible uploads
```
Accepted flags:
```
-m or --mediainfo This works only with the blu and run-all command it will disable scanning with mediainfo.
```
## Breakdown
### Scanning Process
We scan a given directory or directories for every .mkv file.

Then loop through every file and parse information from the filename.
This includes Titles, file size, quality, resolution, release group, etc.

Based on information extracted we can "ban" a file. 
This can happen when it's a TV show, the file is too small, from a banned release group, contains and undesired keyword (ie. "10bit"), and undesired qualities (bdrip, webrip, cam).
This will set the "banned" key in database.json to true. This is to prevent re-scanning files.

### Search TMDB
We then attempt to search TMDB based on title and if extracted year.
We then grab useful information from the results if a match was made.

### Search Blutopia
We take the TMDB ID and resolution (if extracted) and search Blu looping through the results (if any) and comparing qualities.

Any movie that get's results when a resolution and quality was extracted successfully get's ignored.


### Create blu_data.json
#### Mediainfo
This is enabled by default and can be disabled by passing -m or --mediainfo

We scan every potential uploadable file and get useful information.

The most useful being audio and subtitle languages as one of those need to be English to be uploaded to Blu.

#### Taking information from our Blu searches.

If no results or novel resolution we put this in the "safe" category.

If there are results but the quality is novel this goes in the "risky" category.

If there are results but resolution or quality couldn't be extracted from filename this gets put in the "danger" category. 

If the release year extracted differs from the release year from TMDB match, this gets put in the "danger" category and likely means TMDB mismatch.

And finally if media info couldn't find English audio or subtitles, this gets put in the danger category.

### Export information
#### L4G
We export every safe file to a text file.
#### Manual
We export every potential upload to a text file with useful information.

## Example Outputs
### blu_data.json
```json
{
    "safe": {
        "Movie": {
            "file_location": "/home/movies/Movie.2014.DC.1080p.BluRay.x264.DTS-WiKi.mkv",
            "year": "2014",
            "quality": "encode",
            "resolution": "1080p",
            "tmdb": 123,
            "tmdb_year": "2014",
            "blu_message": "Either not on Blu or new resolution.",
            "file_size": "9.73 GB",
            "extra_info": "None",
            "mediainfo": {
                "audio_language(s)": [
                    "en"
                ],
                "subtitle(s)": [
                    "en"
                ],
                "video_info": {
                    "bit_rate": 1647896,
                    "frame_rate": "23.976",
                    "format": "AVC",
                    "height": 404,
                    "width": 720
                },
                "audio_info": {
                    "track_2": {
                        "language": "en",
                        "channels": 2,
                        "format": "AAC"
                    }
                }
            }
        },
        "Movie": {
            "file_location": "/home/movies/Movie.2023.1080p.Filmin.WEB-DL.AAC.2.0.H.264-Tayy.mkv",
            "year": "2023",
            "quality": "webdl",
            "resolution": "1080p",
            "tmdb": 123,
            "tmdb_year": "2023",
            "blu_message": "Either not on Blu or new resolution.",
            "file_size": "4.74 GB",
            "extra_info": "None",
            "mediainfo": {
                "audio_language(s)": [
                    "en"
                ],
                "subtitle(s)": [
                    "en"
                ],
                "video_info": {
                    "bit_rate": 1647896,
                    "frame_rate": "23.976",
                    "format": "AVC",
                    "height": 404,
                    "width": 720
                },
                "audio_info": {
                    "track_2": {
                        "language": "en",
                        "channels": 2,
                        "format": "AAC"
                    }
                }
            }
        }
    },
    "risky": {
        "Movie": {
            "file_location": "/home/movies/Movie.1966.1080p.BluRay.REMUX.AVC.FLAC.1.0-EPSiLON.mkv",
            "year": "1966",
            "quality": "remux",
            "resolution": "1080p",
            "tmdb": 123,
            "tmdb_year": "1966",
            "blu_message": "On Blu, but quality [remux] was not found, double check to make sure.",
            "file_size": "21.95 GB",
            "extra_info": "None",
            "mediainfo": {
                "audio_language(s)": [
                    "en"
                ],
                "subtitle(s)": [
                    "en"
                ],
                "video_info": {
                    "bit_rate": 1647896,
                    "frame_rate": "23.976",
                    "format": "AVC",
                    "height": 404,
                    "width": 720
                },
                "audio_info": {
                    "track_2": {
                        "language": "en",
                        "channels": 2,
                        "format": "AAC"
                    }
                }
            }
        }
    },
    "danger": {}
}
```

l4g.txt
```
py /example/Upload-Assistant/upload.py -m -blu C:\Movie Title.2017.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv
py /example/Upload-Assistant/upload.py -m -blu C:\Movie Title.2001.AMZN.WEB-DL.DDP2.0.H.264-Kitsune.mkv
py /example/Upload-Assistant/upload.py -m -blu C:\Movie Title.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv
py /example/Upload-Assistant/upload.py -m -blu C:\Movie Title.2012.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv
```

manual.txt
```
safe

    Movie Title: Movie,
    File Year: 2014,
    TMDB Year: 2014,
    Quality: encode,
    File Location: /home/movies/Movie.2014.DC.1080p.BluRay.x264.DTS-WiKi.mkv,
    File Size: 9.73 GB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: Either not on Blu or new resolution.,
    Extra Info: 
    Media Info: 
                    Language(s): ['en']
                    Subtitle(s): ['en', 'es']
                    Audio Info: {'track_2': {'language': 'en', 'channels': 2, 'format': 'AC-3'}}
                    Video Info: {'bit_rate': 1136093, 'frame_rate': '29.970', 'format': 'AVC', 'height': 480, 'width': 700}
                    
    
    

    Movie Title: Movie,
    File Year: 2023,
    TMDB Year: 2023,
    Quality: webdl,
    File Location: /home/movies/Movie.2023.1080p.Filmin.WEB-DL.AAC.2.0.H.264-Tayy.mkv,
    File Size: 4.74 GB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: Either not on Blu or new resolution.,
    Extra Info: 
    Media Info: 
                    Language(s): ['en']
                    Subtitle(s): ['en', 'es']
                    Audio Info: {'track_2': {'language': 'en', 'channels': 2, 'format': 'AC-3'}}
                    Video Info: {'bit_rate': 1136093, 'frame_rate': '29.970', 'format': 'AVC', 'height': 480, 'width': 700}
                    
    
    
danger

    Movie Title: Movie,
    File Year: 1966,
    TMDB Year: 1966,
    Quality: remux,
    File Location: /home/movies/Movie.1966.1080p.BluRay.REMUX.AVC.FLAC.1.0-EPSiLON.mkv,
    File Size: 21.95 GB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: On Blu, but quality [remux] was not found, double check to make sure.
    Extra Info: TMDB Release year and given year are different this might mean improper match manual search required No English subtitles found in media info
    Media Info: 
                    Language(s): ['da']
                    Subtitle(s): []
                    Audio Info: {'track_2': {'language': 'da', 'channels': 6, 'format': 'AC-3'}}
                    Video Info: {'bit_rate': 3080628, 'frame_rate': '25.000', 'format': 'HEVC', 'height': 800, 'width': 1920}
                    
    
    
```    



