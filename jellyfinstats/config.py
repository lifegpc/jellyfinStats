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
from . import _


class Config:
    def __init__(self, path: str, args: Namespace = None):
        with open(path, encoding="UTF-8") as f:
            self._data = loadyaml(f, Loader=SafeLoader)
            if self._data is None:
                self._data = {}
        self._args = args

    @cached_property
    def ask_page_size(self) -> int:
        if self._args and self._args.ask_page_size is not None:
            return self._args.ask_page_size
        if 'ask_page_size' in self._data and isinstance(self._data['ask_page_size'], int):  # noqa: E501
            return self._data['ask_page_size']
        return 10

    @cached_property
    def playback_reporting_db(self) -> str:
        if self._args and self._args.playback_reporting_db:
            return self._args.playback_reporting_db
        if 'playback_reporting_db' in self._data and self._data['playback_reporting_db']:  # noqa: E501
            return self._data['playback_reporting_db']
        d = self.jellyfin_data_dir
        if d:
            return join(d, "playback_reporting.db")
        raise ValueError(_('%s not set.') % ('playback_reporting_db'))

    @cached_property
    def library_db(self) -> str:
        if self._args and self._args.library_db:
            return self._args.library_db
        if 'library_db' in self._data and self._data['library_db']:
            return self._data['library_db']
        d = self.jellyfin_data_dir
        if d:
            return join(d, "library.db")
        raise ValueError(_('%s not set.') % ('library_db'))

    @cached_property
    def jellyfin_data_dir(self) -> str | None:
        if self._args and self._args.jellyfin_data_dir:
            return self._args.jellyfin_data_dir
        if 'jellyfin_data_dir' in self._data and self._data['jellyfin_data_dir']:  # noqa: E501
            return self._data['jellyfin_data_dir']

    @cached_property
    def output_dir(self) -> str:
        if self._args and self._args.output_dir:
            return self._args.output_dir
        if 'output_dir' in self._data and self._data['output_dir']:
            return self._data['output_dir']
        return 'output'
