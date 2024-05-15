from gettext import bindtextdomain, gettext as _, textdomain  # noqa: F401
from os.path import join


try:
    bindtextdomain('jellyfinStats', join(__path__[0], 'language'))
    textdomain('jellyfinStats')
except Exception:
    from traceback import print_exc
    print_exc()
