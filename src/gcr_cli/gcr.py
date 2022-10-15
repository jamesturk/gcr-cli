#!/usr/bin/env python
import typer
import typing
import pathlib
import json
import subprocess

from github import Github
from dataclasses import dataclass, asdict
from rich import print
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax


APP_NAME = "gcr"

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


def _get_local_dirs(assignment_name: str, student_name: typing.Optional[str]):
    config = load_config()
    path = config.working_path()
    if not student_name:
        dirs = path.glob(assignment_name + "-*")
    else:
        dirs = [path / (assignment_name + "-" + student_name)]
    return dirs


def _force_color(command: list[str]) -> list[str]:
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
    wait: bool = False,
):
    """run a local command within each student repo"""
    dirs = _get_local_dirs(assignment_name, student_name)

    # break apart command for subprocess
    command = command.split()
    # TODO: consider disabling capture_output via flag (to avoid color loss)
    capture_output = True
    if capture_output:
        command = _force_color(command)

    for match in dirs:
        if not capture_output:
            print(f"[bold white]{match.name}")

        result = subprocess.run(command, cwd=match, capture_output=True)

        if (errors_only and result.returncode != 0) or (
            success_only
            and result.returncode == 0
            or (not success_only and not errors_only)
        ):
            print(
                Panel(
                    Text.from_ansi(result.stderr.decode())
                    + Text.from_ansi(result.stdout.decode()),
                    title=f"[bold white]{match.name}",
                    subtitle="press <Enter> to continue" if wait else "",
                )
            )
            if wait:
                typer.prompt("", show_default=False, default="y", prompt_suffix="")


@app.command()
def show(
    filename: str,
    assignment_name: str,
    student_name: typing.Optional[str] = typer.Argument(None),
    wait: bool = False,
):
    """view a file for each student repo"""
    dirs = _get_local_dirs(assignment_name, student_name)
    for path in dirs:
        print(
            Panel(
                Syntax.from_path(path / filename),
                title=f"[bold white]{path.name}/{filename}",
                subtitle="press <Enter> to continue" if wait else "",
            )
        )
        if wait:
            typer.prompt("", show_default=False, default="y", prompt_suffix="")


@app.command()
def configure(reset: bool = False):
    """initial configuration"""
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: pathlib.Path = pathlib.Path(app_dir) / "config.json"
    if config_path.is_file() and not reset:
        print(f"[red]{config_path} already exists, pass --reset to overwrite")
        exit()

    default_working_dir = f"~/{APP_NAME}-workdir"
    working_dir = typer.prompt("Working directory", default=default_working_dir)
    if not working_dir:
        working_dir = default_working_dir
    org_name = typer.prompt("GitHub organization")
    print(
        "Visit https://github.com/settings/tokens/new and obtain a personal access token."
    )
    print("[magenta]Be sure to select 'repo' scope!")
    github_token = typer.prompt("GitHub token", hide_input=True)

    c = Config(org_name, working_dir, github_token)

    # test login before write
    c.github_org()

    json.dump(asdict(c), config_path.open("w"))
    print(f"[green]Successfully configured, writing '{config_path}'")


if __name__ == "__main__":
    app()
