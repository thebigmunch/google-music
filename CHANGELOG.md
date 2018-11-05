# Change Log

Notable changes to this project based on the [Keep a Changelog](https://keepachangelog.com) format.
This project adheres to [Semantic Versioning](https://semver.org).


## [Unreleased](https://github.com/thebigmunch/google-music/tree/master)

[Commits](https://github.com/thebigmunch/google-music/compare/2.0.0...master)



## [2.0.0](https://github.com/thebigmunch/google-music/releases/tag/2.0.0) (2018-11-05)

[Commits](https://github.com/thebigmunch/google-music/compare/1.1.0...2.0.0)

### Added

* ``MobileClient.playlist_entries_iter``
* ``MobileClient.playlists_iter``
* ``MobileClient.podcasts_iter``
* ``MobileClient.podcast_episdode_iter``
* ``generated`` and ``library`` parameters to ``MobileClient.stations``
  to control returned station types.
* ``MobileClient.new_releases`` to get explore tab new releases.
* Support for I'm Feeling Lucky Radio.
* ``MobileClient.playlist_delete``
* ``library`` and ``store`` parameters to ``MobileClient.thumbs_up_songs``.
* ``MobileClient.search_google``
* ``MobileClient.search_library``

### Changed

* Refactor ``MobileClient.playlist_entries`` to match ``MobileClient.songs`` impelementation.
* Rename ``MobileClient.playlist_feed`` to ``MobileClient.playlists``.
* Refactor ``MobileClient.playlists`` to match ``MobileClient.songs`` impelementation.
* Refactor ``MobileClient.podcasts`` to match ``MobileClient.songs`` impelementation.
* Refactor ``MobileClient.podcast_episodes`` to match ``MobileClient.songs`` impelementation.
* ``MobileClient.songs`` now uses ``TrackFeed`` call instead of ``Tracks``.
* Refactor ``MobileClient.stations`` to match ``MobileClient.songs`` impelementation.
* Rename ``MobileClient.listen_now_situations`` to ``situations``.
* Rename ``MobileClient.browse_top_chart`` to ``top_charts``.
* Rename ``MobileClient.browse_top_chart_genres`` to ``top_charts_genres``.
* Rename ``MobileClient.browse_top_chart_for_genre`` to ``top_charts_for_genre``.
* ``MobileClient.explore_tabs`` now returns dict with lowercased keys.
* ``MobileClient.listen_now_items`` now returns a dict with ``albums`` and ``stations``
  keys containing those types of listen now items.
* Rename ``MobileClient.browse_station_categories`` to ``browse_stations_categories``.
* Rename ``MobileClient.browse_podcast_genres`` to ``browse_podcasts_genres``.
* Rename ``MobileClient.delete_song(s)`` to ``song(s)_delete``.
* Rename ``MobileClient.promoted_songs`` to ``thumbs_up_songs``.
* ``MobileClient.thumbs_up_songs`` now returns both
  library and store 'Thumbs Up' songs.
* Rename ``MobileClient.add_store_song(s)`` to ``song(s)_add``.
* ``MobileClient.search`` now returns results from both
  Google Music and user's library as done in the official client.

### Removed

* ``MobileClient.song_feed``.
* ``MobileClient.song_feed_iter``.
* ``only_library`` parameter from ``MobileClient.station``.
* ``only_library`` parameter from ``MobileClient.stations``.


## [1.1.0](https://github.com/thebigmunch/google-music/releases/tag/1.1.0) (2018-10-20)

[Commits](https://github.com/thebigmunch/google-music/compare/1.0.0...1.1.0)

### Added

* Support for rating store and playlist songs.
* ``Mobileclient.song_play`` for incrementing song play counts.

### Changed

* Return plain dict from ``Mobileclient.search``.
  This was mistakenly left as defaultdict.
* Only return item dicts from search results.
  Previously, entire search result with metadata was returned.
* Return value for ``Mobileclient.song_rate``.
  ``True`` if successful, ``False`` if not.


## [1.0.0](https://github.com/thebigmunch/google-music/releases/tag/1.0.0) (2018-10-19)

[Commits](https://github.com/thebigmunch/google-music/commit/b3924b728cb73b9d354e1ff4f520411fd8d1b987)

* Initial release.
