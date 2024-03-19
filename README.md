## Features

- Scan directories for movies (.mkv)
- Parse filenames then search on TMDB
- Use TMDB id + resolution (if found) to search Blutopia for unique movies


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
        "Movie Title": {
            "file_location": "C:\\Movie Title.2017.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv",
            "quality": "WEB-DL",
            "resolution": null,
            "tmdb": 123,
            "blu_message": "Either not on Blu or new resolution.",
            "file_size": "811.42 MB"
        },
        "Movie Title 2001": {
            "file_location": "C:\\Movie Title.2001.AMZN.WEB-DL.DDP2.0.H.264-Kitsune.mkv",
            "quality": "WEB-DL",
            "resolution": null,
            "tmdb": 123,
            "blu_message": "Either not on Blu or new resolution.",
            "file_size": "818.43 MB"
        },
        "Movie Title 2019": {
            "file_location": "C:\\Movie Title.2019.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv",
            "quality": "WEB-DL",
            "resolution": null,
            "tmdb": 123,
            "blu_message": "Either not on Blu or new resolution.",
            "file_size": "810.0 MB"
        },
        "Movie Title 2012": {
            "file_location": "C:\\Movie Title.2012.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv",
            "quality": "WEB-DL",
            "resolution": null,
            "tmdb": 123,
            "blu_message": "Either not on Blu or new resolution.",
            "file_size": "817.78 MB"
        }
    },
    "risky": {},
    "danger": {
        "Movie Title 2016": {
            "file_location": "C:\\Movie Title.1080p.DD5.1.x264-NTG.mkv",
            "quality": null,
            "resolution": "1080p",
            "tmdb": 123,
            "blu_message": "Source was found on Blu at 1080p, but couldn't determine input source quality. Manual search required.",
            "file_size": "808.63 MB"
        }
    }
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

    Movie Title: Movie Title 2017,
    Quality: WEB-DL,
    File Location: C:\Movie Title.2017.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv,
    File Size: 811.42 MB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=132,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie%20Title%202017,
    TMDB: https://www.themoviedb.org/movie/132,
    Blu Search Info: Either not on Blu or new resolution.
    

    Movie Title: Movie Title 2001,
    Quality: WEB-DL,
    File Location: C:\Movie Title.2001.AMZN.WEB-DL.DDP2.0.H.264-Kitsune.mkv,
    File Size: 818.43 MB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie%20Title%202001,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: Either not on Blu or new resolution.
    

    Movie Title: Freshman Year 2019,
    Quality: WEB-DL,
    File Location: C:\Movie Title.2019.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv,
    File Size: 810.0 MB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie%20Title%202019,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: Either not on Blu or new resolution.
    

    Movie Title: Movie Title 2012,
    Quality: WEB-DL,
    File Location: C:\Movie Title.2012.AMZN.WEB-DL.AAC2.0.H.264-Kitsune.mkv,
    File Size: 817.78 MB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie%20Title%202012,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: Either not on Blu or new resolution.
    
danger

    Movie Title: Movie Title 2016,
    Quality: None,
    File Location: C:\Movie Title.2016.1080p.DD5.1.x264-NTG.mkv,
    File Size: 808.63 MB,
    Blu TMDB Search: https://blutopia.cc/torrents?view=list&tmdbId=123,
    Blu String Search: https://blutopia.cc/torrents?view=list&name=Movie%20Title%202016,
    TMDB: https://www.themoviedb.org/movie/123,
    Blu Search Info: Source was found on Blu at 1080p, but couldn't determine input source quality. Manual search required.
    
```    



