#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

base_dir = os.path.dirname(__file__)

about = {}
with open(os.path.join(base_dir, 'src', 'google_music', '__about__.py')) as f:
	exec(f.read(), about)

setup(
	name=about['__title__'],
	version=about['__version__'],
	description=about['__summary__'],
	url=about['__url__'],
	license=about['__license__'],
	author=about['__author__'],
	author_email=about['__author_email__'],

	keywords=[],
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
	],

	install_requires=[
		'appdirs>=1.4',
		'audio-metadata>=0.3',
		'google-music-proto>=2.5',
		'protobuf>=3.5',
		'requests-oauthlib>=1.0',
		'tenacity>=5.0',
		'wrapt>=1.0'
	],

	extras_require={
		'doc': ['sphinx'],
		'lint': [
			'flake8',
			'flake8-builtins',
			'flake8-import-order',
			'flake8-import-order-tbm'
		],
	},

	packages=find_packages('src'),
	package_dir={
		'': 'src'
	},

	zip_safe=False
)
