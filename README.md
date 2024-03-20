## Features

- Scan directories for movies (.mkv)
- Parse filenames then search on TMDB
- Use TMDB id + resolution (if found) to search Blutopia for unique movies
- Made for Blutopia, but I don't see why it wouldn't work on any UNIT3D API with the needed editing.


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
Edit need variables:
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

## Functions

```py
ch = BluChecker()

ch.scan_directories() # Scans given directories for all .mkv files. Parses filenames using PTN (parse-torrent-name) getting title, quality, resolution, group, etc.

ch.get_tmdb() # Search TMDB for parsed titles and release year if provided.

ch.search_blu() # Search Blu by TMDB ID + resolution. See if movie exists, or if quality or resolution are unique.

ch.create_blu_data() # Creates blu_data.json storing various information.
ch.export_l4g() # Exports l4g.txt for files most likely safe to upload. Note: probably don't use this.
ch.export_all() # Exports manual.txt of all possible hits + various useful information to ensure safe uploads.
```

## Example Outputs
blu_data.json
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
            "extra_info": "None"
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
            "extra_info": "None"
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
            "extra_info": "None"
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
    Extra Info: None
    

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
    Extra Info: None
    
risky

    Movie Title: Movie,
    File Year: 1966,
    TMDB Year: 1966,
    Quality: remux,
    File Location: /home/movies/Movie.1966.1080p.BluRay.REMUX.AVC.FLAC.1.0-EPSiLON.mkv,
    File Size: 21.95 GB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: On Blu, but quality [remux] was not found, double check to make sure.,
    Extra Info: None
    
```    



