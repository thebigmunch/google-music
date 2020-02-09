__all__ = [
	'FileTokenHandler',
	'TokenHandler',
]

import abc
import json
from pathlib import Path

import appdirs

from .__about__ import __author__, __title__

TOKEN_DIR = Path(appdirs.user_data_dir(__title__, __author__))


class TokenHandler(abc.ABC):
	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)

	@abc.abstractmethod
	def dump(self, token):
		"""Dump an OAuth token to storage."""

	@abc.abstractmethod
	def load(self):
		"""Load an OAuth token from storage."""


class FileTokenHandler(TokenHandler):
	def dump(self, token, *, username=None, client=None):
		username = username or getattr(self, 'username', '')
		client = client or getattr(self, 'client', '')

		token_path = TOKEN_DIR / username / f'{client}.token'

		try:
			token_path.parent.mkdir(parents=True)
		except FileExistsError:
			pass

		with token_path.open('w') as f:
			json.dump(token, f)

		self.token = token
		self.token_path = token_path

	def load(self, username=None, client=None):
		username = username or getattr(self, 'username', '')
		client = client or getattr(self, 'client', '')

		token_path = TOKEN_DIR / username / f'{client}.token'

		try:
			token_path.parent.mkdir(parents=True)
		except FileExistsError:
			pass

		with token_path.open('r') as f:
			try:
				token = json.load(f)
			except json.JSONDecodeError:
				token = {}

		self.token = token
		self.token_path = token_path

		return self.token
