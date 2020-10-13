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
import functools

import click


__title__ = "multi-tldr"
__version__ = "0.12.0"
__author__ = "Phuker"
__homepage__ = "https://github.com/Phuker/multi-tldr"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2020 Phuker, Copyright (c) 2015 lord63"

PLATFORM_DEFAULT = 0
PLATFORM_ALL = 1

if sys.flags.optimize > 0:
    print('Error: Do not run with "-O", assert require no optimize', file=sys.stderr)
    sys.exit(1)


def get_config_path():
    config_dir_path = os.environ.get('TLDR_CONFIG_DIR', '~')
    config_dir_path = os.path.abspath(os.path.expanduser(config_dir_path))
    config_path = os.path.join(config_dir_path, '.tldr.config.json')

    return config_path


def check_config(config):
    assert type(config) == dict, 'type(config) != dict'
    assert type(config['color_output']) == str, 'type(color_output) != str'
    assert type(config['colors']) == dict, 'type(colors) != dict'
    assert type(config['platform_list']) == list, 'type(platform_list) != list'
    assert type(config['repo_directory_list']) == list, 'type(repo_directory_list) != list'
    assert type(config['compact_output']) == bool, 'type(compact_output) != bool'

    supported_color_output = ('always', 'auto', 'never')
    assert config['color_output'] in supported_color_output
    
    supported_colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white')
    if not set(config['colors'].values()).issubset(set(supported_colors)):
        bad_colors = set(config['colors'].values()) - set(supported_colors)
        bad_colors_str = ', '.join([repr(_) for _ in bad_colors])
        raise ValueError(f'Unsupported colors in config file: {bad_colors_str}')

    for platform in config['platform_list']:
        assert type(platform) == str, f'Bad item in platform_list: {platform!r}'
    
    for _repo_dir in config['repo_directory_list']:
        assert type(_repo_dir) == str, f'Bad item in repo_directory_list: {_repo_dir!r}'
        if not os.path.exists(_repo_dir):
            raise ValueError(f"Path in repo_directory_list not exist: {_repo_dir!r}")


def load_json(file_path):
    log = logging.getLogger(__name__)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
            return result
    except Exception as e:
        log.error('Error when load json file %r: %r %r', file_path, type(e), e)
        sys.exit(1)


@functools.lru_cache
def get_config():
    """Get the configurations and return it as a dict."""

    log = logging.getLogger(__name__)

    config_path = get_config_path()
    if not os.path.exists(config_path):
        log.error("Can't find config file at: %r.", config_path)
        log.error('You may use `tldr --init` to init the config file.')
        sys.exit(1)

    log.debug('Reading file: %r', config_path)
    config = load_json(config_path)

    try:
        check_config(config)
        return config
    except Exception as e:
        log.error('Check config failed: %r.', e)
        log.error('You may use `tldr --init` to init the config file.')
        sys.exit(1)


def style(text, *args, **kwargs):
    """Wrapper of click.style()"""

    color_output = get_config()['color_output']

    if color_output == 'always':
        return click.style(text, *args, **kwargs)
    elif color_output == 'auto':
        if sys.stdout.isatty() and 'TERM' in os.environ:
            return click.style(text, *args, **kwargs)
        else:
            return text
    else: # 'never'
        return text


@functools.lru_cache
def get_escape_str(*args, **kwargs):
    """Wrapper of style(), get escape string without reset string at the end"""

    if 'reset' not in kwargs:
        kwargs['reset'] = False
    return style('', *args, **kwargs)


@functools.lru_cache
def get_escape_str_by_type(_type):
    """Get escape string by type"""

    colors = get_config()['colors']

    if _type in ('description', 'usage', 'command'):
        return get_escape_str(fg=colors[_type], underline=False)
    elif _type == 'param':
        return get_escape_str(fg=colors[_type], underline=True)
    else:
        raise ValueError(f'Unexpected type: {_type!r}')


def parse_inline_md(line, line_type):
    """Parse inline markdown syntax"""

    line_list = re.split(r'(`|\{\{|\}\})', line)
    line_list = [_ for _ in line_list if len(_) > 0]
    code_started = False
    result = ''
    
    result += get_escape_str_by_type(line_type)
    type_stack = [line_type]
    for item in line_list:
        if item == '`':
            if not code_started:
                result += get_escape_str_by_type('command')
                type_stack.append('command')
            else:
                type_stack.pop()
                result += get_escape_str_by_type(type_stack[-1])
            
            code_started = not code_started
        elif item == '{{':
            result += get_escape_str_by_type('param')
            type_stack.append('param')
        elif item == '}}':
            type_stack.pop()
            result += get_escape_str_by_type(type_stack[-1])
        else:
            result += item
    
    result += get_escape_str(reset=True)
    return result


def parse_page(page_file_path):
    """Parse the command man page."""

    log = logging.getLogger(__name__)

    compact_output = get_config()['compact_output']

    log.debug('Reading file: %r', page_file_path)
    with open(page_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines() # with '\n' end
    
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
            if not compact_output:
                # default: reset = True, add reset string at the end
                output_lines.append(style(line))
            else:
                pass
        else:
            line = parse_inline_md(line, 'usage')
            output_lines.append(line)
    return output_lines


@functools.lru_cache
def get_index(repo_directory):
    """Generate index in the pages directory.
    Return: [(platform, command), ]
    """

    assert type(repo_directory) == str

    log = logging.getLogger(__name__)

    index = []

    log.debug('os.walk() in %r', repo_directory)
    tree_generator = os.walk(repo_directory)
    platforms = next(tree_generator)[1]
    
    for platform in platforms:
        pages = next(tree_generator)[2]
        index += [(platform, os.path.splitext(page)[0]) for page in pages]
    
    return index


def get_page_path_list(command=None, platform=PLATFORM_DEFAULT):
    """Get page_path_list in all repo"""

    assert command is None or type(command) == str
    assert type(platform) in (int, str)

    repo_directory_list = get_config()['repo_directory_list']
    default_platform_set = set(get_config()['platform_list'])

    page_path_list = []
    for repo_directory in repo_directory_list:
        index = get_index(repo_directory)

        if command is not None:
            filter_func = lambda entry: entry[1] == command
            index = filter(filter_func, index)
        
        if platform == PLATFORM_ALL:
            pass
        elif platform == PLATFORM_DEFAULT:
            index = filter(lambda entry: entry[0] in default_platform_set, index)
        else:
            index = filter(lambda entry: entry[0] == platform, index)

        page_path_list += [os.path.join(repo_directory, entry[0], entry[1] + '.md') for entry in index]
    
    return page_path_list


def action_init():
    """Interactively gererate config file"""

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

    log.info('Please input colors, empty to use default.')
    colors_choice = click.Choice(('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'))
    colors = {
        "description": click.prompt('Input color for description', type=colors_choice, default='bright_yellow'),
        "usage": click.prompt('Input color for usage', type=colors_choice, default='green'),
        "command": click.prompt('Input color for command', type=colors_choice, default='white'),
        "param": click.prompt('Input color for param', type=colors_choice, default='cyan'),
    }

    color_output_choice = click.Choice(('always', 'auto', 'never'))
    color_output = click.prompt('When output with color?', type=color_output_choice, default='auto')

    compact_output = click.prompt('Enable compact output (not output empty lines)? (yes/no)', default='no') == 'yes'

    config = {
        'repo_directory_list': repo_path_list,
        'color_output': color_output,
        'colors': colors,
        'platform_list': platform_list,
        'compact_output': compact_output,
    }

    log.info("Write to config file %r", config_path)
    with open(config_path, 'w') as f:
        f.write(json.dumps(config, ensure_ascii=True, indent=4))


def action_update():
    """Update all tldr pages repo."""

    log = logging.getLogger(__name__)

    repo_directory_list = get_config()['repo_directory_list']

    for repo_directory in repo_directory_list:
        os.chdir(repo_directory)
        log.info("Check for updates in %r ...", repo_directory)
        subprocess.call(['git', 'pull', '--stat'])


def action_find(command, platform):
    """Find and display the tldr pages of a command."""

    assert type(command) == str
    assert platform is None or type(platform) == str

    log = logging.getLogger(__name__)

    if platform:
        page_path_list = get_page_path_list(command, platform)
    else:
        page_path_list = get_page_path_list(command, PLATFORM_DEFAULT)
    
    if len(page_path_list) == 0:
        log.error("Command not found: %r", command)
        log.error("You can file an issue or send a PR on github: https://github.com/tldr-pages/tldr")
        sys.exit(1)
    else:
        for page_path in page_path_list:
            output_lines = parse_page(page_path)
            print(style(command + ' - ' + page_path, underline=True, bold=True))
            print(''.join(output_lines))


def action_list_command(command, platform):
    """Locate all tldr page files path of the command."""
    
    assert command is None or type(command) == str
    assert platform is None or type(platform) == str

    if platform:
        page_path_list = get_page_path_list(command, platform)
    else:
        page_path_list = get_page_path_list(command, PLATFORM_ALL)
    
    for page_path in page_path_list:
        try:
            print(page_path)
        except BrokenPipeError:
            sys.exit()


def action_version():
    print(f'{__title__}')
    print(f'Version: {__version__}')
    print(f'By {__author__}')
    print(f'{__homepage__}')


def parse_args(args=sys.argv[1:]):
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description='Yet another python client for tldr-pages/tldr. View tldr pages in multi repo, multi platform, any language at the same time.',
        epilog='https://github.com/Phuker/multi-tldr',
        add_help=True
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--init', action="store_true", help="Interactively gererate config file")
    group.add_argument('--list', action='store_true', help="Print all tldr page files path (of a command if specified) in all repo on all/specified platform")
    group.add_argument('--update', action="store_true", help="Pull all git repo")
    
    parser.add_argument('command', help="Command to query", nargs='?')
    parser.add_argument('-p', '--platform', help='Specify platform', choices=['common', 'linux', 'osx', 'sunos', 'windows'])

    parser.add_argument('-V', '--version', action="store_true", help="Show version and exit")

    args = parser.parse_args(args)

    ctrl_group_set = args.init or args.list or args.update
    ok_conditions = [
        args.version,
        args.init and args.command is None and args.platform is None,
        args.list,
        args.update and args.command is None and args.platform is None,
        not ctrl_group_set and args.command is not None,
    ]

    if not any(ok_conditions):
        log.error('Bad arguments')
        parser.print_help()
        sys.exit(1)
    
    return args


def init_logging():
    escape_bold = get_escape_str(bold=True)
    escape_reset = get_escape_str(reset=True)
    escape_fg_default = get_escape_str(fg='reset')
    escape_fg_red = get_escape_str(fg='red')
    escape_fg_yellow = get_escape_str(fg='yellow')
    escape_fg_cyan = get_escape_str(fg='cyan')

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
        action_version()
    elif args.init:
        action_init()
    elif args.list:
        action_list_command(args.command, args.platform)
    elif args.update:
        action_update()
    else:
        action_find(args.command, args.platform)


if __name__ == "__main__":
    cli()
