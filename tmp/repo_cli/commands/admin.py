"""
Manage your Anaconda Server server-side settings

###### Set server-side settings

You can add a site named **site_name** like this:

    conda repo admin --set SETTING_NAME SETTING_VALUE

Currently supported settings are:

    - `user_channel_autocreate` - if True, a user's channel is created automatically on first login

###### Show server-side settings

Yuo can see current settings:

    conda repo admin --show
"""
import logging
from argparse import RawDescriptionHelpFormatter

from .. import errors
from ..utils.format import SettingsFormatter
from ..utils.yaml import safe_load
from .base import SubCommandBase

logger = logging.getLogger("repo_cli")


SETTINGS_VALIDATOR = {"user_channel_autocreate": safe_load}


class SubCommand(SubCommandBase):
    name = "admin"

    def main(self):

        if self.args.show:
            self.show_settings()
            return

        if self.args.get:
            self.show_settings(self.args.get)
            return

        if self.args.set:
            self.update_settings(self.args.set)
            return

        raise NotImplementedError("Please use command options")

    def show_settings(self, key=None):
        settings = self.api.get_system_settings()
        if key is not None:
            if key not in settings:
                raise errors.RepoCLIError("%s is an unknown admin setting" % key)
            settings = {key: settings[key]}

        self.log.info(SettingsFormatter.format_object_as_list(settings))

    def update_settings(self, args):
        data = {}
        for key, value in args:
            if key not in SETTINGS_VALIDATOR:
                raise errors.RepoCLIError("%s is an unknown admin setting" % key)
            data[key] = SETTINGS_VALIDATOR[key](value)

        settings = self.api.get_system_settings()
        settings.update(data)
        self.api.update_system_settings(settings)

        self.log.info("Anaconda Server settings are updated")

    def add_parser(self, subparsers):
        description = "Anaconda Server admin settings"
        parser = subparsers.add_parser(
            "admin",
            help=description,
            description=description,
            epilog=__doc__,
            formatter_class=RawDescriptionHelpFormatter,
        )

        agroup = parser.add_argument_group("actions")

        agroup.add_argument(
            "--set",
            nargs=2,
            action="append",
            default=[],
            help="sets a server setting value: name value",
            metavar=("name", "value"),
        )
        agroup.add_argument("--get", metavar="name", help="get value: name")
        agroup.add_argument(
            "--show", action="store_true", default=False, help="show all variables"
        )

        parser.set_defaults(main=self.main, sub_parser=parser)