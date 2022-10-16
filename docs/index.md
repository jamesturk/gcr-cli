# About gcr

`gcr` is a command-line toolkit for GitHub Classroom.

## Features

- Checkout latest versions of all student repositories for a given assignment.
- Run local commands within student repositories with option to view per-repository output or see in aggregate.
- Push post-assignment updates by copying local files into all student repositories at once with a single command.
- GitHub token based authentication.

## Installation

For now, download and run via `poetry`.

Will be `pip`/`pipx` installable once I have a chance to stabilize the API.

## Usage Examples

Configure `gcr` with your GitHub organization name, a local working directory, and your GitHub token.

```console
$ gcr configure
Working directory [~/gcr-workdir]:
GitHub organization: your-classroom
Visit https://github.com/settings/tokens/new and obtain a personal access token.
Be sure to select 'repo' scope!
GitHub token: ********
Successfully authenticated, wrote local config file!
```

Get a local check out all student repositories:

```console
$ gcr checkout homework2 --all
Cloning into 'homework2-edna-k'...
Cloning into 'homework2-liz-h'...
Cloning into 'homework2-seymour-s'...
Cloning into 'homework2-dewey-l'...
```

Copy a file into each local repository:
```console
$ gcr update-file homework2 fixed_README.md README.md
Copying fixed_README.md to:
    ~/gcr-workdir/homework2-edna-k/README.md
    ~/gcr-workdir/homework2-liz-h/README.md
    ~/gcr-workdir/homework2-seymour-s/README.md
    ~/gcr-workdir/homework2-dewey-l/README.md
```

Run a command in each local repository:
```
$ gcr run 'git commit -am "Fixed typo in README"' homework2
╭─────────────────────────── homework-2-edna-k ───────────────────────────╮
│ [main cd4186f] Fixed typo in README                                     │
│  1 files changed, 86 insertions(+), 1 deletion(-)                       │
╰─────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────── homework-2-liz-h ────────────────────────────╮
│ [main ab23460] Fixed typo in README                                     │
│  1 files changed, 86 insertions(+), 1 deletion(-)                       │
╰─────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────── homework-2-seymour-s ────────────────────────╮
│ [main 11bc922] Fixed typo in README                                     │
│  1 files changed, 86 insertions(+), 1 deletion(-)                       │
╰─────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────── homework-2-dewey-l ──────────────────────────╮
│ [main de52971] Fixed typo in README                                     │
│  1 files changed, 86 insertions(+), 1 deletion(-)                       │
╰─────────────────────────────────────────────────────────────────────────╯
```

Or run commands in aggregate to check results:
```
$ gcr check 'pytest problem1' homework2
Running 'pytest problem1'... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ student                      ┃ success ┃ time  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ homework-2-edna-k            │    ✓    │ 0.24s │
│ homework-2-liz-h             │    ✓    │ 0.25s │
│ homework-2-seymour-s         │    ✗    │ 0.29s │
│ homework-2-dewey-l           │    ✗    │ 0.21s │
└──────────────────────────────┴─────────┴───────┘
╭────────── Statistics ──────────╮
│ Command        pytest problem1 │
│ Total Passing                2 │
│ Total Failing                2 │
│ Min Time                 0.21s │
│ Max Time                 0.29s │
│ Average Time             0.25s │
╰────────────────────────────────╯
```

[typer](https://typer.tiangolo.com/)-powered help & completions:

```console
$ gcr --help

 Usage: gcr [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────────────────────────────╮
│ --install-completion        [bash|zsh|fish|powers  Install completion for │
│                             hell|pwsh]             the specified shell.   │
│                                                    [default: None]        │
│ --show-completion           [bash|zsh|fish|powers  Show completion for    │
│                             hell|pwsh]             the specified shell,   │
│                                                    to copy it or          │
│                                                    customize the          │
│                                                    installation.          │
│                                                    [default: None]        │
│ --help                                             Show this message and  │
│                                                    exit.                  │
╰───────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────╮
│ check        run a local command within each student repo and aggregate   │
│              output                                                       │
│ checkout     checkout student repositories                                │
│ configure    initial configuration                                        │
│ run          run a local command within each student repo                 │
│ show         view a file for each student repo                            │
│ update-file  update a file in each student repo                           │
╰───────────────────────────────────────────────────────────────────────────╯
```
