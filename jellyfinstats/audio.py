from . import _
from .cache import IdRelativeCache
from .config import Config
from .csv import CSVFile
from .db import PlaybackReportingDb, LibraryDb
from .utils import ask_choice, parse_time
from datetime import datetime
from re import compile
from os import makedirs
from os.path import join


ITEMNAME_PATTERN = compile(r'(?P<album_artist>.*) - (?P<track>.*) \((?P<album>.*)\)')  # noqa: E501


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
                if re['album_artist'] == 'Not Known':
                    re['album_artist'] = None
                if re['album'] == 'Not Known':
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
    return itemMap, rowMap


def generate_audio_report(pdb: PlaybackReportingDb, itemMap, rowMap,
                          output: str, userId: str = None,
                          startTime: float = None, endTime: float = None):
    makedirs(output, exist_ok=True)
    offset = 0
    data = pdb.get_activitys(offset, itemType='Audio', userId=userId,
                             startTime=startTime, endTime=endTime)
    with CSVFile(join(output, "history.csv")) as his:
        his.write(_("Id"), _("Date"), _("Time"), _("Name"), _("Artists"), _("Album"), _("Album artists"), _("Original item id"), _("Item id"), _("Play Duration"), _("Record content"), _("Client name"), _("Device name"), _("Playback method"))  # noqa: E501
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
                if 'type' in item:
                    name = item['Name']
                    artists = item['Artists']
                    album = item['Album']
                    album_artists = item['AlbumArtists']
                else:
                    it = ITEMNAME_PATTERN.match(item['ItemName']).groupdict()
                    name = it['track']
                    if it['album'] != 'Not Known':
                        album = it['album']
                    if it['album_artist'] != "Not Known":
                        album_artists = it['album_artist']
                his.write(rowid, date, time, name, artists, album, album_artists, original_item_id, itemId, play_duration, i['ItemName'], i['ClientName'], i['DeviceName'], i['PlaybackMethod'])  # noqa: E501
            offset += len(data)
            data = pdb.get_activitys(offset, itemType='Audio', userId=userId,
                                     startTime=startTime, endTime=endTime)
