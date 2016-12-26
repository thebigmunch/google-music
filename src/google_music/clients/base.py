import time

import requests
from google_music_proto.oauth import AUTHORIZATION_BASE_URL, REDIRECT_URI, TOKEN_URL
from tenacity import retry, stop_after_attempt, wait_exponential

from ..session import GoogleMusicSession, dump_token, load_token


# TODO: Configurable token updater/saver/loader.
class GoogleMusicClient():
	def _oauth(self, username, *, token=None):
		auto_refresh_kwargs = {
			'client_id': self.client_id,
			'client_secret': self.client_secret
		}

		self.session = GoogleMusicSession(
			client_id=self.client_id, scope=self.oauth_scope, redirect_uri=REDIRECT_URI,
			auto_refresh_url=TOKEN_URL, auto_refresh_kwargs=auto_refresh_kwargs,
			token_updater=self._update_token
		)

		if not token:
			try:
				token = load_token(username, self.client)
				token['expires_at'] = time.time() - 10

				self.session.token = token
			except FileNotFoundError:
				authorization_url, state = self.session.authorization_url(
					AUTHORIZATION_BASE_URL, access_type='offline', prompt='consent'
				)

				code = input(
					f"Visit:\n\n{authorization_url}\n\nFollow the prompts and paste provided code: "
				)
				token = self.session.fetch_token(TOKEN_URL, client_secret=self.client_secret, code=code)

		self.session.refresh_token(TOKEN_URL)
		self.token = token
		self._update_token(token)

	@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=10))
	def _call(self, call_cls, *args, **kwargs):
		call = call_cls(*args, **kwargs)

		# Override default hl/tier params from google-music-proto for Mobileclient.
		params = {**call.params, **self.session.params}

		response = self.session.request(
			call.method, call.url, headers=call.headers, data=call.body,
			params=params, allow_redirects=call.follow_redirects
		)

		try:
			response.raise_for_status()
		except requests.HTTPError:
			raise

		return call.parse_response(response.headers, response.content)

	def _update_token(self, token):
		dump_token(self.username, self.client, token)

	@property
	def is_authenticated(self):
		"""The authentication status of the client instance."""

		return self.session.authorized

	@property
	def username(self):
		"""The username associated with the client instance.

		This is used to store OAuth credentials for different accounts separately.
		"""

		return self._username

	def login(self, username='', *, token=None):
		"""Log in to Google Music.

		Parameters:
			username (str, Optional): Your Google Music username.
				Used for keeping stored OAuth tokens for multiple accounts separate.
			device_id (str, Optional): A mobile device ID or music manager uploader ID.
				Default: MAC address is used.
			token (dict, Optional): An OAuth token compatible with ``requests-oauthlib``.

		Returns:
			bool: ``True`` if successfully authenticated, ``False`` if not.
		"""

		self._username = username
		self._oauth(username, token=token)

		return self.is_authenticated

	# TODO: Revoke oauth token/delete oauth token file.
	def logout(self):
		"""Log out of Google Music."""

		self.session = None
		self._username = None

		return True

	# TODO Revoke oauth token/delete oauth token file.
	def switch_user(self, username='', *, token=None):
		"""Log in to Google Music with a different user.

		Parameters:
			username (str, Optional): Your Google Music username.
				Used for keeping stored OAuth tokens for multiple accounts separate.
			token (dict, Optional): An OAuth token compatible with ``requests-oauthlib``.

		Returns:
			bool: ``True`` if successfully authenticated, ``False`` if not.
		"""

		if self.logout():
			return self.login(username, token=token)

		return False
