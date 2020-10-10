#!/usr/bin/env python3
# encoding: utf-8

from setuptools import setup

import tldr

with open('Readme.PyPI.md', 'r') as f:
    long_description = f.read()

setup(
    name='multi-tldr',
    version=tldr.__version__,
    description='Yet another python client for tldr-pages/tldr. View tldr pages in multi repo, multi platform, any language at the same time.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Phuker',
    author_email='Phuker@users.noreply.github.com',
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
        'Environment :: Console',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    python_requires = '>=3.6'
)
