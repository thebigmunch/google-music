__all__ = ['GoogleMusicSession']

import json
import os

import appdirs
from requests_oauthlib import OAuth2Session

from . import __author__, __title__, __version__

TOKEN_DIR = appdirs.user_data_dir(__title__, __author__)


def ensure_token_directory(token_dir):
	try:
		os.makedirs(token_dir)
	except OSError:
		if not os.path.isdir(token_dir):
			raise


def dump_token(username, client, token):
	token_path = os.path.join(TOKEN_DIR, username, f'{client}.token')
	ensure_token_directory(os.path.dirname(token_path))

	with open(token_path, 'w') as f:
		json.dump(token, f)


def load_token(username, client):
	with open(os.path.join(TOKEN_DIR, username, f'{client}.token'), 'r') as f:
		token = json.load(f)

		return token


class GoogleMusicSession(OAuth2Session):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.headers.update({
			'User-Agent': f'{__title__}/{__version__}'
		})
