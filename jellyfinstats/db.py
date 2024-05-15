import sqlite3


class PlaybackReportingDb:
    def __init__(self, fn: str):
        self._db = sqlite3.connect(fn)
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, tp, val, trace):
        self.close()

    def close(self):
        if self._closed:
            return
        self._db.close()
        self._closed = True

    def get_activitys(self, offset: int = 0, limit: int = 100,
                      itemType: str = None):
        where_sql = ''
        args = []
        if itemType is not None:
            where_sql = ' WHERE ItemType = ?'
            args.append(itemType)
        args.append(limit)
        args.append(offset)
        cur = self._db.execute(f"SELECT * FROM PlaybackActivity{where_sql} LIMIT ? OFFSET ?;", args)  # noqa: E501
        cur.row_factory = sqlite3.Row
        return [dict(i) for i in cur.fetchall()]


class LibraryDb:
    def __init__(self, fn: str):
        self._db = sqlite3.connect(fn)
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, tp, val, trace):
        self.close()

    def close(self):
        if self._closed:
            return
        self._db.close()
        self._closed = True

    def get_items(self, offset: int = 0, limit: int = 100):
        cur = self._db.execute("SELECT * FROM TypedBaseItems LIMIT ? OFFSET ?;", [limit, offset])  # noqa: E501
        cur.row_factory = sqlite3.Row
        return [dict(i) for i in cur.fetchall()]

    def get_item(self, itemId: str):
        cur = self._db.execute("SELECT * FROM TypedBaseItems WHERE PresentationUniqueKey = ?;", [itemId])  # noqa: E501
        cur.row_factory = sqlite3.Row
        re = cur.fetchone()
        return dict(re) if re is not None else None

    def get_audios(self, track: str = None, album: str = None):
        args = ['MediaBrowser.Controller.Entities.Audio.Audio']
        where_sql = ''
        if track is not None:
            where_sql += ' AND Name = ?'
            args.append(track)
        if album is not None:
            where_sql += ' AND Album = ?'
            args.append(album)
        cur = self._db.execute(f"SELECT * FROM TypedBaseItems WHERE type = ?{where_sql};", args)  # noqa: E501
        cur.row_factory = sqlite3.Row
        return [dict(i) for i in cur.fetchall()]
