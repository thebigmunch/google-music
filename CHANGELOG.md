# Change Log

Notable changes to this project based on the [Keep a Changelog](https://keepachangelog.com) format.
This project adheres to [Semantic Versioning](https://semver.org).


## [Unreleased](https://github.com/thebigmunch/google-music/tree/master)

[Commits](https://github.com/thebigmunch/google-music/compare/1.0.0...master)

### Added

* Add support for rating store and playlist songs.
* Add Mobileclient.song_play for incrementing song play counts.

### Changed

* Return plain dict from Mobileclient.search.
  This was mistakenly left as defaultdict.
* Only return item dicts from search results.
  Previously, entire search result with metadata was returned.
* Add return value for Mobileclient.song_rate.
  ``True`` if successful, ``False`` of not.


## [1.0.0](https://github.com/thebigmunch/google-music/releases/tag/1.0.0) (2018-10-19)

[Commits](https://github.com/thebigmunch/google-music/commit/b3924b728cb73b9d354e1ff4f520411fd8d1b987)

* Initial release.
