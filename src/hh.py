#!/usr/bin/env python
import typer
import typing
import pathlib
import json
import subprocess

from github import Github
from dataclasses import dataclass, asdict
from getpass import getpass


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
            print("Could not authenticate for github.com/{org_name}")
            print(e)
            exit()


def load_config():
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: pathlib.Path = pathlib.Path(app_dir) / "config.json"
    if not config_path.is_file():
        print(f"Could not open {config_path}")
        exit()
    data = json.load(config_path.open())
    return Config(**data)


@app.command()
def checkout(
    assignment_name: str,
    student_name: typing.Optional[str] = typer.Argument(None),
    all: bool = False,
):
    config = load_config()
    org = config.github_org()
    if (not student_name and not all) or (student_name and all):
        print("must provide either student_name or explicitly pass --all")
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
def configure(reset: bool = False):
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: pathlib.Path = pathlib.Path(app_dir) / "config.json"
    if config_path.is_file() and not reset:
        print(f"{config_path} already exists, pass --reset to overwrite")
        exit()

    default_working_dir = "~/hh-workdir"
    working_dir = input(f"Working directory [{default_working_dir}]: ")
    if not working_dir:
        working_dir = default_working_dir
    org_name = input("GitHub organization: ")
    print(
        "Visit https://github.com/settings/tokens/new and obtain a personal access token."
    )
    print("   Be sure to select scope 'repo'")
    github_token = getpass("GitHub token: ")

    c = Config(org_name, working_dir, github_token)

    # test login before write
    c.github_org()

    json.dump(asdict(c), config_path.open("w"))
    print(f"Successfully configured, writing {config_path}")


if __name__ == "__main__":
    app()
