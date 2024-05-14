from argparse import ArgumentParser
from .audio import generate_audio_report
from .config import Config
from .db import PlaybackReportingDb, LibraryDb


p = ArgumentParser()
p.add_argument("-c", "--config", help="The path to config file.", default="config.yaml")  # noqa: E501
p.add_argument("--playback-reporting-db", help="The path to playback_reporting.db")  # noqa: E501
p.add_argument("--library-db", help="The path to library.db")
p.add_argument("--jellyfin-data-dir", help="The path to data directory.")
arg = p.parse_intermixed_args()
cfg = Config(arg.config, arg)
with PlaybackReportingDb(cfg.playback_reporting_db) as pdb:
    with LibraryDb(cfg.library_db) as ldb:
        generate_audio_report(pdb, ldb)
