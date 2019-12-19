__all__ = [
	'mobileclient',
	'musicmanager',
]

from .clients import MobileClient, MusicManager
from .token_handlers import FileTokenHandler


def mobileclient(
	username=None,
	device_id=None,
	*,
	locale='en_US',
	session=None,
	token=None,
	token_handler=FileTokenHandler,
	token_handler_kwargs=None
):
	"""Create and authenticate a Google Music mobile client.

	>>> import google_music
	>>> mc = google_music.mobileclient('username')

	Parameters:
		username (str, Optional):
			Your Google Music username.
			Used to store OAuth tokens for multiple accounts separately.
		device_id (str, Optional):
			A mobile device ID.
			Default: MAC address is used.
		locale (str, Optional):
			`ICU <http://www.localeplanet.com/icu/>`__
			locale used to localize some responses.
			This must be a locale supported by Android.
			Default: ``'en_US'``.
		session (:class:`~google_music.GoogleMusicSession`, Optional):
			A session compatible with :class:`GoogleMusicSession`.
		token (dict, Optional):
			An OAuth token compatible with ``oauthlib``.
		token_handler (:class:`~google_music.TokenHandler`, Optional):
			A token handler class compatible with :class:`TokenHandler`
			for dumping and loading the OAuth token.
		token_handler_kwargs (dict, Optional):
			Keyword arguments to pass to the ``token_handler``
			class. These become attributes on the class instance.

	Returns:
		MobileClient: An authenticated :class:`~google_music.MobileClient` instance.
	"""

	return MobileClient(
		username,
		device_id,
		locale=locale,
		session=session,
		token=token,
		token_handler=FileTokenHandler,
		token_handler_kwargs=None
	)


def musicmanager(
	username=None,
	uploader_id=None,
	*,
	session=None,
	token=None,
	token_handler=FileTokenHandler,
	token_handler_kwargs=None
):
	"""Create and authenticate a Google Music Music Manager client.

	>>> import google_music
	>>> mm = google_music.musicmanager('username')

	Parameters:
		username (str, Optional):
			Your Google Music username.
			Used to store OAuth tokens for multiple accounts separately.
		uploader_id (str, Optional):
			A unique uploader ID.
			Default: MAC address and username used.
		session (:class:`~google_music.GoogleMusicSession`, Optional):
			A session compatible with :class:`GoogleMusicSession`.
		token (dict, Optional):
			An OAuth token compatible with ``oauthlib``.
		token_handler (:class:`~google_music.TokenHandler`, Optional):
			A token handler class compatible with :class:`TokenHandler`
			for dumping and loading the OAuth token.
		token_handler_kwargs (dict, Optional):
			Keyword arguments to pass to the ``token_handler``
			class. These become attributes on the class instance.

	Returns:
		MusicManager: An authenticated :class:`~google_music.MusicManager` instance.
	"""

	return MusicManager(
		username,
		uploader_id,
		session=session,
		token=token,
		token_handler=FileTokenHandler,
		token_handler_kwargs=None
	)
