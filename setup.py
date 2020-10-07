#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

import tldr

with open('Readme.md') as f:
    long_description = f.read()

setup(
    name='multi-tldr',
    version=tldr.__version__,
    description='A python client for tldr: simplified and community-driven man pages.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Phuker',
    # author_email='',
    url='https://github.com/Phuker/multi-tldr',
    license='MIT',
    keywords='tldr cli man command usage',
    packages=[],
    py_modules = ['tldr'],
    install_requires=[
        'click>=5.0',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'tldr=tldr:cli'
        ]
    },
    classifiers=[
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    python_requires = '>=3'
)
