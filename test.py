#!/usr/bin/env python3
# encoding: utf-8

import os
import copy
import unittest
import unittest.mock

import tldr

ROOT = os.path.dirname(os.path.realpath(__file__))

print(f'Testing tldr: {tldr!r}')
print(f'Root dir of project: {ROOT!r}')

ok_config = {
    "repo_directory_list": [
        os.path.join(ROOT, 'tldr-pages-test', 'pages1'),
        os.path.join(ROOT, 'tldr-pages-test', 'pages2')
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
    "compact_output": False
}

class TldrPureFunctionTests(unittest.TestCase):
    def test_get_config_path(self):
        self.assertIsInstance(tldr.get_config_path(), str)
    
    def test_check_config(self):
        self.assertRaises(AssertionError, tldr.check_config, '')
        self.assertRaises(AssertionError, tldr.check_config, [])
        self.assertRaises(KeyError, tldr.check_config, {})

        tldr.check_config(ok_config)

        config = copy.deepcopy(ok_config)
        config['repo_directory_list'] = ''
        self.assertRaises(AssertionError, tldr.check_config, config)

        config = copy.deepcopy(ok_config)
        config['colors'] = []
        self.assertRaises(AssertionError, tldr.check_config, config)

        config = copy.deepcopy(ok_config)
        config['platform_list'] = {}
        self.assertRaises(AssertionError, tldr.check_config, config)

        config = copy.deepcopy(ok_config)
        config['compact_output'] = 1
        self.assertRaises(AssertionError, tldr.check_config, config)

        config = copy.deepcopy(ok_config)
        config['repo_directory_list'] = ['/not.exist.dir']
        self.assertRaises(ValueError, tldr.check_config, config)

        config = copy.deepcopy(ok_config)
        config['colors']['description'] = 'not-exist-color'
        self.assertRaises(ValueError, tldr.check_config, config)

        config = copy.deepcopy(ok_config)
        config['platform_list'] = 'not_exist_os'
        self.assertRaises(AssertionError, tldr.check_config, config)

    def test_get_escape_str(self):
        self.assertEqual(tldr.get_escape_str(fg='red'), '\x1b[31m')
        self.assertEqual(tldr.get_escape_str(fg='reset'), '\x1b[39m')
        self.assertEqual(tldr.get_escape_str(reset=True), '\x1b[0m')
        self.assertEqual(tldr.get_escape_str(), '')
    
    def test_parse_args(self):
        tldr.parse_args(['-V'])
        tldr.parse_args(['--version'])
        tldr.parse_args(['--version', 'tar'])
        tldr.parse_args(['--version', '-p', 'linux', 'tar'])
        tldr.parse_args(['--init'])
        tldr.parse_args(['--list'])
        tldr.parse_args(['--list', 'tar'])
        tldr.parse_args(['--list', '-p', 'linux'])
        tldr.parse_args(['--list', '-p', 'linux', 'tar'])
        tldr.parse_args(['--update'])

        for args in (
            ['--xxxx'],
            ['--init', '-p', 'linux'],
            ['--init', 'tar'],
            ['--init', '-p', 'linux', 'tar'],
            ['--update', '-p', 'linux'],
            ['--update', 'tar'],
            ['--update', '-p', 'linux', 'tar'],
            ['--init', '--list'],
            ['--init', '--update'],
            ['--list', '--update'],
            ['--init', '--list', '--update'],
        ):
            self.assertRaises(SystemExit, tldr.parse_args, args)


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        tldr.get_index.cache_clear()
        tldr.get_config.cache_clear()
        tldr.get_escape_str.cache_clear()
        tldr.get_escape_str_by_type.cache_clear()
        tldr.load_json = unittest.mock.Mock(return_value=copy.deepcopy(ok_config))


class TldrTests(BasicTestCase):
    def test_get_config(self):
        tldr.get_config()
    
    def test_get_escape_str_by_type(self):
        self.assertEqual(tldr.get_escape_str_by_type('description'), '\x1b[93m\x1b[24m')
        self.assertEqual(tldr.get_escape_str_by_type('usage'), '\x1b[32m\x1b[24m')
        self.assertEqual(tldr.get_escape_str_by_type('command'), '\x1b[37m\x1b[24m')
        self.assertEqual(tldr.get_escape_str_by_type('param'), '\x1b[36m\x1b[4m')
    
    def test_parse_inline_md(self):
        line = 'usage 1 `command 1` usage 2 `command 2 {{param 1}}` usage 3 `command 3 {{param 2}} command 4` usage 4 `{{param 3}} command 5 end` usage 5 `{{param 4}}` usage 6 {{param 5 end}} usage 7 end'

        line = 'usage `command` usage'
        result = '\x1b[32m\x1b[24musage \x1b[37m\x1b[24mcommand\x1b[32m\x1b[24m usage\x1b[0m'
        self.assertEqual(tldr.parse_inline_md(line, 'usage'), result)

        line = 'usage `command {{param}} command` usage'
        result = '\x1b[32m\x1b[24musage \x1b[37m\x1b[24mcommand \x1b[36m\x1b[4mparam\x1b[37m\x1b[24m command\x1b[32m\x1b[24m usage\x1b[0m'
        self.assertEqual(tldr.parse_inline_md(line, 'usage'), result)
    
    def test_get_index(self):
        result = [
            ('osx', 'airport'),
            ('osx', 'du'),
            ('linux', 'du'),
            ('linux', 'tcpflow'),
            ('common', 'tldr-test')
        ]
        repo_path = os.path.join(ROOT, 'tldr-pages-test', 'pages1')
        self.assertEqual(sorted(tldr.get_index(repo_path)), sorted(result))

        result = [
            ('common', 'tldr-test'),
            ('sunos', 'tldr-test'),
        ]
        repo_path = os.path.join(ROOT, 'tldr-pages-test', 'pages2')
        self.assertEqual(sorted(tldr.get_index(repo_path)), sorted(result))

    def test_get_page_path_list(self):
        result_expected = [
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'sunos', 'tldr-test.md'),
        ]
        result = tldr.get_page_path_list('tldr-test', tldr.PLATFORM_ALL)
        self.assertEqual(sorted(result_expected), sorted(result))

        result_expected = [
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'common', 'tldr-test.md'),
        ]
        result = tldr.get_page_path_list('tldr-test', tldr.PLATFORM_DEFAULT)
        self.assertEqual(sorted(result_expected), sorted(result))

        result_expected = [
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'linux', 'du.md'),
        ]
        result = tldr.get_page_path_list('du', 'linux')
        self.assertEqual(sorted(result_expected), sorted(result))

        result_expected = [
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'linux', 'du.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'linux', 'tcpflow.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'osx', 'airport.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'osx', 'du.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'sunos', 'tldr-test.md'),
        ]
        result = tldr.get_page_path_list(None, tldr.PLATFORM_ALL)
        self.assertEqual(sorted(result_expected), sorted(result))

        result_expected = [
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'linux', 'du.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'linux', 'tcpflow.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'osx', 'airport.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'osx', 'du.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'common', 'tldr-test.md'),
        ]
        result = tldr.get_page_path_list(None, tldr.PLATFORM_DEFAULT)
        self.assertEqual(sorted(result_expected), sorted(result))

        result_expected = [
            os.path.join(ROOT, 'tldr-pages-test', 'pages1', 'common', 'tldr-test.md'),
            os.path.join(ROOT, 'tldr-pages-test', 'pages2', 'common', 'tldr-test.md'),
        ]
        result = tldr.get_page_path_list(None, 'common')
        self.assertEqual(sorted(result_expected), sorted(result))

if __name__ == "__main__":
    unittest.main()
