# Change Log

Notable changes to this project based on the [Keep a Changelog](https://keepachangelog.com) format.
This project adheres to [Semantic Versioning](https://semver.org).


## [Unreleased](https://github.com/thebigmunch/google-music/tree/master)

[Commits](https://github.com/thebigmunch/google-music/compare/1.0.0...master)

### Added

* Add ``playlist_entries_iter`` method to ``MobileClient``.
* Add ``playlists_iter`` method to ``MobileClient``.
* Add ``podcasts_iter`` method to ``MobileClient``.
* Add ``podcast_episdode_iter`` method to ``MobileClient``.
* ``generated`` and ``library`` parameters to ``MobileClient.stations``
  to control returned station types.

### Changed

* Refactor ``MobileClient.playlist_entries`` to match ``MobileClient.songs`` impelementation.
* Rename ``MobileClient.playlist_feed`` to ``MobileClient.playlists``.
* Refactor ``MobileClient.playlists`` to match ``MobileClient.songs`` impelementation.
* Refactor ``MobileClient.podcasts`` to match ``MobileClient.songs`` impelementation.
* Refactor ``MobileClient.podcast_episodes`` to match ``MobileClient.songs`` impelementation.
* Change ``MobileClient.songs`` to use ``TrackFeed`` call instead of ``Tracks``.
* Refactor ``MobileClient.stations`` to match ``MobileClient.songs`` impelementation.
* Rename ``Mobileclient.listen_now_situations`` to ``situations``.

### Removed

* ``MobileClient.song_feed``.
* ``MobileClient.song_feed_iter``.
* ``only_library`` parameter from ``MobileClient.station``.
* ``only_library`` parameter from ``MobileClient.stations``.


## [1.1.0](https://github.com/thebigmunch/google-music/releases/tag/1.1.0) (2018-10-20)

[Commits](https://github.com/thebigmunch/google-music/compare/1.0.0...1.1.0)

### Added

* Add support for rating store and playlist songs.
* Add ``Mobileclient.song_play`` for incrementing song play counts.

### Changed

* Return plain dict from ``Mobileclient.search``.
  This was mistakenly left as defaultdict.
* Only return item dicts from search results.
  Previously, entire search result with metadata was returned.
* Add return value for ``Mobileclient.song_rate``.
  ``True`` if successful, ``False`` if not.


## [1.0.0](https://github.com/thebigmunch/google-music/releases/tag/1.0.0) (2018-10-19)

[Commits](https://github.com/thebigmunch/google-music/commit/b3924b728cb73b9d354e1ff4f520411fd8d1b987)

* Initial release.
