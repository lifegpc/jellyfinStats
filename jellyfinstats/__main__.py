from argparse import ArgumentParser
from os.path import join
from . import _
from .audio import prepare_audio_map, generate_audio_report
from .cache import IdRelativeCache
from .config import Config
from .db import PlaybackReportingDb, LibraryDb, JellyfinDb


p = ArgumentParser(prog="jellyfinstats")
p.add_argument("-c", "--config", help=_("The path to config file."), default="config.yaml")  # noqa: E501
p.add_argument("--playback-reporting-db", help=_("The path to playback_reporting.db"))  # noqa: E501
p.add_argument("--library-db", help=_("The path to library.db"))
p.add_argument("--jellyfin-data-dir", help=_("The path to jellyfin data directory."))  # noqa: E501
p.add_argument("--output-dir", help=_("The directory for output files."))
p.add_argument("--ask-page-size", help=_("Specify maximum items to display in one page."), type=int)  # noqa: E501
p.add_argument("--jellyfin-db", help=_("The path to jellyfin.db"))
arg = p.parse_intermixed_args()
cfg = Config(arg.config, arg)
with PlaybackReportingDb(cfg.playback_reporting_db) as pdb:
    with LibraryDb(cfg.library_db) as ldb:
        with IdRelativeCache(cfg.output_dir) as icache:
            with JellyfinDb(cfg.jellyfin_db) as jdb:
                re = prepare_audio_map(pdb, ldb, icache, cfg)
                users = pdb.get_users('Audio')
                for u in users:
                    userid = u['UserId']
                    user = jdb.get_user(userid)
                    username = user['Username'] if user else userid
                    output = join(cfg.output_dir, 'audio', username)
                    maxDate = u['MaxDate']
                    minDate = u['MinDate']
                    generate_audio_report(pdb, re[0], re[1], output, userid)
