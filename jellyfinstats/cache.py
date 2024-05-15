from os import makedirs
from os.path import exists, join
from typing import Dict, Any
from yaml import dump as dumpyaml, load as loadyaml
try:
    from yaml import CSafeDumper as SafeDumper, CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeDumper, SafeLoader
from . import _


class IdRelativeCache:
    def __init__(self, output_dir: str):
        makedirs(output_dir, exist_ok=True)
        self._path = join(output_dir, 'id_relative_cache.yaml')
        self._data = {}
        if exists(self._path):
            try:
                with open(self._path, "r", encoding="UTF-8") as f:
                    data = loadyaml(f, SafeLoader)
                version = data['version']
                if version > 1:
                    t = _("Unsupported version: ")
                    raise NotImplementedError(f'{t}{version}')
                self._data = data['data']
            except Exception:
                from traceback import print_exc
                print_exc()
                print(_("Failed to load cache."))
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, tp, val, trace):
        self.close()

    def close(self):
        if self._closed:
            return
        with open(self._path, "w", encoding='UTF-8') as f:
            dumpyaml({'version': 1, 'data': self._data}, f, SafeDumper,
                     allow_unicode=True)
        self._closed = True

    def get(self, oldId: str):
        return self._data[oldId] if oldId in self._data else None

    def set(self, oldId: str, newId: str, data: Dict[str, Any]):
        self._data[oldId] = {k: data[k] for k in data}
        self._data[oldId]['id'] = newId

    def set_value(self, oldId: str, value):
        self._data[oldId] = value
