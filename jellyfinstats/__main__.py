from argparse import ArgumentParser
from os.path import join
from . import _
from .audio import (
    prepare_audio_map,
    generate_audio_report,
    fix_audio_report_library,
)
from .cache import IdRelativeCache
from .config import Config
from .db import PlaybackReportingDb, LibraryDb, JellyfinDb
from .utils import gen_year_range, parse_datetime


p = ArgumentParser(prog="jellyfinstats")
p.add_argument("-c", "--config", help=_("The path to config file."), default="config.yaml")  # noqa: E501
p.add_argument("--playback-reporting-db", help=_("The path to playback_reporting.db"))  # noqa: E501
p.add_argument("--library-db", help=_("The path to library.db"))
p.add_argument("--jellyfin-data-dir", help=_("The path to jellyfin data directory."))  # noqa: E501
p.add_argument("--output-dir", help=_("The directory for output files."))
p.add_argument("--ask-page-size", help=_("Specify maximum items to display in one page."), type=int)  # noqa: E501
p.add_argument("--jellyfin-db", help=_("The path to jellyfin.db"))
ps = p.add_subparsers(dest='action', help=_('sub-command help'), required=False, metavar='action')  # noqa: E501
audio = ps.add_parser('audio', help=_('Generate audio report.'))
audio.add_argument("--fix", help=_("Fix incorrect play duration."), action='store_true', default=False)  # noqa: E501
audio.add_argument("-u", "--user", help=_("Generate report for specify users."), action='append', default=[])  # noqa: E501
audio.add_argument("-i", "--user-id", help=_("Generate report for specify users."), action='append', default=[])  # noqa: E501
audios = audio.add_subparsers(dest='type', help=_("Report type. Default: ") + "all", required=False, metavar='type')  # noqa: E501
audio_all = audios.add_parser('all', help=_("All time report"))
audio_year = audios.add_parser('year', help=_("Year report"))
audio_year.add_argument('year', action='extend', nargs='*', help=_("Generate year report for specify years."), default=[], type=int)  # noqa: E501
audio_year.add_argument('-s', '--start', help=_("The start year of range of years."), type=int)  # noqa: E501
audio_year.add_argument('-e', '--end', help=_("The end year of range of years."), type=int)  # noqa: E501
audio_year.add_argument('--utc', action='store_true', help=_("Use UTC time."), default=False)  # noqa: E501
arg = p.parse_args()
if arg.action == 'a':
    arg.action = 'audio'
cfg = Config(arg.config, arg)
with PlaybackReportingDb(cfg.playback_reporting_db) as pdb:
    if arg.action == 'audio' and arg.fix:
        fix_audio_report_library(pdb)
    with LibraryDb(cfg.library_db) as ldb:
        with IdRelativeCache(cfg.output_dir) as icache:
            with JellyfinDb(cfg.jellyfin_db) as jdb:
                if arg.action == 'audio':
                    if arg.type is None:
                        arg.type = 'all'
                    re = prepare_audio_map(pdb, ldb, icache, cfg)
                    users = pdb.get_users('Audio')
                    for u in users:
                        userid = u['UserId']
                        user = jdb.get_user(userid)
                        username = user['Username'] if user else userid
                        if arg.user or arg.user_id:
                            if username not in arg.user and userid not in arg.user_id:  # noqa: E501
                                continue
                        output = join(cfg.output_dir, 'audio', username)
                        maxDate = u['MaxDate']
                        minDate = u['MinDate']
                        if arg.type == 'all':
                            generate_audio_report(
                                pdb, re[0], re[1], re[2], output, userid)
                        elif arg.type == 'year':
                            minTime = parse_datetime(minDate)
                            minYear = minTime.year
                            maxTime = parse_datetime(maxDate)
                            maxYear = maxTime.year
                            for year in range(minYear, maxYear + 1):
                                if arg.year and year not in arg.year:
                                    continue
                                if arg.start is not None and year < arg.start:
                                    continue
                                if arg.end is not None and year > arg.end:
                                    continue
                                time = gen_year_range(year, arg.utc)
                                toutput = join(output, str(year))
                                generate_audio_report(pdb, re[0], re[1], re[2], toutput, userid, max(time[0], minTime.timestamp()), min(time[1], maxTime.timestamp()))  # noqa: E501
