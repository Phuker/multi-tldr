#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
multi-tldr

A python client for tldr: simplified and community-driven man pages.
"""


import os
import sys
import json
import logging
import argparse
import subprocess
from operator import itemgetter

import click


__title__ = "multi-tldr"
__version__ = "0.9.0"
__author__ = "Phuker"
__homepage__ = "https://github.com/Phuker/multi-tldr"
__license__ = "MIT"
__copyright__ = "Copyright 2020 Phuker"


logging_stream = sys.stderr
logging_format = '\033[1m%(asctime)s [%(levelname)s]:\033[0m%(message)s'

if 'DEBUG' in os.environ:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

if logging_stream.isatty():
    logging_date_format = '%H:%M:%S'
else:
    print('', file=logging_stream)
    logging_date_format = '%Y-%m-%d %H:%M:%S'

logging.basicConfig(
    level=logging_level,
    format=logging_format,
    datefmt=logging_date_format,
    stream=logging_stream,
)

logging.addLevelName(logging.CRITICAL, '\033[31m{}\033[39m'.format(logging.getLevelName(logging.CRITICAL)))
logging.addLevelName(logging.ERROR, '\033[31m{}\033[39m'.format(logging.getLevelName(logging.ERROR)))
logging.addLevelName(logging.WARNING, '\033[33m{}\033[39m'.format(logging.getLevelName(logging.WARNING)))
logging.addLevelName(logging.INFO, '\033[36m{}\033[39m'.format(logging.getLevelName(logging.INFO)))
logging.addLevelName(logging.DEBUG, '\033[36m{}\033[39m'.format(logging.getLevelName(logging.DEBUG)))


if sys.flags.optimize > 0:
    logging.critical('Do not run with "-O", assert require no optimize')
    sys.exit(1)



def get_config_path():
    config_dir_path = os.environ.get('TLDR_CONFIG_DIR') or '~'
    config_dir_path = os.path.abspath(os.path.expanduser(config_dir_path))
    config_path = os.path.join(config_dir_path, '.tldr.config.json')

    return config_path


def get_config():
    """Get the configurations and return it as a dict."""

    config_path = get_config_path()
    if not os.path.exists(config_path):
        logging.error("Can't find config file at: %r. You may use `tldr --init` to init the config file.", config_path)
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except Exception as e:
            logging.error('Error when load config file %r: %r %r', config_path, type(e), e)
            sys.exit(1)

    assert type(config['platform']) == list
    assert type(config['repo_directory']) == list

    supported_colors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    if not set(config['colors'].values()).issubset(set(supported_colors)):
        logging.error('Unsupported colors in config file: %s', ', '.join(set(config['colors'].values()) - set(supported_colors)))
        sys.exit(1)

    for _repo_dir in config['repo_directory']:
        if not os.path.exists(_repo_dir):
            logging.error("Can't find the tldr repo, check the `repo_directory` setting in config file.")
            sys.exit(1)

    return config


def parse_page(page):
    """Parse the command man page."""

    colors = get_config()['colors']
    with open(page, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = []
    for line in lines[1:]:
        if line.startswith('# '): # h1
            continue
        elif line.startswith('> '): # description
            output_lines.append(click.style(line[2:], fg=colors['description']))
        elif line.startswith('- '): # usage
            output_lines.append(click.style(line[2:], fg=colors['usage']))
        elif line.startswith('`'): # code example
            line = '    ' + line.strip('`\n') + '\n'
            line = line.replace('{{', click.style('', fg=colors['param'], underline=True, reset=False))
            line = line.replace('}}', click.style('', fg=colors['command'], underline=False, reset=False))
            output_lines.append(click.style(line, fg=colors['command']))
        elif line.startswith("\n"): # empty line
            output_lines.append(click.style(line))
        else:
            output_lines.append(click.style(line, fg=colors['usage']))
    return output_lines


def get_index(repo_directory):
    """Retrieve index in the pages directory."""

    assert type(repo_directory) == str

    with open(os.path.join(repo_directory, 'pages/index.json'), 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    return index


def find_commands(repo_directory):
    """List commands in the pages directory."""
    
    assert type(repo_directory) == str

    index = get_index(repo_directory)
    return [item['name'] for item in index['commands']]


def find_commands_on_specified_platform(repo_directory, specified_platform):
    """List commands on the specified platform"""

    assert type(repo_directory) == str
    assert specified_platform is None or type(specified_platform) == str

    default_platform_list = get_config()['platform']

    index = get_index(repo_directory)

    platform_list = ([specified_platform] if specified_platform else default_platform_list)

    return [item['name'] for item in index['commands'] if [_ for _ in platform_list if _ in item['platform']]]


def find_page_location(command, platform_list, repo_directory):
    assert type(platform_list) == list
    assert type(repo_directory) == str

    index = get_index(repo_directory)
    command_list = find_commands(repo_directory)

    page_path_list = []

    if command not in command_list:
        return page_path_list

    supported_platforms = index['commands'][command_list.index(command)]['platform']

    for platform in platform_list:
        if platform in supported_platforms:
            page_path = os.path.join(os.path.join(repo_directory, 'pages'), os.path.join(platform, command + '.md'))
            page_path_list.append(page_path)
    
    return page_path_list


def build_index():
    """Rebuild the index."""

    repo_directory_list = get_config()['repo_directory']

    for repo_directory in repo_directory_list:
        logging.info('Rebuild the index in %r', repo_directory)
        index_path = os.path.join(repo_directory, 'pages', 'index.json')
        page_path = os.path.join(repo_directory, 'pages')

        tree_generator = os.walk(page_path)
        folders = next(tree_generator)[1]
        commands, new_index = {}, {}
        for folder in folders:
            pages = next(tree_generator)[2]
            for page in pages:
                command_name = os.path.splitext(page)[0]
                if command_name not in commands:
                    commands[command_name] = {
                        'name': command_name,
                        'platform': [folder]
                    }
                else:
                    commands[command_name]['platform'].append(folder)
        command_list = [item[1] for item in sorted(commands.items(), key=itemgetter(0))]
        new_index['commands'] = command_list

        with open(index_path, mode='w') as f:
            json.dump(new_index, f)


def find(command, platform):
    """Find the command usage."""

    repo_directory_list = get_config()['repo_directory']
    default_platform_list = get_config()['platform']

    if platform:
        platform_list = [platform]
    else:
        platform_list = default_platform_list

    page_path_list = []
    for repo_directory in repo_directory_list:
        page_path_list += find_page_location(command, platform_list, repo_directory)
    
    if len(page_path_list) == 0:
        logging.error("Command not found: %r", command)
        logging.error("You can file an issue or send a PR on github: https://github.com/tldr-pages/tldr")
        sys.exit(1)
    else:
        for page_path in page_path_list:
            output_lines = parse_page(page_path)
            print(click.style(page_path, underline=True, bold=True))
            print(''.join(output_lines))


def update():
    """Update to the latest pages."""

    repo_directory_list = get_config()['repo_directory']

    for repo_directory in repo_directory_list:
        os.chdir(repo_directory)
        logging.info("Check for updates in %r ...", repo_directory)
        subprocess.call(['git', 'pull', '--stat'])
    
    build_index()


def init():
    """Init config file."""

    config_path = get_config_path()
    if os.path.exists(config_path):
        logging.warning("A config file already exists: %r", config_path)
        if click.prompt('Are you sure want to overwrite it? Enter "yes" to confirm.', default='no') != 'yes':
            return
    
    repo_path_list = []
    logging.info('Please input repo path line by line, empty line to end.')
    while True:
        repo_path = click.prompt("Input 1 tldr repo path", default='')
        if len(repo_path) == 0:
            break
        repo_path = os.path.abspath(os.path.expanduser(repo_path))
        if not os.path.exists(repo_path):
            logging.error("Repo path not exist, clone it first.")
        elif repo_path not in repo_path_list:
            repo_path_list.append(repo_path)

    platform_list = []
    platform_choice = click.Choice(('common', 'linux', 'osx', 'sunos', 'windows'))
    logging.info('Please input platform line by line, empty line to end.')
    while True:
        platform = click.prompt("Input 1 platform", type=platform_choice, default='')
        if len(platform) == 0:
            break
        elif platform not in platform_list:
            platform_list.append(platform)

    color_choice = click.Choice(('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'))
    colors = {
        "description": click.prompt('Input color for description, empty to use default', type=color_choice, default='cyan'),
        "usage": click.prompt('Input color for usage, empty to use default', type=color_choice, default='green'),
        "command": click.prompt('Input color for command, empty to use default', type=color_choice, default='white'),
        "param": click.prompt('Input color for param, empty to use default', type=color_choice, default='cyan'),
    }

    config = {
        "repo_directory": repo_path_list,
        "colors": colors,
        "platform": platform_list
    }

    logging.info("Write to config file %r", config_path)
    with open(config_path, 'w') as f:
        f.write(json.dumps(config, ensure_ascii=True, indent=4))

    build_index()


def locate(command, platform):
    """Locate the command's man page file path."""

    repo_directory_list = get_config()['repo_directory']
    default_platform_list = get_config()['platform']

    if platform:
        platform_list = [platform]
    else:
        platform_list = default_platform_list

    page_path_list = []
    for repo_directory in repo_directory_list:
        page_path_list += find_page_location(command, platform_list, repo_directory)
    
    for page_path in page_path_list:
        print(page_path)


def list_command(platform): # do NOT name 'list', conflict with keyword
    """list the command's man page."""

    repo_directory_list = get_config()['repo_directory']
    for repo_directory in repo_directory_list:
        command_list = find_commands_on_specified_platform(repo_directory, platform)
        command_list_output = [json.dumps([repo_directory, item]) for item in command_list]
        print('\n'.join(command_list_output))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Yet another python client for tldr.',
        epilog='https://github.com/Phuker/multi-tldr',
        add_help=True
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--init',  action="store_true", help="Gererate config file, rebuild the index")
    group.add_argument('--locate', metavar='command', help="Locate tldr page file path of a command")
    group.add_argument('--list',  action="store_true", help="Print a command list")
    group.add_argument('--reindex',  action="store_true", help="Rebuild the index")
    group.add_argument('--update',  action="store_true", help="Pull all git repo, rebuild the index")
    
    parser.add_argument('command', help="Command to query", nargs='?')
    parser.add_argument('-V', '--version',  action="store_true", help="Show version and exit.")
    parser.add_argument('-p', '--platform', help='Specify platform.', choices=['common', 'linux', 'osx', 'sunos', 'windows'])

    args = parser.parse_args()

    ctrl_group_set = args.init or args.locate is not None or args.list or args.reindex or args.update or args.version
    if ctrl_group_set and args.command is not None:
        logging.error('No need argument: command')
        sys.exit(1)
    if not ctrl_group_set and args.command is None:
        logging.error('Need argument: command')
        sys.exit(1)
    
    return args


def cli():
    """A python client for tldr: simplified and community-driven man pages."""

    args = parse_args()

    if args.version:
        print(f'{__title__}\nVersion: {__version__}\nBy {__author__}\n{__homepage__}')
    elif args.init:
        init()
    elif args.locate:
        locate(args.locate, args.platform)
    elif args.list:
        list_command(args.platform)
    elif args.reindex:
        build_index()
    elif args.update:
        update()
    else:
        find(args.command, args.platform)

if __name__ == "__main__":
    cli()