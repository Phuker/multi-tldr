#!/usr/bin/env python3
# encoding: utf-8

from os import path

from basic import BasicTestCase


class TestLocate(BasicTestCase):
    def test_common_command(self):
        assert (self.call_locate_command('tldr', platform='').output.strip() ==
                path.join(self.repo_dir, 'pages', 'common', 'tldr.md'))
