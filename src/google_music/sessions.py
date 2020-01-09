__all__ = [
	'GoogleMusicSession',
]

import httpx
from google_music_proto.oauth import AUTHORIZATION_BASE_URL, REDIRECT_URI, TOKEN_URL
from oauthlib.common import generate_token, urldecode
from oauthlib.oauth2 import TokenExpiredError, WebApplicationClient

from .__about__ import __title__, __version__


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
		**kwargs
	):
		# httpx sets a default timeout on the Client class.
		# requests did not.
		# Disable timeout by default as too low a value
		# can cause issues with upload calls.
		timeout = kwargs.pop('timeout', None)
		super().__init__(timeout=timeout, **kwargs)

		self.params = {}
		self.headers.update(
			{'User-Agent': f'{__title__}/{__version__}'}
		)

		self.client_id = client_id
		self.client_secret = client_secret
		self.scope = scope

		self.token = token or {}
		self.oauth_client = WebApplicationClient(self.client_id, token=self.token)

	@property
	def access_token(self):
		return self.token.get('access_token')

	@property
	def authorized(self):
		return bool(self.access_token)

	def authorization_url(self):
		state = generate_token()

		return (
			self.oauth_client.prepare_request_uri(
				self.authorization_base_url,
				redirect_uri=self.redirect_uri,
				scope=self.scope,
				state=state,
				access_type='offline',
				prompt='select_account'
			)
		)

	def fetch_token(self, code):
		body = self.oauth_client.prepare_request_body(
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
			auth=httpx.BasicAuth(self.client_id, self.client_secret)
		)

		self.token = self.oauth_client.parse_request_body_response(response.text, scope=self.scope)

		return self.token

	def refresh_token(self):
		refresh_token = self.token.get('refresh_token')

		body = self.oauth_client.prepare_refresh_body(
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
			auth=httpx.BasicAuth(self.client_id, self.client_secret),
			withhold_token=True
		)

		self.token = self.oauth_client.parse_request_body_response(response.text, scope=self.scope)
		if 'refresh_token' not in self.token:
			self.token['refresh_token'] = refresh_token

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
				url, headers, data = self.oauth_client.add_token(
					url,
					http_method=method,
					body=data,
					headers=headers
				)
			except TokenExpiredError:
				self.refresh_token()
				url, headers, data = self.oauth_client.add_token(
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
