==================
google-music
==================


google-music is an API wrapper for interacting with Google Music.


Getting Started
===============

Install google-music with `pip <https://pip.pypa.io/en/stable/>`_.

.. code-block:: console

	$ pip install google-music


Create a mobile or music manager client using the :ref:`api`.

.. code-block:: python

	>>> import google_music

	>>> mc = google_music.mobileclient()
	>>> mm = google_music.musicmanager()


See the :ref:`mobileclient` and :ref:`musicmanager` documentation for available functionality.


API Reference
=============

.. toctree::
	:maxdepth: 1

	api
	mobileclient
	musicmanager
