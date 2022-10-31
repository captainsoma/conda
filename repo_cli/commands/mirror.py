"""
Manage your Anaconda repository channels.
"""

from __future__ import print_function, unicode_literals

import argparse

from .. import errors
from ..utils.format import (
    AllMirrorFormatter,
    MirrorFormatter,
    SyncStateFormatter,
    comma_string_to_list,
)
from ..utils.validators import (
    check_cve_score,
    check_date_format,
    check_proxy_url,
    check_url,
)
from .base import SubCommandBase

DEFAULT_MIRROR_CRON = "0 0 * * *"


class SubCommand(SubCommandBase):
    name = "mirror"

    def main(self):
        self.log.info("")
        args = self.args
        if (
            args.create or args.update or args.delete or args.show
        ) and not args.channel:
            msg = (
                "Channel name not specified. Please use -c or --channel to specify your channel.\n"
                "Use --help for help."
            )
            self.log.info(msg)
            raise errors.RepoCLIError(msg)
        if args.create:
            self.create_mirror(
                args.channel,
                args.source,
                args.create,
                args.mode,
                args.type,
                args.licenses,
                args.subdirs,
                args.projects,
                args.only_spec,
                args.exclude_spec,
                args.include_spec,
                args.cve_score,
                args.exclude_uncurated_cve_packages,
                args.date_from,
                args.date_to,
                args.cron,
                args.run_now,
                args.proxy,
            )
        elif args.update:
            self.update_mirror(
                args.channel,
                args.source,
                args.update,
                args.name,
                args.mode,
                args.type,
                args.licenses,
                args.subdirs,
                args.projects,
                args.only_spec,
                args.exclude_spec,
                args.include_spec,
                args.cve_score,
                args.exclude_uncurated_cve_packages,
                args.date_from,
                args.date_to,
                args.cron,
                args.run_now,
                args.proxy,
            )
        elif args.delete:
            self.delete(args.channel, args.delete)
        elif args.list:
            self.show_list(args.list)
        elif args.list_all:
            self.show_all_list()
        elif args.sync_state:
            self.sync_state(args.sync_state)
        elif args.show:
            self.show(args.channel, args.show)
        else:
            raise NotImplementedError()

    # flake8: noqa: C901
    def create_mirror(
        self,
        channel,
        source,
        name,
        mode,
        type_,
        filter_licenses,
        filter_subdirs,
        filter_projects,
        filter_only_specs,
        filter_exclude_specs,
        filter_include_specs,
        cve_score,
        exclude_uncurrated_cve_packages,
        filter_date_from,
        filter_date_to,
        cron,
        run_now,
        proxy,
    ):
        filters = {}
        if filter_subdirs:
            filters["subdirs"] = comma_string_to_list(filter_subdirs)
        if filter_projects:
            filters["projects"] = comma_string_to_list(filter_projects)
        if filter_licenses:
            filters["include_licenses"] = []
            filters["exclude_licenses"] = []
            for license in comma_string_to_list(filter_licenses):
                group = "include_licenses"
                if license.startswith("-"):
                    group = "exclude_licenses"
                    license = license[1:]
                if license.startswith("+"):
                    license = license[1:]
                filters[group].append(license)
        if filter_only_specs:
            filters["only_specs"] = filter_only_specs
        if filter_exclude_specs:
            filters["exclude_specs"] = filter_exclude_specs
        if filter_include_specs:
            filters["include_specs"] = filter_include_specs
        if filter_date_from:
            filters["date_from"] = filter_date_from
        if filter_date_to:
            filters["date_to"] = filter_date_to
        if cve_score is not None:
            filters["cve_score_threshold"] = cve_score
        if exclude_uncurrated_cve_packages:
            filters["exclude_non_curated_cve"] = exclude_uncurrated_cve_packages

        self.validate_mirror_filters(filters)

        self.api.create_mirror(
            channel, source, name, mode, filters, type_, cron, run_now, proxy
        )
        self.log.info("Mirror %s successfully created on channel %s", name, channel)

    def update_mirror(
        self,
        channel,
        source,
        name,
        new_name,
        mode,
        type_,
        filter_licenses,
        filter_subdirs,
        filter_projects,
        filter_only_specs,
        filter_exclude_specs,
        filter_include_specs,
        cve_score,
        exclude_uncurrated_cve_packages,
        filter_date_from,
        filter_date_to,
        cron,
        run_now,
        proxy,
    ):
        mirror = self._get_by_name(channel, name)
        if not mirror:
            self.log.info("Mirror not found")
            return

        filters = mirror["filters"]

        if filter_subdirs is not None:
            filters["subdirs"] = comma_string_to_list(filter_subdirs)
        if filter_projects is not None:
            filters["projects"] = comma_string_to_list(filter_projects)
        if filter_licenses is not None:
            filters["include_licenses"] = []
            filters["exclude_licenses"] = []
            for license in comma_string_to_list(filter_licenses):
                group = "include_licenses"
                if license.startswith("-"):
                    group = "exclude_licenses"
                    license = license[1:]
                if license.startswith("+"):
                    license = license[1:]
                filters[group].append(license)
        if filter_only_specs is not None:
            filters["only_specs"] = filter_only_specs
        if filter_exclude_specs is not None:
            filters["exclude_specs"] = filter_exclude_specs
        if filter_include_specs is not None:
            filters["include_specs"] = filter_include_specs
        if filter_date_from is not None:
            filters["date_from"] = filter_date_from
        if filter_date_to is not None:
            filters["date_to"] = filter_date_to
        if cve_score is not None:
            filters["cve_score_threshold"] = cve_score
        if exclude_uncurrated_cve_packages is not None:
            filters["exclude_non_curated_cve"] = exclude_uncurrated_cve_packages

        self.validate_mirror_filters(filters)

        if source:
            mirror["source_root"] = source

        if new_name:
            mirror["mirror_name"] = new_name

        if proxy is not None:
            mirror["proxy"] = proxy if proxy else None

        if cron is not None and cron != DEFAULT_MIRROR_CRON:
            mirror["cron"] = cron

        self.api.update_mirror(
            mirror["mirror_id"],
            channel,
            mirror["source_root"],
            mirror["mirror_name"],
            mirror["mirror_mode"],
            filters,
            mirror["mirror_type"],
            mirror["cron"],
            run_now,
            mirror["proxy"],
        )
        self.log.info("Mirror %s successfully update on channel %s", name, channel)

    def validate_mirror_filters(self, filters):
        if filters.get("only_specs") and (
            filters.get("exclude_specs") or filters.get("include_specs")
        ):
            raise errors.RepoCLIError(
                "Can't combine only_specs with exclude_specs and include_specs"
            )

    def show_list(self, channel):
        data = self.api.get_mirrors(channel)
        self.log.info(MirrorFormatter.format_list(data["items"]))
        self.log.info("")

    def show_all_list(self):
        data = self.api.get_all_mirrors()
        self.log.info(AllMirrorFormatter.format_list_all(data["items"]))
        self.log.info("")

    def sync_state(self, mirror):
        data = self.api.get_all_mirrors()
        self.log.info(SyncStateFormatter.format_sync_state(data["items"], mirror))
        self.log.info("")

    def show(self, channel, name):
        # TODO: Get mirror api is currently unavailable so we need to use the
        #       GET mirrors api and filter by name...
        # data = self.api.get_mirror(channel, name)

        mirror = self._get_by_name(channel, name)
        if mirror:
            self.log.info(MirrorFormatter.format_detail(mirror))
            self.log.info("")
        else:
            self.log.info("Mirror not found")

    def delete(self, channel, name):
        mirror = self._get_by_name(channel, name)
        if not mirror:
            self.log.info("Mirror not found")
            return
        self.api.delete_mirror(channel, mirror["mirror_id"], name)
        self.log.info("Mirror %s successfully delete on channel %s", name, channel)

    def _get_by_name(self, channel, name):
        data = self.api.get_mirrors(channel)
        for mirror in data["items"]:
            if mirror["mirror_name"] == name:
                return mirror

    def add_parser(self, subparsers):
        subparser = subparsers.add_parser(
            self.name,
            help="Manage your Anaconda repository {}s".format(self.name),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=__doc__,
        )

        subparser.add_argument("--channel", "-c", help="Channel to mirror to.")
        group = subparser.add_mutually_exclusive_group(required=True)

        # group.add_argument('--create', nargs=2, metavar=self.name.upper())
        group.add_argument(
            "--create",
            metavar=self.name.upper(),
            help="Create a new {}".format(self.name),
        )
        group.add_argument(
            "--update", metavar=self.name.upper(), help="Update a {}".format(self.name)
        )
        group.add_argument(
            "--delete", metavar=self.name.upper(), help="Delete a {}".format(self.name)
        )
        group.add_argument(
            "--list",
            "-l",
            metavar=self.name.upper(),
            help="list all {}s for a user".format(self.name),
        )
        group.add_argument(
            "--show",
            metavar=self.name.upper(),
            help="Show all of the files in a {}".format(self.name),
        )

        group.add_argument("--list-all", action="store_true", help="list all mirrors")

        group.add_argument("--sync-state", help="show sync state of mirror")

        subparser.add_argument(
            "--source",
            "-s",
            type=check_url,
            help="Path to the source channel to mirror. "
            "I.e.: https://conda.anaconda.org/conda-test",
        )
        subparser.add_argument("--name", "-n", help="Name of the mirror")
        subparser.add_argument(
            "--mode",
            default="passive",
            help='Mirror mode. If "active", will download all the files from the source channel '
            'immediately else, if "passive", download JSON immediately and files on demand '
            'later. Default is "passive"',
        )
        subparser.add_argument(
            "--type",
            default="conda",
            help='Mirror type. Possible types: "conda", "python_simple" and "CRAN"',
        )
        subparser.add_argument(
            "--cron",
            default=DEFAULT_MIRROR_CRON,
            help="Cron string to configure the mirror job.",
        )
        subparser.add_argument(
            "--proxy",
            default=None,
            type=check_proxy_url,
            help='Proxy to use for the mirroring in format "http://<PROXYURL>" or "http://<USER>:<PASS>@<PROXYURL>"',
        )

        filters_group = subparser.add_argument_group(
            "mirror filters",
            description="Filters are used to filter specific subset of packages from the original "
            "index. Some filters are specific to artifact family.",
        )
        filters_group.add_argument(
            "--subdirs",
            default=None,
            help="[conda] List of conda subdirs, I.e.: linux-64, osx-64, linux-32, etc. "
            "Use comma-separated string.",
        )
        filters_group.add_argument(
            "--projects",
            default=None,
            help="[python] List of pypi projects to mirror. Use comma-separated string.",
        )
        filters_group.add_argument(
            "--licenses",
            default=None,
            help='List of licenses to filter for. Use comma-separated string, prepent with "-" to exclude, '
            "or just a license to include. The allowed license values are: agpl, gpl2, gpl3, lgpl, "
            "bsd, mit, apache, psf, public_domain, proprietary, other, none",
        )
        filters_group.add_argument(
            "--only_spec",
            action="append",
            default=None,
            help="MatchSpec to only spec. Use multiple times the option for multiple entries",
        )
        filters_group.add_argument(
            "--exclude_spec",
            action="append",
            default=None,
            help="MatchSpec to exclude. Use multiple times the option for multiple entries",
        )
        filters_group.add_argument(
            "--include_spec",
            action="append",
            default=None,
            help="MatchSpec to include. Use multiple times the option for multiple entries",
        )
        filters_group.add_argument(
            "--cve_score",
            type=check_cve_score,
            default=None,
            help="Only mirror files with CVE score less or equal to this value. I.e.: 9.5",
        )
        filters_group.add_argument(
            "--exclude_uncurated_cve_packages",
            default=None,
            action="store_true",
            help="Only mirror files with CVE score less or equal to this value. I.e.: 9.5",
        )
        filters_group.add_argument(
            "--date_from",
            type=check_date_format,
            default=None,
            help="[conad] bottom date YYYY-mm-dd when package was published",
        )
        filters_group.add_argument(
            "--date_to",
            type=check_date_format,
            default=None,
            help="[conad] upper date YYYY-mm-dd when package was published",
        )

        subparser.add_argument(
            "--run_now",
            action="store_true",
            help="Determines whether the mirror job should run immediately or "
            "according to the cron schedule",
        )

        subparser.set_defaults(main=self.main)
