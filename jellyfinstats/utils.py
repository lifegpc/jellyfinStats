from math import ceil
from . import _
from .config import Config


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
