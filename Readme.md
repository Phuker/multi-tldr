# multi-tldr

Yet another python client for [tldr-pages/tldr](https://github.com/tldr-pages/tldr). View tldr pages in multi repo, multi platform, any language at the same time.

Forked from [lord63/tldr.py](https://github.com/lord63/tldr.py), whose original idea is very good. Modified a large proportion of code.

## Intro

Instead of the long man pages, tldr will give you several simple yet powerful examples:

![multi-tldr tar command](screenshots/screenshot1.png)

The command examples are not good? The tldr pages are just [simplified markdown files](https://github.com/tldr-pages/tldr/blob/master/contributing-guides/style-guide.md). You can easily contribute to [tldr-pages/tldr](https://github.com/tldr-pages/tldr), or create your own repo and keep your pages private.

One more thing, `tldr` is just a simple version for the man page, it's **NOT** an alternative. Sometimes, you should read the man pages patiently.

## Features

- No internet requests when lookup a tldr page, it is always fast.
- tldr pages are managed by `git`, and updated manually by `tldr --update`.
- Support display tldr pages in multi repo, multi platform, any language at the same time. You can create your own private tldr pages repo, add all dirs you want to the config file, whose path specified to the language level, e.g. `/path/to/pages/` or `/path/to/pages.xx/`.
- Support custom output style, including color, compact output (not output empty lines).

![multi-tldr custom output style](screenshots/screenshot2.png)

### Other differences with `lord63/tldr.py`

- No need to use `tldr find some_command` or create an alias of `tldr find`, just type `tldr some_command` ([related issue](https://github.com/lord63/tldr.py/issues/47))
- No need to rebuild `index.json` index file.
- Advanced parser: render nested `` ` `` inline code, `{{` and `}}` arguments ([related issue](https://github.com/lord63/tldr.py/issues/25)).
- Config file format `YAML` --> `JSON`, because I hate `YAML`.
- Drop support for Python 2.
- Simplify (just delete) tests code

## Requirements

- Python >= `3.6`, with `pip` installed

### Recommend

- Git: if you do not have `git`, you can still download `.zip` file from [tldr-pages/tldr](https://github.com/tldr-pages/tldr), extract it, and add it when run `tldr --init`, most things still work, but `tldr --update` will NOT work.

### For Windows users

A better terminal is recommended, which must support [ANSI escape sequences](https://en.wikipedia.org/wiki/ANSI_escape_code), and make sure `git` command is available. You may try and/or combine these: [Cmder](https://cmder.net/), [Cygwin](https://www.cygwin.com/), [Windows Terminal](https://github.com/microsoft/terminal), [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10), [Git for Windows](https://gitforwindows.org/), [scoop](https://github.com/lukesampson/scoop), [Chocolatey](https://chocolatey.org/), etc.

Test your environment with Python 3:

```python
#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import shutil

print(f'sys.stdout.isatty() -> {sys.stdout.isatty()}')
print(f'env TERM = {os.environ.get("TERM")!r}')
print('Test ANSI escape sequences: \x1b[31mred \x1b[1mbold\x1b[0m')
print(f'git command is: {shutil.which("git")!r}')
```

If you are using Windows 10, you can import this to the Windows Registry to enable [ANSI escape sequences](https://en.wikipedia.org/wiki/ANSI_escape_code) of `cmd` and `PowerShell` to enable colord output ([related discussions](https://superuser.com/questions/413073/windows-console-with-ansi-colors-handling)):

```registry
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Console]
"VirtualTerminalLevel"=dword:00000001
```

If output is not colored, try set `color_output` in the config file to `always`.

## Install

First, uninstall any other existing tldr client.

Then, use `pip` to install:

```bash
python3 -m pip install -U multi-tldr
```

## Initialize manually

This program won't work out of the box, first you need to initialize it manually.

### Clone [tldr-pages/tldr](https://github.com/tldr-pages/tldr)

`cd` to some directory (e.g. `~/code/tldr`) and clone the [tldr-pages/tldr](https://github.com/tldr-pages/tldr) repo. We will use it when we look up a command usage.

```bash
git clone --depth=1 https://github.com/tldr-pages/tldr.git
```

### Create config file

Then, run this command to interactively generate configuration file:

```bash
tldr --init
```

The default location for the config file is `~/.config/multi-tldr/tldr.config.json`. You can use `TLDR_CONFIG_DIR` and `XDG_CONFIG_HOME` environment variable to point it to another path. If `TLDR_CONFIG_DIR` is `/a/b/c`, config file is `/a/b/c/tldr.config.json`. If `XDG_CONFIG_HOME` is `/a/b/c`, config file is `/a/b/c/multi-tldr/tldr.config.json`.

Your configuration file should look like this:

```json
{
    "repo_directory_list": [
        "/home/user/code/tldr/pages/",
        "/home/user/code/tldr-private/pages.zh"
    ],
    "color_output": "auto",
    "colors": {
        "description": "bright_yellow",
        "usage": "green",
        "command": "white",
        "param": "cyan"
    },
    "platform_list": [
        "common",
        "osx",
        "linux"
    ],
    "compact_output": false
}
```

The `colors` option is for the output when you look for a command, you can custom it by yourself. (Note that the color should be in `'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'`)

## Usage

This tldr client is designed based on the [tldr-pages client specification 1.4](https://github.com/tldr-pages/tldr/blob/master/CLIENT-SPECIFICATION.md), so it is very similar to other clients. But the specification is not 100% implemented, there is some differences.

### Show help message

```bash
tldr --help
```

### Show version info

```console
$ tldr --version
multi-tldr, by Phuker, version 0.13.1
Homepage: https://github.com/Phuker/multi-tldr
This tldr client is designed based on the tldr-pages client specification 1.4, but not 100% implemented.
```

### Look up a command usage

```bash
tldr tar
tldr git pull    # same as `tldr git-pull`
```

By default, only pages on default platforms in `platform_list` are output.

You can specify platform using `-p` argument:

```bash
tldr -p osx airport    # only osx platform
tldr -p all snoop      # all platforms
```

### List tldr page files path

List all pages on all platforms:

```bash
tldr --list
```

Specify platform and/or a command:

```bash
tldr --list tar                # all platforms, only tar command
tldr --list -p linux           # only linux platform
tldr --list -p common du       # only common platform, only du command
tldr --list -p default         # only default platforms in config
tldr --list -p default tree    # only default platforms in config, only tree command
```

Fuzzy find a command:

```console
$ tldr -l | grep git | grep show
/home/user/code/tldr/pages/common/git-show.md
/home/user/code/tldr/pages/common/git-show-ref.md
/home/user/code/tldr/pages/common/git-show-branch.md
```

### Check for updates

`git pull` will be run in all dir paths of `repo_directory_list`, so that we can get the latest tldr pages.

```console
$ tldr --update
08:00:00 [INFO]:Check for updates in '/home/user/code/tldr/pages' ...
Already up to date.
08:00:02 [INFO]:Command 'git pull --stat' return code 0
08:00:02 [INFO]:Check for updates in '/home/user/code/tldr-private/pages' ...
Already up to date.
08:00:04 [INFO]:Command 'git pull --stat' return code 0
```

## FAQ

**Q: I want to add some custom command usages to a command, how to do it?**

**Q: I want to create some private command pages, how?**

A: You can contribute to [tldr-pages/tldr](https://github.com/tldr-pages/tldr), or create your own Git repo, or just create a private directory, and add it to `repo_directory_list`.

**Q: I don't like the default color theme, how to change it?**

A: Edit the configuration file, modify the color until you're happy with it.

**Q: I faided to update the tldr pages, why?**

A: Actually, This program just tries to pull the latest tldr pages for you, no magic behinds it. So the reason why you faided to update is that this program failed to pull the latest upstream, check the failing output and you may know the reason, e.g. you make some changes and haven't commit them yet. You can pull the pages by hand so you can have a better control on it.

**Q: Why use `git`, instead of download assets packaged by the official?**

A: In fact, you can use the offical assets if you want, download the assets and extract it somewhere, but this program don't support update it using `tldr --update`.

By using `git`, we can:

- make this program simple but powerful, and easy to understand and control.
- do the version control, yeah, use `git`.
- easily maintain private repos.

**Q: How to auto update tldr pages?**

A: This program will neither update tldr pages when loop up a command, nor create a daemon or service to update tldr pages periodically. Updating is totally up to you. You can run `tldr --update` manually at any time you want, or use `crontab`, Windows `Task Scheduler` or any tool else to automatically update.

## Contributing

- It sucks? Why not help me improve it? Let me know the bad things.
- Want a new feature? Feel free to file an issue for a feature request.
- Find a bug? Open an issue please, or it's better if you can send me a pull request.

Contributions are always welcome at any time!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full license text.
