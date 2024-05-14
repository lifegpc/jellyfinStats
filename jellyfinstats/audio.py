from .db import PlaybackReportingDb, LibraryDb
from re import compile


ITEMNAME_PATTERN = compile(r'(?P<album_artist>.*) - (?P<track>.*) \((?P<album>.*)\)')  # noqa: E501


def generate_audio_report(pdb: PlaybackReportingDb, ldb: LibraryDb):
    offset = 0
    data = pdb.get_activitys(offset, itemType='Audio')
    count = 0
    while len(data) > 0:
        for d in data:
            itemId = d['ItemId']
            item = ldb.get_item(itemId)
            if item:
                pass
            else:
                itemName = d['ItemName']
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
                    pass
                else:
                    if len(items):
                        print(items)
                    else:
                        print(re)
                    count += 1
        offset += len(data)
        data = pdb.get_activitys(offset, itemType='Audio')
    print('Count', count)
