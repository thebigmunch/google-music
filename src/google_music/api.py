__all__ = [
	'mobileclient',
	'musicmanager',
]

from .clients import MobileClient, MusicManager


def mobileclient(
	username=None,
	device_id=None,
	*,
	token=None,
	locale='en_US'
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
		token (dict, Optional):
			An OAuth token compatible with ``oauthlib``.
		locale (str, Optional):
			`ICU <http://www.localeplanet.com/icu/>`__
			locale used to localize some responses.
			This must be a locale supported by Android.
			Default: ``'en_US'``.

	Returns:
		MobileClient: An authenticated :class:`~google_music.MobileClient` instance.
	"""

	return MobileClient(
		username,
		device_id,
		token=token,
		locale=locale
	)


def musicmanager(
	username=None,
	uploader_id=None,
	*,
	token=None
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
		token (dict, Optional):
			An OAuth token compatible with ``oauthlib``.

	Returns:
		MusicManager: An authenticated :class:`~google_music.MusicManager` instance.
	"""

	return MusicManager(username, uploader_id, token=token)
