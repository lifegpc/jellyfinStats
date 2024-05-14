from argparse import Namespace
try:
    from functools import cached_property
except ImportError:
    cached_property = property
from os.path import join
from yaml import load as loadyaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


class Config:
    def __init__(self, path: str, args: Namespace = None):
        with open(path, encoding="UTF-8") as f:
            self._data = loadyaml(f, Loader=SafeLoader)
        self._args = args

    @cached_property
    def playback_reporting_db(self) -> str:
        if self._args and self._args.playback_reporting_db:
            return self._args.playback_reporting_db
        if 'playback_reporting_db' in self._data and self._data['playback_reporting_db']:  # noqa: E501
            return self._data['playback_reporting_db']
        d = self.jellyfin_data_dir
        if d:
            return join(d, "playback_reporting.db")
        raise ValueError('playback_reporting.db not set.')

    @cached_property
    def library_db(self) -> str:
        if self._args and self._args.library_db:
            return self._args.library_db
        if 'library_db' in self._data and self._data['library_db']:
            return self._data['library_db']
        d = self.jellyfin_data_dir
        if d:
            return join(d, "library.db")
        raise ValueError('library.db not set.')

    @cached_property
    def jellyfin_data_dir(self) -> str | None:
        if self._args and self._args.jellyfin_data_dir:
            return self._args.jellyfin_data_dir
        if 'jellyfin_data_dir' in self._data and self._data['jellyfin_data_dir']:  # noqa: E501
            return self._data['jellyfin_data_dir']
