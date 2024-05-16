from math import ceil, floor
from datetime import datetime, timezone
from re import compile
from . import _
from .config import Config


DATETIME_RE = compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}).(\d{0,6})')  # noqa: E501


def ask_choice(cfg: Config, choices: list, prompt=_("Please choose: "),
               fn=None, extra=None):
    if extra:
        for n in extra:
            if n[0] in ['f', 'p', 'n', 'l']:
                raise ValueError(f'Internal action used: {n[0]}')
    page_size = cfg.ask_page_size
    if page_size <= 0:
        page_size = 10
    count = len(choices)
    total_pages = ceil(count / page_size)
    page = 1

    def show_page():
        nonlocal page
        base = (page - 1) * page_size
        if total_pages > 1:
            print(_("Page %i/%i") % (page, total_pages))
        for i in range(page_size):
            index = base + i
            if index >= count:
                break
            s = fn(choices[index]) if fn else choices[index]
            print(f"{i}. {s}")
        if page > 1:
            fp = _("First page")
            print(f'f. {fp}')
            pp = _("Previous page")
            print(f'p. {pp}')
        if page < total_pages:
            np = _("Next page")
            print(f'n. {np}')
            lp = _("Last page")
            print(f'l. {lp}')
        if extra is not None:
            for t in extra:
                print(f"{t[0]}. {t[1]}")

    while True:
        show_page()
        s = input(prompt)
        if s == "f":
            page = 1
        elif s == "p":
            page = max(1, page - 1)
        elif s == "n":
            page = min(total_pages, page + 1)
        elif s == "l":
            page = total_pages
        else:
            if extra is not None:
                for t in extra:
                    if t[0] == s:
                        return t[2]
            try:
                index = int(s)
            except Exception:
                continue
            base = (page - 1) * page_size
            index += base
            if index < 0 or index >= count:
                continue
            return choices[index]


def format_time(time: float | None = None, tz=timezone.utc) -> str:
    d = datetime.fromtimestamp(time, tz=tz)
    return d.strftime('%Y-%m-%d %H:%M:%S.%f')


def parse_time(time: str) -> float:
    re = DATETIME_RE.match(time)
    t = datetime(int(re[1]), int(re[2]), int(re[3]), int(re[4]), int(re[5]), int(re[6]), int(re[7].ljust(6, '0')), timezone.utc)  # noqa: E501
    return t.timestamp()


def convert_uid(uid: str) -> str:
    t = uid.upper()
    return f"{t[:8]}-{t[8:12]}-{t[12:16]}-{t[16:20]}-{t[20:]}"


def format_duration(duration: float | None) -> str:
    if duration is None:
        return ''
    duration = round(duration)
    re = ''
    if duration >= 86400:
        re += _("%i day") % (floor(duration / 86400)) + " "
        duration %= 86400
    if duration >= 3600:
        re += str(floor(duration / 3600)).rjust(2, "0") + ":"
        duration %= 3600
    min = str(floor(duration / 60)).rjust(2, "0")
    sec = str(duration % 60).rjust(2, "0")
    return f"{re}{min}:{sec}"
