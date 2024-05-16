import sqlite3
from .utils import convert_uid, format_time


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
                      itemType: str = None, userId: str = None,
                      startTime: float = None, endTime: float = None):
        where_sqls = []
        where_sql = ''
        args = []
        if itemType is not None:
            where_sqls.append('ItemType = ?')
            args.append(itemType)
        if userId is not None:
            where_sqls.append('UserId = ?')
            args.append(userId)
        if startTime is not None:
            where_sqls.append('DateCreated >= ?')
            args.append(format_time(startTime))
        if endTime is not None:
            where_sqls.append('DateCreated <= ?')
            args.append(format_time(endTime))
        if len(where_sqls):
            where_sql = ' WHERE ' + " AND ".join(where_sqls)
        args.append(limit)
        args.append(offset)
        cur = self._db.execute(f"SELECT ROWID, * FROM PlaybackActivity{where_sql} LIMIT ? OFFSET ?;", args)  # noqa: E501
        cur.row_factory = sqlite3.Row
        return [dict(i) for i in cur.fetchall()]

    def get_users(self, itemType: str = None):
        where_sql = ''
        args = []
        if itemType is not None:
            where_sql = ' WHERE ItemType = ?'
            args.append(itemType)
        cur = self._db.execute(f"SELECT UserId, min(DateCreated) AS MinDate, max(DateCreated) AS MaxDate FROM PlaybackActivity{where_sql} GROUP BY UserId;", args)  # noqa: E501
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

    def get_albums(self, album: str = None, albumArtists: str = None):
        args = ['MediaBrowser.Controller.Entities.Audio.MusicAlbum']
        where_sql = ''
        if album is not None:
            where_sql += ' AND Name = ?'
            args.append(album)
        if albumArtists is not None:
            where_sql += ' AND AlbumArtists = ?'
            args.append(albumArtists)
        cur = self._db.execute(f"SELECT * FROM TypedBaseItems WHERE type = ?{where_sql};", args)  # noqa: E501
        cur.row_factory = sqlite3.Row
        return [dict(i) for i in cur.fetchall()]


class JellyfinDb:
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

    def get_user(self, userId: str):
        if len(userId) == 32:
            userId = convert_uid(userId)
        cur = self._db.execute("SELECT * FROM Users WHERE Id = ?;", [userId])
        cur.row_factory = sqlite3.Row
        re = cur.fetchone()
        return dict(re) if re is not None else None
