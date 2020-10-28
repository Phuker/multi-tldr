#!/usr/bin/env python3
# encoding: utf-8

"""
All patterns in all tldr pages

https://github.com/Phuker/multi-tldr
"""

import os
import sys
import argparse
import logging
import re
import string

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


def parse_args():
    parser = argparse.ArgumentParser(
        description='Get all possible patterns of tldr pages',
        add_help=True
    )

    parser.add_argument('tldr_dir', metavar='DIR', help='tldr page repo dir path')
    args = parser.parse_args()

    return args


args = parse_args()
logging.debug('argparse result: %r', args)

pattern_set = set()


def replace_all(s, search, replace):
    while True:
        old_s = s
        s = s.replace(search, replace)
        if s == old_s:
            return s


def get_inline(line):
    if line.startswith('# '):
        line = line[2:]
    elif line.startswith('`') and line.endswith('`'):
        line = line[1:-1]
    elif line.startswith('- '):
        line = line[2:]
    elif line.startswith('> '):
        line = line[2:]
    
    return line


def get_inline_pattern(line):
    special_chars = '<>`{}'
    replace_list = (
        ('aa', 'a'),
        ('{{a}}{{a}}', '{{a}}'),
        ('{{a}}a{{a}}', '{{a}}'),
        ('`a``a`', '`a`'),
        ('`a`a`a`', '`a`'),
        ('<a><a>', '<a>'),
        ('<a>a<a>', '<a>'),
    )

    old_line = line
    line = ''
    for ch in old_line:
        if ch not in special_chars:
            line += 'a'
        else:
            line += ch
        
    while True:
        old_line = line

        for search, replace in replace_list:
            line = replace_all(line, search, replace)

        if line == old_line:
            return line
        

def get_file_pattern(file_path):
    logging.debug('get pattern in: %r', file_path)

    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    file_path_printed = False
    for line in lines:
        original_line = line.rstrip('\n')
        line = get_inline(original_line)
        pattern = get_inline_pattern(line)

        if pattern not in pattern_set:
            pattern_set.add(pattern)

            if not file_path_printed:
                print(f'\x1b[1;4;33m{file_path}\x1b[0m')
                file_path_printed = True
            
            print(f'\x1b[36m{original_line}\x1b[0m')
            print(pattern)


def main():
    for top, _, files in os.walk(args.tldr_dir):
        for filename in files:
            if filename.endswith('.md'):
                get_file_pattern(os.path.join(top, filename))

    print('- ' * 38)
    print('Patterns count: ', len(pattern_set))
    print('- ' * 38)
    for pattern in sorted(list(pattern_set)):
        print(pattern)


if __name__ == "__main__":
    main()

