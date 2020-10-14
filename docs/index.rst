google-music --- A Google Music API library
===========================================

**Due to Google Music shutting down in favor of YouTube Music, this project has ended.****Due to Google Music shutting down in favor of YouTube Music, this project has ended.**


Getting Started
---------------

Install google-music with `pip <https://pip.pypa.io/en/stable/>`_.

.. code-block:: console

	$ pip install google-music


Create a mobile or music manager client using the high-level API.

.. code-block:: python

	>>> import google_music

	>>> mc = google_music.mobileclient()
	>>> mm = google_music.musicmanager()

.. toctree::
	:hidden:

	api
	mobileclient
	musicmanager
	sessions
	token-handlers
