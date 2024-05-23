from . import _
from .cache import IdRelativeCache
from .config import Config
from .csv import CSVFile
from .db import PlaybackReportingDb, LibraryDb
from .utils import ask_choice, format_duration, parse_time
from datetime import datetime
from re import compile
from os import makedirs
from os.path import join
from math import floor


ITEMNAME_PATTERN = compile(r'(?P<album_artist>.*) - (?P<track>.*) \((?P<album>.*)\)')  # noqa: E501
NOT_KNOWN = "Not Known"
TIME_BASE = 10_000_000


def print_item(item):
    s = item['Name']
    if item['Album']:
        s += "\n" + _("Album: ") + item['Album']
    if item['Artists']:
        s += "\n" + _("Artists: ") + item['Artists']
    if item['AlbumArtists']:
        s += "\n" + _("Album artists: ") + item['AlbumArtists']
    return s


class AudioSelector:
    def __init__(self, cfg: Config, origin, ldb: LibraryDb, choices=None):
        self.cfg = cfg
        self.origin = origin
        self.ldb = ldb
        self.choices = choices if choices and len(choices) else None
        self.re = None
        self.fns = []

    def print_original(self):
        print(_("Original item: ") + self.origin['track'])
        if self.origin['album']:
            print(_("Album: ") + self.origin['album'])
        if self.origin['album_artist']:
            print(_("Album artists: ") + self.origin['album_artist'])

    def choose_in_choices(self):
        item = ask_choice(self.cfg, self.choices, _("Please choose audio item:"), print_item, (("x", _("No item"), "none"), ("o", _("Choose other items"), "other"),))  # noqa: E501
        self.re = item
        if item == "none":
            self.re = None
        elif item == "other":
            self.fns.append(self.choose_others)

    def choose_others(self):
        act = [("i", _("Input item id"), "id"), ("t", _("Input track name"), "track"), ("a", _("Input album name"), "album"), ("x", _("No item"), "none")]  # noqa: E501
        if self.choices:
            act.append(("o", _("Choose in given choices"), "choose"))
        re = ask_choice(self.cfg, [], _("Please choose action: "), extra=act)
        if re == "choose":
            self.fns.append(self.choose_in_choices)
        elif re == "id":
            self.fns.append(self.input_id)
        elif re == "track":
            self.fns.append(self.input_track)
        elif re == "album":
            self.fns.append(self.input_album)
        elif re == "none":
            self.re = None

    def input_id(self):
        id = input(_("Please input item id:"))
        item = self.ldb.get_item(id)
        if item and item['type'] == 'MediaBrowser.Controller.Entities.Audio.Audio':  # noqa: E501
            self.re = item
        else:
            print(_("Item not found."))
            self.fns.append(self.choose_others)

    def handle_items(self, items):
        if len(items):
            act = [("b", _("Back"), "back"), ("x", _("No item"), "none")]
            if self.choices:
                act.append(("o", _("Choose in given choices"), "choose"))
            self.re = ask_choice(self.cfg, items, _("Please choose audio item:"), print_item, act)  # noqa: E501
            if self.re == "back":
                self.fns.append(self.choose_others)
            elif self.re == "choose":
                self.fns.append(self.choose_in_choices)
            elif self.re == "none":
                self.re = None
        else:
            print(_("Items not found."))
            self.fns.append(self.choose_others)

    def input_track(self):
        track = input(_("Please input track name:"))
        items = self.ldb.get_audios(track)
        self.handle_items(items)

    def input_album(self):
        album = input(_("Please input album name:"))
        items = self.ldb.get_audios(album=album)
        self.handle_items(items)

    def ask(self):
        self.print_original()
        if self.choices:
            self.fns.append(self.choose_in_choices)
        else:
            self.fns.append(self.choose_others)
        while True:
            if len(self.fns) == 0:
                break
            self.fns.pop(0)()
        return self.re


def prepare_audio_map(pdb: PlaybackReportingDb, ldb: LibraryDb,
                      icache: IdRelativeCache, cfg: Config):
    offset = 0
    data = pdb.get_activitys(offset, itemType='Audio')
    re = None
    itemMap = {}
    rowMap = {}
    while len(data) > 0:
        for d in data:
            itemId = d['ItemId']
            rowid = d['rowid']
            item = ldb.get_item(itemId)
            if not item:
                re = icache.get(itemId)
                if re and isinstance(re, str):
                    if re == 'no_track':
                        if itemId in itemMap:
                            rowMap[rowid] = itemId
                        else:
                            itemMap[itemId] = d
                            rowMap[rowid] = itemId
                        continue
                    re = None
                elif re:
                    item = ldb.get_item(re['id'])
                    if item and item['PresentationUniqueKey'] in itemMap:
                        rowMap[rowid] = item['PresentationUniqueKey']
                        continue
                else:
                    if itemId in itemMap:
                        rowMap[rowid] = itemId
                        continue
            else:
                if itemId in itemMap:
                    rowMap[rowid] = itemId
                    continue
            if not item:
                itemName = d['ItemName']
                if re is None:
                    re = ITEMNAME_PATTERN.match(itemName)
                if re is None:
                    raise ValueError(f"Failed to parse ItemName: {itemName}")
                re = re.groupdict()
                if re['album_artist'] == NOT_KNOWN:
                    re['album_artist'] = None
                if re['album'] == NOT_KNOWN:
                    re['album'] = None
                items = ldb.get_audios(re['track'], re['album'])
                if len(items) == 1:
                    newId = items[0]['PresentationUniqueKey']
                    icache.set(itemId, newId, {'album': items[0]['Album'], 'track': items[0]['Name'], 'album_artist': items[0]['AlbumArtists'], 'original': re})  # noqa: E501
                    item = items[0]
                else:
                    if not len(items):
                        items = ldb.get_audios(re['track'])
                    if not len(items) and re['album']:
                        items = ldb.get_audios(album=re['album'])
                    item = AudioSelector(cfg, re, ldb, items).ask()
                    if item:
                        newId = item['PresentationUniqueKey']
                        icache.set(itemId, newId, {'album': item['Album'], 'track': item['Name'], 'album_artist': item['AlbumArtists'], 'original': re})  # noqa: E501
                    else:
                        icache.set_value(itemId, 'no_track')
            if item:
                itemId = item['PresentationUniqueKey']
                itemMap[itemId] = item
                rowMap[rowid] = itemId
            else:
                itemMap[itemId] = d
                rowMap[rowid] = itemId
        offset += len(data)
        data = pdb.get_activitys(offset, itemType='Audio')
    albumMap = {}
    for itemId in itemMap:
        item = itemMap[itemId]
        album = ''
        album_artists = ''
        if 'type' in item:
            album = item['Album']
            album_artists = item['AlbumArtists']
        else:
            it = ITEMNAME_PATTERN.match(item['ItemName']).groupdict()
            if it['album'] != NOT_KNOWN:
                album = it['album']
            if it['album_artist'] != NOT_KNOWN:
                album_artists = it['album_artist']
        if album:
            if album not in albumMap:
                album_artists = album_artists if album_artists else None
                items = ldb.get_albums(album, album_artists)
                if len(items) == 0:
                    items = ldb.get_albums(album)
                if len(items) == 1:
                    albumMap[album] = items[0]
                elif len(items) > 1:
                    print(len(items))
                    raise NotImplementedError('FIX ME')
                else:
                    data = {'name': album}
                    if 'type' in item:
                        data['album_artists'] = item['AlbumArtists']
                        data['date'] = item['PremiereDate']
                        data['year'] = item['ProductionYear']
                        data['publisher'] = item['Studios']
                    else:
                        data['album_artists'] = album_artists
                        data['date'] = None
                        data['year'] = None
                        data['publisher'] = None
                    albumMap[album] = data
    return itemMap, rowMap, albumMap


def generate_audio_report(pdb: PlaybackReportingDb, itemMap, rowMap, albumMap,
                          output: str, userId: str = None,
                          startTime: float = None, endTime: float = None):
    makedirs(output, exist_ok=True)
    offset = 0
    data = pdb.get_activitys(offset, itemType='Audio', userId=userId,
                             startTime=startTime, endTime=endTime)
    albumCountMap = {}
    trackCountMap = {}
    artistCountMap = {}
    alArtCountMap = {}
    with CSVFile(join(output, "history.csv")) as his:
        his.write(_("Id"), _("Date"), _("Time"), _("Name"), _("Artists"), _("Album"), _("Album artists"), _("Duration"), _("Duration") + _("(seconds)"), _("Original item id"), _("Item id"), _("Play duration"), _("Play duration") + _("(seconds)"), _("Record content"), _("Client name"), _("Device name"), _("Playback method"), _("Play count"))  # noqa: E501
        while len(data) > 0:
            for i in data:
                rowid = i['rowid']
                itemId = rowMap[rowid]
                created = datetime.fromtimestamp(parse_time(i['DateCreated']),
                                                 None)
                date = created.strftime("%Y-%m-%d")
                time = created.strftime("%H:%M:%S.%f")
                item = itemMap[itemId]
                name = ''
                artists = ''
                album = ''
                album_artists = ''
                original_item_id = i['ItemId']
                play_duration = i['PlayDuration']
                duration = None
                play_count = 1
                if 'type' in item:
                    name = item['Name']
                    artists = item['Artists']
                    album = item['Album']
                    album_artists = item['AlbumArtists']
                    duration = item['RunTimeTicks'] / 10_000_000
                    play_count = floor(play_duration / duration)
                    extrad = play_duration % duration
                    if extrad > 60 or extrad > duration * 0.95:
                        play_count += 1
                else:
                    it = ITEMNAME_PATTERN.match(item['ItemName']).groupdict()
                    name = it['track']
                    if it['album'] != NOT_KNOWN:
                        album = it['album']
                    if it['album_artist'] != NOT_KNOWN:
                        album_artists = it['album_artist']
                his.write(rowid, date, time, name, artists, album, album_artists, format_duration(duration), duration, original_item_id, itemId, format_duration(play_duration), play_duration, i['ItemName'], i['ClientName'], i['DeviceName'], i['PlaybackMethod'], play_count)  # noqa: E501
                if album:
                    if album in albumCountMap:
                        tmp = albumCountMap[album]
                        tmp['count'] += 1
                        tmp['play_count'] += play_count
                        tmp['duration'] += play_duration
                    else:
                        albumCountMap[album] = {'count': 1,
                                                'play_count': play_count,
                                                'duration': play_duration}
                if itemId in trackCountMap:
                    tmp = trackCountMap[itemId]
                    tmp['count'] += 1
                    tmp['play_count'] += play_count
                    tmp['duration'] += play_duration
                else:
                    trackCountMap[itemId] = {'count': 1,
                                             'play_count': play_count,
                                             'duration': play_duration}
                if artists:
                    for art in artists.split("|"):
                        ar = art.strip()
                        if ar in artistCountMap:
                            tmp = artistCountMap[ar]
                            tmp['count'] += 1
                            tmp['play_count'] += play_count
                            tmp['duration'] += play_duration
                        else:
                            artistCountMap[ar] = {'count': 1,
                                                  'play_count': play_count,
                                                  'duration': play_duration}
                if album_artists:
                    if 'type' in item:
                        arts = album_artists.split("|")
                    else:
                        arts = album_artists.split(",")
                    for art in arts:
                        ar = art.strip()
                        if ar in alArtCountMap:
                            tmp = alArtCountMap[ar]
                            tmp['count'] += 1
                            tmp['play_count'] += play_count
                            tmp['duration'] += play_duration
                        else:
                            alArtCountMap[ar] = {'count': 1,
                                                 'play_count': play_count,
                                                 'duration': play_duration}
            offset += len(data)
            data = pdb.get_activitys(offset, itemType='Audio', userId=userId,
                                     startTime=startTime, endTime=endTime)
    with CSVFile(join(output, 'album.csv')) as al:
        al.write(_("Name"), _("Album artists"), _("Artists"), _("Record count"), _("Play count"), _("Play duration"), _("Play duration") + _("(seconds)"), _("Duration"), _("Duration") + _("(seconds)"), _("Year"), _("Publish date"), _("Publisher"), _("Item id"))  # noqa: E501
        for album in albumCountMap:
            if album not in albumMap:
                continue
            item = albumMap[album]
            album_artists = ''
            artists = ''
            count = albumCountMap[album]
            duration = None
            year = None
            publisher = None
            itemId = None
            if 'type' in item:
                album_artists = item['AlbumArtists']
                artists = item['Artists']
                duration = item['RunTimeTicks'] / TIME_BASE
                year = item['ProductionYear']
                date = item['PremiereDate']
                publisher = item['Studios']
                itemId = item['PresentationUniqueKey']
            else:
                album_artists = item['album_artists']
                year = item['year']
                date = item['date']
                publisher = item['publisher']
            if year and date:
                if date.endswith("-01-01 00:00:00"):
                    date = None
            al.write(album, album_artists, artists, count['count'], count['play_count'], format_duration(count['duration']), count['duration'], format_duration(duration), duration, year, date, publisher, itemId)  # noqa: E501
    with CSVFile(join(output, 'track.csv')) as tr:
        tr.write(_("Name"), _("Artists"), _("Record count"), _("Play count"), _("Play duration"), _("Play duration") + _("(seconds)"), _("Duration"), _("Duration") + _("(seconds)"), _("Album"), _("Album artists"), _("Genres"), _("Track no"), _("Disc no"), _("Year"), _("Publish date"), _("Publisher"), _("Item id"))  # noqa: E501
        for itemId in trackCountMap:
            item = itemMap[itemId]
            count = trackCountMap[itemId]
            name = ''
            artists = ''
            album = ''
            album_artists = ''
            genres = ''
            track = None
            disc = None
            year = None
            date = None
            publisher = None
            duration = None
            if 'type' in item:
                name = item['Name']
                artists = item['Artists']
                album = item['Album']
                album_artists = item['AlbumArtists']
                genres = item['Genres']
                track = item['IndexNumber']
                disc = item['ParentIndexNumber']
                duration = item['RunTimeTicks'] / TIME_BASE
                year = item['ProductionYear']
                date = item['PremiereDate']
                publisher = item['Studios']
            else:
                it = ITEMNAME_PATTERN.match(item['ItemName']).groupdict()
                name = it['track']
                if it['album'] != NOT_KNOWN:
                    album = it['album']
                if it['album_artist'] != NOT_KNOWN:
                    album_artists = it['album_artist']
            if year and date:
                if date.endswith("-01-01 00:00:00"):
                    date = None
            tr.write(name, artists, count['count'], count['play_count'], format_duration(count['duration']), count['duration'], format_duration(duration), duration, album, album_artists, genres, track, disc, year, date, publisher, itemId)  # noqa: E501
    with CSVFile(join(output, 'artist.csv')) as ar:
        ar.write(_("Name"), _("Record count"), _("Play count"), _("Play duration"), _("Play duration") + _("(seconds)"))  # noqa: E501
        for artist in artistCountMap:
            count = artistCountMap[artist]
            ar.write(artist, count['count'], count['play_count'], format_duration(count['duration']), count['duration'])  # noqa: E501
    with CSVFile(join(output, 'album_artist.csv')) as alAr:
        alAr.write(_("Name"), _("Record count"), _("Play count"), _("Play duration"), _("Play duration") + _("(seconds)"))  # noqa: E501
        for artist in alArtCountMap:
            count = alArtCountMap[artist]
            alAr.write(artist, count['count'], count['play_count'], format_duration(count['duration']), count['duration'])  # noqa: E501
