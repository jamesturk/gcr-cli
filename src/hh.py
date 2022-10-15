#!/usr/bin/env python
import typer
import typing
import pathlib
import json
import subprocess

from github import Github
from dataclasses import dataclass, asdict
from getpass import getpass
from rich import print
from rich.text import Text


APP_NAME = "hh"

app = typer.Typer()


@dataclass
class Config:
    org_name: str
    working_dir: str
    github_token: str

    def working_path(self):
        path = pathlib.Path(self.working_dir).expanduser()
        if not path.exists():
            path.mkdir()
        return path

    def github_org(self):
        try:
            return Github(self.github_token).get_organization(self.org_name)
        except Exception as e:
            print(f"[red]Could not authenticate for github.com/{self.org_name}")
            print(e)
            exit()


def load_config():
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: pathlib.Path = pathlib.Path(app_dir) / "config.json"
    if not config_path.is_file():
        print(f"[red]Could not open '{config_path}', run '{APP_NAME} configure'")
        exit()
    data = json.load(config_path.open())
    return Config(**data)


def force_color(command: list[str]) -> list[str]:
    """a hack to work around subprocess.run losing color"""

    # special rules for git
    if command[0] == "git":
        return (
            command[:1]
            + [
                "-c",
                "color.ui=always",
                "-c",
                "color.diff=always",
                "-c",
                "color.status=always",
            ]
            + command[1:]
        )
    known_commands = {"pytest": "--color=yes"}
    colorize = known_commands.get(command[0])
    if colorize:
        return command + [colorize]
    return command


@app.command()
def checkout(
    assignment_name: str,
    student_name: typing.Optional[str] = typer.Argument(None),
    all: bool = False,
):
    """checkout student repositories"""
    config = load_config()
    org = config.github_org()
    if (not student_name and not all) or (student_name and all):
        print("[red]must provide either student_name or explicitly pass --all")
        exit()
    elif student_name:
        repos = [org.get_repo(assignment_name + "-" + student_name)]
    else:
        repos = [
            r for r in org.get_repos() if r.name.rsplit("-", 1)[0] == assignment_name
        ]

    for repo in repos:
        subprocess.run(["git", "clone", repo.ssh_url], cwd=config.working_path())


@app.command()
def run(
    command: str,
    assignment_name: str,
    student_name: typing.Optional[str] = typer.Argument(None),
    errors_only: bool = False,
    success_only: bool = False,
):
    """run a local command within each student repo"""
    config = load_config()
    path = config.working_path()
    if not student_name:
        dirs = path.glob(assignment_name + "-*")
    else:
        dirs = [path / (assignment_name + "-" + student_name)]

    # break apart command for subprocess
    command = command.split()
    capture_output = errors_only or success_only
    if capture_output:
        command = force_color(command)

    for match in dirs:
        if not capture_output:
            print(f"[bold white]{match.name}")

        result = subprocess.run(command, cwd=match, capture_output=capture_output)

        if (errors_only and result.returncode != 0) or (
            success_only and result.returncode == 0
        ):
            print(f"[bold white]{match.name}")
            print(Text.from_ansi(result.stdout.decode()))


@app.command()
def configure(reset: bool = False):
    """initial configuration"""
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: pathlib.Path = pathlib.Path(app_dir) / "config.json"
    if config_path.is_file() and not reset:
        print(f"[red]{config_path} already exists, pass --reset to overwrite")
        exit()

    default_working_dir = "~/hh-workdir"
    working_dir = typer.prompt(f"Working directory", default=default_working_dir)
    if not working_dir:
        working_dir = default_working_dir
    org_name = typer.prompt("GitHub organization")
    print(
        "Visit https://github.com/settings/tokens/new and obtain a personal access token."
    )
    print("[magenta]Be sure to select 'repo' scope!")
    github_token = getpass("GitHub token: ")

    c = Config(org_name, working_dir, github_token)

    # test login before write
    c.github_org()

    json.dump(asdict(c), config_path.open("w"))
    print(f"[green]Successfully configured, writing '{config_path}'")


if __name__ == "__main__":
    app()
