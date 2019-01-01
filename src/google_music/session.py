__all__ = ['GoogleMusicSession']

import json
from pathlib import Path

import appdirs
from requests_oauthlib import OAuth2Session

from . import __author__, __title__, __version__

TOKEN_DIR = Path(appdirs.user_data_dir(__title__, __author__))


def dump_token(token, username, client):
	username = username or ''
	token_path = TOKEN_DIR / username / f'{client}.token'

	try:
		token_path.mkdir(parents=True)
	except FileExistsError:
		pass

	with token_path.open('w') as f:
		json.dump(token, f)


def load_token(username, client):
	username = username or ''
	token_path = TOKEN_DIR / username / f'{client}.token'

	with token_path.open('r') as f:
		token = json.load(f)

	return token


class GoogleMusicSession(OAuth2Session):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.headers.update(
			{'User-Agent': f'{__title__}/{__version__}'}
		)
