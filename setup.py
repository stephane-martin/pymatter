#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

requirements = ['future', 'requests']
setup_requires = ['setuptools_git', 'setuptools', 'twine', 'wheel', 'pip']
name = 'pymatter'
version = '0.1'
description = 'mattermost integrations in python'
author = 'Stephane Martin',
author_email = 'stephane.martin_github@vesperal.eu',
url = 'https://github.com/stephane-martin/pymatter',
licens = "LGPLv3+"
keywords = 'python mattermost webhook integration'
data_files = []
test_requirements = []

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Environment :: Plugins',
    'Environment :: Web Environment',
    'Environment :: Console',
    'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
    'Programming Language :: Python :: 2.7',
    'Operating System :: POSIX',
    'Operating System :: Microsoft :: Windows'
]

entry_points = {
    'console_scripts': [
        'pymattertee = pymatter.tee:main'
    ]
}

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

long_description = readme + '\n\n' + history


def runsetup():

    setup(
        name=name,
        version=version,
        description=description,
        long_description=long_description,
        author=author,
        author_email=author_email,
        url=url,
        packages=find_packages(exclude=['tests']),
        setup_requires=setup_requires,
        include_package_data=True,
        install_requires=requirements,
        license=licens,
        zip_safe=False,
        keywords=keywords,
        classifiers=classifiers,
        entry_points=entry_points,
        data_files=data_files,
        test_suite='tests',
        tests_require=test_requirements,
    )


if __name__ == "__main__":
    runsetup()
