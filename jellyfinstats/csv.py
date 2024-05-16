from enum import Enum
from typing import IO, List


UTF8_BOM = b'\xef\xbb\xbf'


def escapeField(s: str) -> str:
    if s.find('\r\n') > -1 or s.find(',') > -1 or s.find('"') > -1:
        return '"' + s.replace('"', '""') + '"'
    else:
        return s


def readField(f: IO[str]) -> List[str]:
    t = f.readline()
    le = len(t)
    if le == 0:
        return None
    i = 0
    r = []
    s = ''
    e = False
    a = False
    while i < le:
        n = t[i]
        if n == '"' and s == '':
            e = True
        elif n == '"' and e:
            e = False
            a = True
        elif n == '"' and a:
            e = True
            a = False
            s += '"'
        elif not e and n == ',':
            r.append(s)
            s = ''
            a = False
        else:
            a = False
            s += n
        i += 1
        if e and i == le:
            t += f.readline()
            le = len(t)
    if s != '':
        r.append(s)
    if r[-1][-1] == '\n':
        r[-1] = r[-1][:-1]
    return r


def writeField(f: IO[bytes], *k):
    a = False
    for i in k:
        if a:
            f.write(b',')
        else:
            a = True
        if i is None:
            i = ''
        elif isinstance(i, bool):
            i = str(int(i))
        elif isinstance(i, Enum):
            i = str(i.value)
        elif not isinstance(i, str):
            i = str(i)
        f.write(escapeField(i).encode())
    f.write(b'\r\n')


class OpenMode(Enum):
    Read = 1
    Write = 2


class CSVFile:
    def __init__(self, path: str, mode: OpenMode = OpenMode.Write):
        mod = 'rb' if mode == OpenMode.Read else 'wb'
        self._mode = mode
        self._f = open(path, mod)
        if mode == OpenMode.Read:
            bom = self._f.read(3)
            if bom != UTF8_BOM:
                self._f.seek(0)
        else:
            self._f.write(UTF8_BOM)
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, tp, val, trace):
        self.close()

    def close(self):
        if self._closed:
            return
        self._f.close()
        self._closed = True

    def read(self):
        if self._mode != OpenMode.Read:
            raise ValueError("Stream is not readable")
        return readField(self._f)

    def write(self, *k):
        if self._mode != OpenMode.Write:
            raise ValueError("Stream is not writable")
        writeField(self._f, *k)
