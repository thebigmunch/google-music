# Change Log

## [Unreleased](https://github.com/thebigmunch/google-music/tree/master)

[Commits](https://github.com/thebigmunch/google-music/compare/1.0.0...master)

### Changed

* Return plain dict from Mobileclient.search.
  This was mistakenly left as defaultdict.
* Only return item dicts from search results.
  Previously, entire search result with metadata was returned.


## [1.0.0](https://github.com/thebigmunch/google-music/releases/tag/1.0.0) (2018-10-19)

[Commits](https://github.com/thebigmunch/google-music/commit/b3924b728cb73b9d354e1ff4f520411fd8d1b987)

* Initial release.
