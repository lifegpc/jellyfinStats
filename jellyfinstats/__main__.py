from argparse import ArgumentParser
from . import _
from .audio import generate_audio_report
from .cache import IdRelativeCache
from .config import Config
from .db import PlaybackReportingDb, LibraryDb


p = ArgumentParser(prog="jellyfinstats")
p.add_argument("-c", "--config", help=_("The path to config file."), default="config.yaml")  # noqa: E501
p.add_argument("--playback-reporting-db", help=_("The path to playback_reporting.db"))  # noqa: E501
p.add_argument("--library-db", help=_("The path to library.db"))
p.add_argument("--jellyfin-data-dir", help=_("The path to jellyfin data directory."))  # noqa: E501
p.add_argument("--output-dir", help=_("The directory for output files."))
p.add_argument("--ask-page-size", help=_("Specify maximum items to display in one page."), type=int)  # noqa: E501
arg = p.parse_intermixed_args()
cfg = Config(arg.config, arg)
with PlaybackReportingDb(cfg.playback_reporting_db) as pdb:
    with LibraryDb(cfg.library_db) as ldb:
        with IdRelativeCache(cfg.output_dir) as icache:
            generate_audio_report(pdb, ldb, icache, cfg)
