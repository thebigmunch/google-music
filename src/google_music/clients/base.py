import time

from tenacity import retry, stop_after_attempt, wait_exponential

from ..sessions import GoogleMusicSession
from ..token_handlers import FileTokenHandler

try:
	from httpx import HTTPError as RequestError
except ImportError:
	from httpx import RequestError


# TODO: Configurable token updater/saver/loader.
class GoogleMusicClient:
	def __init__(
		self,
		username,
		*,
		session=None,
		token=None,
		token_handler=FileTokenHandler,
		token_handler_kwargs=None
	):
		self._username = username or ''

		if token_handler_kwargs is None:
			token_handler_kwargs = {}

		self._token_handler = token_handler(
			username=self._username,
			client=self.client,
			**token_handler_kwargs
		)

		self._session = (
			session
			or GoogleMusicSession(
				self.client_id,
				self.client_secret,
				self.oauth_scope,
				token=token
			)
		)

	@property
	def is_authenticated(self):
		"""The authentication status of the client instance."""

		return self._session.authorized

	@property
	def token(self):
		return self._session.token

	@token.setter
	def token(self, token):
		self._session.token = token

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
		params = {**call.params, **self._session.params}

		response = self._session.request(
			call.method,
			call.url,
			headers=call.headers,
			data=call.body,
			params=params,
			allow_redirects=call.follow_redirects
		)

		self._token_handler.dump(self.token)

		try:
			response.raise_for_status()
		except RequestError:
			raise

		return call.parse_response(response.headers, response.content)

	def login(self):
		"""Log in to Google Music.

		Parameters:
			username (str, Optional):
				Your Google Music username.
				Used to store OAuth tokens for multiple accounts separately.
			token (dict, Optional):
				An OAuth token compatible with ``oauthlib``.

		Returns:
			bool: ``True`` if successfully authenticated, ``False`` if not.
		"""

		if not self.token:
			try:
				token = self._token_handler.load()
				token['expires_at'] = time.time() - 10
				self.token = token
			except FileNotFoundError:
				authorization_url = self._session.authorization_url()

				code = input(
					f"Visit:\n\n{authorization_url}\n\n"
					"Follow the prompts and paste provided code: "
				)

				self._session.fetch_token(code)

		self._session.refresh_token()
		self._token_handler.dump(self.token)

		return self.is_authenticated

	# TODO: Revoke oauth token/delete oauth token file.
	def logout(self):
		"""Log out of Google Music."""

		self._session.close()
		self._session = None
		self._username = None
		self._token_handler = None

		try:
			delattr('_uploader_id')
			delattr('_uploader_name')
		except AttributeError:
			pass

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
