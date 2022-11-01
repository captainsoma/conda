import conda.plugins

from repo_cli import commands
from repo_cli._version import get_versions
from repo_cli.commands.base import RepoCommand

def repo_plugin(argv: list):
    main_cmd = RepoCommand(commands, argv, get_versions())
    main_cmd.run()



@conda.plugins.register
def conda_subcommands():
    yield conda.plugins.CondaSubcommand(
        name="repo",
        summary="A subcommand that accesses Anaconda Server",
        action=repo_plugin,
        )
