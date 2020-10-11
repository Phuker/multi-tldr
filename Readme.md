# multi-tldr

Yet another python client for [tldr-pages/tldr](https://github.com/tldr-pages/tldr). View tldr pages in multi repo, multi platform, any language at the same time.

Forked and modified from [lord63/tldr.py](https://github.com/lord63/tldr.py), whose original idea is very good.

## Intro

Instead of the long man pages, tldr will give you several simple yet powerful examples:

![tar-tldr-page](screenshots/screenshot1.png)

The command examples are not good? Don't worry, you can set up your own `tldr`! They are just [simplified markdown files](https://github.com/tldr-pages/tldr/blob/master/contributing-guides/style-guide.md) and you can create your own pages. You can contribute to [tldr-pages/tldr](https://github.com/tldr-pages/tldr), or keep them private.

One more thing, `tldr` is just a simple version for the man page, it's **NOT** an alternative. Sometimes, you should read the man pages patiently.

## Features

- Use local file, fast and no network delay. tldr pages are managed and updated by `git`.
- Support custom output color.

### Differences with `lord63/tldr.py`

- No need to use `tldr find xxxxxx` or alias to `tldr find`, just type `tldr xxxxxx` ([related issue](https://github.com/lord63/tldr.py/issues/47))
- No need to rebuild index, or generate `index.json` file.
- Support display multi repo and multi platform at the same time. You can create your own private tldr pages repo.
- New feature: compact output, not output empty lines.
- Advanced parser: render `{{` and `}}` ([related issue](https://github.com/lord63/tldr.py/issues/25)), render `` ` `` inline code.
- Config file format `YAML` --> `JSON`, because I hate `YAML`.
- Support tlgr pages in other languages, by specify `repo_directory` dir path to the `pages/` level.
- Drop support for Python 2.

## Requirements

- Python >= `3.6`, with `pip` installed

### Recommend

- Git: if you do not have `git`, you can still download `.zip` file from [tldr-pages/tldr](https://github.com/tldr-pages/tldr), extract it, and add it to `repo_directory` config, most things still work, but `tldr --update` will NOT work.

## Install

```bash
python3 -m pip install -U multi-tldr
```

## Initialize manually

### Clone [tldr-pages/tldr](https://github.com/tldr-pages/tldr)

First, clone the [tldr-pages/tldr](https://github.com/tldr-pages/tldr) to somewhere (e.g. `~/code/tldr`). We will use it when we look for a command usage.

```bash
git clone --depth=1 https://github.com/tldr-pages/tldr.git
```

### Create config file

Then, run this command to interactively generate configuration file:

```bash
tldr --init
```

Your configuration file should look like this:

```json
{
    "repo_directory": [
        "/home/user/code/tldr/pages/",
        "/home/user/code/tldr-private/pages.zh"
    ],
    "colors": {
        "description": "bright_yellow",
        "usage": "green",
        "command": "white",
        "param": "cyan"
    },
    "platform": [
        "common",
        "osx",
        "linux"
    ],
    "compact_output": false
}
```

The `colors` option is for the output when you look for a command, you can custom it by yourself. (Note that the color should be in `'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'`)

The default location for the configuration file is `~/.tldrrc.json`, you can use the `TLDR_CONFIG_DIR` environment variable to point it to another folder (e.g. `$HOME/.config`).

## Usage

You can run `tldr --help` to get the help message.

### Look for a command usage

```bash
tldr tar
```

You can specify a platform using `-p` argument:

```bash
tldr -p osx airport
```

### Check for updates

`git pull` will be run in all `repo_directory`, so that we can get the latest tldr pages

```console
$ tldr --update
Check for updates in '/home/user/code/tldr' ...
Already up to date.
Check for updates in '/home/user/code/tldr-private' ...
Already up to date.
```

## Locate all tldr page files path of a command

```bash
tldr --locate {{command}}
```

## List all commands

```bash
tldr --list
```

It will output `json` format each line.

## FAQ

**Q: I want to add some custom command usages to a command, how to do it?**

**Q: I want to add some custom command pages, how?**

A: You can contribute to [tldr-pages/tldr](https://github.com/tldr-pages/tldr), or create your own Git repo, or just create a private directory, and add it to `repo_directory`.

**Q: I want a short command like `tldr COMMAND`, not `tldr find COMMAND`.**

A: This problem not exists any more.

**Q: Do I need to rebuild any index after `git pull` or create new `.md` files?**

A: You don't any more. Local file is fast enough, and I added a cache variable.

**Q: I want fuzzy find command usage.**

A: `tldr list | grep KEYWORD`

**Q: I don't like the default color theme, how to change it?**

A: Edit the tldr configuration file at `~/.tldrrc.json`; modify the color until you're happy with it.

**Q: I faided to update the tldr pages, why?**

A: Actually, `tldr.py` just tries to pull the latest tldr pages for you, no magic behinds it. So the reason why you faided to update is that `tldr.py` failed to pull the latest upstream, check the failing output and you may know the reason, e.g. you make some changes and haven't commit them yet. You can pull the pages by hand so you can have a better control on it.

**Q: Why use the git repo instead of the assets packaged by the official?**

A: In fact, you can use the offical assets if you want, download the assets and extract it somewhere, but `tldr.py` don't support update it using `tldr update`.

Use a `git` repo, you can:

- do the version control, yeah, use `git`.
- better for customization, just edit the pages and add new pages, they belongs to you. You can even maintain your own 'tldr'. If use the official assets, you'll always get the latest pages.

## Contributing

- It sucks? Why not help me improve it? Let me know the bad things.
- Want a new feature? Feel free to file an issue for a feature request.
- Find a bug? Open an issue please, or it's better if you can send me a pull request.

Contributions are always welcome at any time!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full license text.
