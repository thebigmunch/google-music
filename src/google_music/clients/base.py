import json
import time
from pathlib import Path

import appdirs
import httpx
from google_music_proto.oauth import AUTHORIZATION_BASE_URL, REDIRECT_URI, TOKEN_URL
from httpx.middleware.basic_auth import BasicAuthMiddleware as HTTPBasicAuth
from oauthlib.common import generate_token, urldecode
from oauthlib.oauth2 import TokenExpiredError, WebApplicationClient
from tenacity import retry, stop_after_attempt, wait_exponential

from ..__about__ import __author__, __title__, __version__

TOKEN_DIR = Path(appdirs.user_data_dir(__title__, __author__))


# Adapted from requests-oauthlib for use with httpx.
class GoogleMusicSession(httpx.Client):
	authorization_base_url = AUTHORIZATION_BASE_URL
	redirect_uri = REDIRECT_URI
	token_url = TOKEN_URL

	def __init__(
		self,
		client_id,
		client_secret,
		scope,
		*,
		token=None,
		token_updater=None,
		**kwargs
	):
		# httpx sets a default timeout on the Client class.
		# requests did not.
		# Disable timeout by default as too low a value
		# can cause issues with upload calls.
		timeout = kwargs.pop('timeout', None)
		super().__init__(http_versions=['HTTP/1.1'], timeout=timeout, **kwargs)

		self.params = {}
		self.headers.update(
			{'User-Agent': f'{__title__}/{__version__}'}
		)

		self.client_id = client_id
		self.client_secret = client_secret
		self.scope = scope

		self.token = token or {}
		self.token_updater = token_updater

		self._client = WebApplicationClient(self.client_id, token=self.token)

	@property
	def access_token(self):
		return self.token.get('access_token')

	@property
	def authorized(self):
		return bool(self.access_token)

	def authorization_url(self):
		state = generate_token()

		return (
			self._client.prepare_request_uri(
				self.authorization_base_url,
				redirect_uri=self.redirect_uri,
				scope=self.scope,
				state=state,
				access_type='offline',
				prompt='select_account'
			)
		)

	def fetch_token(self, code):
		body = self._client.prepare_request_body(
			code=code,
			body='',
			redirect_uri=self.redirect_uri,
			include_client_id=None
		)

		response = self.request(
			'POST',
			self.token_url,
			headers={
				'Accept': 'application/json',
				'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
			},
			data=dict(urldecode(body)),
			auth=HTTPBasicAuth(self.client_id, self.client_secret),
			verify=True
		)

		self.token = self._client.parse_request_body_response(response.text, scope=self.scope)
		self.token_updater(self.token)

		return self.token

	def refresh_token(self):
		refresh_token = self.token.get('refresh_token')

		body = self._client.prepare_refresh_body(
			body='',
			refresh_token=refresh_token,
			scope=self.scope,
			client_id=self.client_id,
			client_secret=self.client_secret
		)

		response = self.request(
			'POST',
			self.token_url,
			headers={
				'Accept': 'application/json',
				'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
			},
			data=dict(urldecode(body)),
			auth=HTTPBasicAuth(self.client_id, self.client_secret),
			verify=True,
			withhold_token=True
		)

		self.token = self._client.parse_request_body_response(response.text, scope=self.scope)
		if 'refresh_token' not in self.token:
			self.token['refresh_token'] = refresh_token

		self.token_updater(self.token)

		return self.token

	def request(
		self,
		method,
		url,
		data=None,
		headers=None,
		withhold_token=False,
		**kwargs
	):
		if self.token and not withhold_token:
			try:
				url, headers, data = self._client.add_token(
					url,
					http_method=method,
					body=data,
					headers=headers
				)
			except TokenExpiredError:
				self.refresh_token()
				url, headers, data = self._client.add_token(
					url,
					http_method=method,
					body=data,
					headers=headers
				)

		return super().request(
			method,
			url,
			headers=headers,
			data=data,
			**kwargs
		)


# TODO: Configurable token updater/saver/loader.
class GoogleMusicClient:
	@property
	def is_authenticated(self):
		"""The authentication status of the client instance."""

		return self.session.authorized

	@property
	def token(self):
		return self.session.token

	@token.setter
	def token(self, token):
		self.session.token = token

	@property
	def username(self):
		"""The username associated with the client instance.

		This is used to store OAuth credentials for different accounts separately.
		"""

		return self._username

	@retry(
		reraise=True,
		stop=stop_after_attempt(5),
		wait=wait_exponential(multiplier=1, max=10),
	)
	def _call(self, call_cls, *args, **kwargs):
		call = call_cls(*args, **kwargs)

		# Override default hl/tier params from google-music-proto for Mobileclient.
		params = {**call.params, **self.session.params}

		response = self.session.request(
			call.method,
			call.url,
			headers=call.headers,
			data=call.body,
			params=params,
			allow_redirects=call.follow_redirects
		)

		try:
			response.raise_for_status()
		except httpx.HTTPError:
			raise

		return call.parse_response(response.headers, response.content)

	def _oauth(self):
		if not self.token:
			try:
				token_path = TOKEN_DIR / self.username / f'{self.client}.token'

				with token_path.open('r') as f:
					token = json.load(f)

				token['expires_at'] = time.time() - 10
				self.token = token
			except FileNotFoundError:
				authorization_url = self.session.authorization_url()

				code = input(
					f"Visit:\n\n{authorization_url}\n\n"
					"Follow the prompts and paste provided code: "
				)

				self.session.fetch_token(code)

		self.session.refresh_token()

	def _update_token(self, token=None):
		token = token or self.token

		token_path = TOKEN_DIR / self.username / f'{self.client}.token'

		try:
			token_path.parent.mkdir(parents=True)
		except FileExistsError:
			pass

		with token_path.open('w') as f:
			json.dump(token, f)

		self.token = token

	def login(self, username, *, token=None, session=None):
		"""Log in to Google Music.

		Parameters:
			username (str, Optional):
				Your Google Music username.
				Used to store OAuth tokens for multiple accounts separately.
			token (dict, Optional):
				An OAuth token compatible with ``oauthlib``.
			session (GoogleMusicSession, Optional):
				A session compatible with :class:`GoogleMusicSession`.

		Returns:
			bool: ``True`` if successfully authenticated, ``False`` if not.
		"""

		self._username = username or ''
		self.session = (
			session
			or GoogleMusicSession(
				self.client_id,
				self.client_secret,
				self.oauth_scope,
				token=token,
				token_updater=self._update_token
			)
		)

		self._oauth()

		return self.is_authenticated

	# TODO: Revoke oauth token/delete oauth token file.
	def logout(self):
		"""Log out of Google Music."""

		self.session.close()
		self.session = None
		self._username = None

		return True

	# TODO Revoke oauth token/delete oauth token file.
	def switch_user(self, username='', *, token=None):
		"""Log in to Google Music with a different user.

		Parameters:
			username (str, Optional):
				Your Google Music username.
				Used to store OAuth tokens for multiple accounts separately.
			token (dict, Optional):
				An OAuth token compatible with ``oauthlib``.

		Returns:
			bool: ``True`` if successfully authenticated, ``False`` if not.
		"""

		if self.logout():
			return self.login(username, token=token)

		return False
