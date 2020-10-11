#!/usr/bin/env python3
# encoding: utf-8

"""
multi-tldr

Yet another python client for tldr-pages/tldr. View tldr pages in multi repo, multi platform, any language at the same time.

https://github.com/Phuker/multi-tldr
"""


import os
import sys
import re
import json
import logging
import argparse
import subprocess
from operator import itemgetter

import click


__title__ = "multi-tldr"
__version__ = "0.11.1"
__author__ = "Phuker"
__homepage__ = "https://github.com/Phuker/multi-tldr"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2020 Phuker, Copyright (c) 2015 lord63"


if sys.flags.optimize > 0:
    print('Error: Do not run with "-O", assert require no optimize', file=sys.stderr)
    sys.exit(1)


_cache = {}


def get_config_path():
    config_dir_path = os.environ.get('TLDR_CONFIG_DIR') or '~'
    config_dir_path = os.path.abspath(os.path.expanduser(config_dir_path))
    config_path = os.path.join(config_dir_path, '.tldr.config.json')

    return config_path


def check_config(config):
    assert type(config) == dict, 'type(config) != dict'
    assert type(config['colors']) == dict, 'type(colors) != dict'
    assert type(config['platform']) == list, 'type(platform) != list'
    assert type(config['repo_directory']) == list, 'type(repo_directory) != list'
    assert type(config['compact_output']) == bool, 'type(compact_output) != bool'

    supported_colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white')
    if not set(config['colors'].values()).issubset(set(supported_colors)):
        bad_colors = set(config['colors'].values()) - set(supported_colors)
        bad_colors_str = ', '.join([repr(_) for _ in bad_colors])
        raise ValueError(f'Unsupported colors in config file: {bad_colors_str}')

    for platform in config['platform']:
        assert type(platform) == str, f'Bad platform value: {platform!r}'
    
    for _repo_dir in config['repo_directory']:
        assert type(_repo_dir) == str, f'Bad repo dir value: {_repo_dir!r}'
        if not os.path.exists(_repo_dir):
            raise ValueError(f"tldr repo dir not exist: {_repo_dir!r}")


def get_config():
    """Get the configurations and return it as a dict."""

    log = logging.getLogger(__name__)

    cache_key = 'config'
    cache_value = _cache.get(cache_key, None)
    if cache_value is not None:
        log.debug('Cache hit: %r', cache_key)
        return cache_value

    config_path = get_config_path()
    if not os.path.exists(config_path):
        log.error("Can't find config file at: %r. You may use `tldr --init` to init the config file.", config_path)
        sys.exit(1)

    log.debug('Reading file: %r', config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except Exception as e:
            log.error('Error when load config file %r: %r %r', config_path, type(e), e)
            sys.exit(1)

    try:
        check_config(config)
    except Exception as e:
        log.error('Check config failed: %r', e)
        sys.exit(1)

    _cache[cache_key] = config
    return config


def _get_escape_str(*args, **kwargs):
    """Wrapper of click.style(), get escape string without reset string at the end"""

    if 'reset' not in kwargs:
        kwargs['reset'] = False
    return click.style('', *args, **kwargs)


def get_escape_str(_type):
    """Get escape string by type"""

    colors = get_config()['colors']

    if _type in ('description', 'usage', 'command'):
        return _get_escape_str(fg=colors[_type], underline=False)
    elif _type == 'param':
        return _get_escape_str(fg=colors[_type], underline=True)
    else:
        raise ValueError(f'Unexpected type: {_type!r}')


def parse_inline_md(line, line_type):
    """Parse inline markdown syntax"""

    line_list = re.split(r'(`|\{\{|\}\})', line)
    line_list = [_ for _ in line_list if len(_) > 0]
    code_started = False
    result = ''
    
    result += get_escape_str(line_type)
    type_stack = [line_type]
    for item in line_list:
        if item == '`':
            if not code_started:
                result += get_escape_str('command')
                type_stack.append('command')
            else:
                type_stack.pop()
                result += get_escape_str(type_stack[-1])
            
            code_started = not code_started
        elif item == '{{':
            result += get_escape_str('param')
            type_stack.append('param')
        elif item == '}}':
            type_stack.pop()
            result += get_escape_str(type_stack[-1])
        else:
            result += item
    
    result += click.style('') # reset
    return result


def parse_page(page_file_path):
    """Parse the command man page."""

    log = logging.getLogger(__name__)

    compact_output = get_config()['compact_output']

    log.debug('Reading file: %r', page_file_path)
    with open(page_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines() # with '\n' end
    
    log.debug('Lines: %r', lines)
    
    output_lines = []
    for line in lines:
        if line.startswith('# '): # h1
            continue
        elif line.startswith('> '): # description
            line = parse_inline_md(line[2:], 'description')
            output_lines.append(line)
        elif line.startswith('- '): # usage
            line = parse_inline_md(line[2:], 'usage')
            output_lines.append(line)
        elif line.startswith('`'): # code example
            line = line.strip('`\n')
            line = parse_inline_md(line, 'command')
            line = '    ' + line + '\n'
            output_lines.append(line)
        elif line.startswith("\n"): # empty line
            if compact_output:
                pass
            else:
                output_lines.append(click.style(line)) # default: reset = True
        else:
            line = parse_inline_md(line, 'usage')
            output_lines.append(line)
    return output_lines


def get_index(repo_directory):
    """Generate index in the pages directory."""

    log = logging.getLogger(__name__)

    assert type(repo_directory) == str

    cache_key = 'index_' + repo_directory
    cache_value = _cache.get(cache_key, None)
    if cache_value is not None:
        log.debug('Cache hit: %r', cache_key)
        return cache_value

    page_path = repo_directory

    log.debug('os.walk() in %r', page_path)
    tree_generator = os.walk(page_path)
    folders = next(tree_generator)[1]
    commands, index = {}, {}
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
    index['commands'] = command_list
    
    _cache[cache_key] = index
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

    if command not in command_list:
        return []

    supported_platforms = index['commands'][command_list.index(command)]['platform']

    page_path_list = []
    for platform in platform_list:
        if platform in supported_platforms:
            page_path = os.path.join(repo_directory, os.path.join(platform, command + '.md'))
            page_path_list.append(page_path)
    
    return page_path_list


def find(command, platform):
    """Find and display the tldr pages of a command."""

    log = logging.getLogger(__name__)

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
        log.error("Command not found: %r", command)
        log.error("You can file an issue or send a PR on github: https://github.com/tldr-pages/tldr")
        sys.exit(1)
    else:
        for page_path in page_path_list:
            output_lines = parse_page(page_path)
            print(click.style(command + ' - ' + page_path, underline=True, bold=True))
            print(''.join(output_lines))


def update():
    """Update all tldr pages repo."""

    log = logging.getLogger(__name__)

    repo_directory_list = get_config()['repo_directory']

    for repo_directory in repo_directory_list:
        os.chdir(repo_directory)
        log.info("Check for updates in %r ...", repo_directory)
        subprocess.call(['git', 'pull', '--stat'])


def init():
    """Init config file."""

    log = logging.getLogger(__name__)

    config_path = get_config_path()
    if os.path.exists(config_path):
        log.warning("A config file already exists: %r", config_path)
        if click.prompt('Are you sure want to overwrite it? (yes/no)', default='no') != 'yes':
            return
    
    repo_path_list = []
    log.info('Please input repo path line by line, to "pages/" level, empty line to end.')
    while True:
        repo_path = click.prompt("Input 1 tldr repo path", default='')
        if len(repo_path) == 0:
            break
        repo_path = os.path.abspath(os.path.expanduser(repo_path))
        if not os.path.exists(repo_path):
            log.error("Repo path not exist, clone it first.")
        elif repo_path not in repo_path_list:
            repo_path_list.append(repo_path)

    platform_list = []
    platform_choice = click.Choice(('common', 'linux', 'osx', 'sunos', 'windows'))
    log.info('Please input platform line by line, empty line to end.')
    while True:
        platform = click.prompt("Input 1 platform", type=platform_choice, default='')
        if len(platform) == 0:
            break
        elif platform not in platform_list:
            platform_list.append(platform)

    color_choice = click.Choice(('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'))
    colors = {
        "description": click.prompt('Input color for description, empty to use default', type=color_choice, default='bright_yellow'),
        "usage": click.prompt('Input color for usage, empty to use default', type=color_choice, default='green'),
        "command": click.prompt('Input color for command, empty to use default', type=color_choice, default='white'),
        "param": click.prompt('Input color for param, empty to use default', type=color_choice, default='cyan'),
    }

    compact_output = click.prompt('Enable compact output (not output empty lines)? (yes/no)', default='no') == 'yes'

    config = {
        "repo_directory": repo_path_list,
        "colors": colors,
        "platform": platform_list,
        "compact_output": compact_output,
    }

    log.info("Write to config file %r", config_path)
    with open(config_path, 'w') as f:
        f.write(json.dumps(config, ensure_ascii=True, indent=4))


def locate(command, platform):
    """Locate all tldr page files path of the command."""

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
    """List all commands (on a specific platform if specified)."""

    repo_directory_list = get_config()['repo_directory']
    for repo_directory in repo_directory_list:
        command_list = find_commands_on_specified_platform(repo_directory, platform)
        command_list_output = [json.dumps([repo_directory, item]) for item in command_list]
        print('\n'.join(command_list_output))


def parse_args():
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description='Yet another python client for tldr-pages/tldr. View tldr pages in multi repo, multi platform, any language at the same time.',
        epilog='https://github.com/Phuker/multi-tldr',
        add_help=True
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--init',  action="store_true", help="Gererate config file")
    group.add_argument('--locate', metavar='command', help="Locate all tldr page files path of a command")
    group.add_argument('--list',  action="store_true", help="Print command list")
    group.add_argument('--update',  action="store_true", help="Pull all git repo")
    
    parser.add_argument('command', help="Command to query", nargs='?')
    parser.add_argument('-V', '--version',  action="store_true", help="Show version and exit")
    parser.add_argument('-p', '--platform', help='Specify platform', choices=['common', 'linux', 'osx', 'sunos', 'windows'])

    args = parser.parse_args()

    ctrl_group_set = args.init or args.locate is not None or args.list or args.update or args.version
    if ctrl_group_set and args.command is not None:
        log.error('No need argument: command')
        parser.print_help()
        sys.exit(1)
    if not ctrl_group_set and args.command is None:
        log.error('Need argument: command')
        parser.print_help()
        sys.exit(1)
    
    return args


def init_logging():
    escape_bold = _get_escape_str(bold=True)
    escape_reset = _get_escape_str(reset=True)
    escape_fg_default = _get_escape_str(fg='reset')
    escape_fg_red = _get_escape_str(fg='red')
    escape_fg_yellow = _get_escape_str(fg='yellow')
    escape_fg_cyan = _get_escape_str(fg='cyan')

    logging_stream = sys.stderr
    logging_format = f'{escape_bold}%(asctime)s [%(levelname)s]:{escape_reset}%(message)s'

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

    logging.addLevelName(logging.CRITICAL, f'{escape_fg_red}{logging.getLevelName(logging.CRITICAL)}{escape_fg_default}')
    logging.addLevelName(logging.ERROR, f'{escape_fg_red}{logging.getLevelName(logging.ERROR)}{escape_fg_default}')
    logging.addLevelName(logging.WARNING, f'{escape_fg_yellow}{logging.getLevelName(logging.WARNING)}{escape_fg_default}')
    logging.addLevelName(logging.INFO, f'{escape_fg_cyan}{logging.getLevelName(logging.INFO)}{escape_fg_default}')
    logging.addLevelName(logging.DEBUG, f'{escape_fg_cyan}{logging.getLevelName(logging.DEBUG)}{escape_fg_default}')


def cli():
    """CLI entry point"""

    init_logging()
    args = parse_args()

    if args.version:
        print(f'{__title__}\nVersion: {__version__}\nBy {__author__}\n{__homepage__}')
    elif args.init:
        init()
    elif args.locate:
        locate(args.locate, args.platform)
    elif args.list:
        list_command(args.platform)
    elif args.update:
        update()
    else:
        find(args.command, args.platform)

if __name__ == "__main__":
    cli()
