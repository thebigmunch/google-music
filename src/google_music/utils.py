__all__ = ['create_mac_string', 'is_valid_mac']

import re

mac_re = re.compile(r'^([\dA-F]{2}[:]){5}([\dA-F]{2})$')


def create_mac_string(mac_int):
	mac = hex(mac_int)[2:].upper()
	pad = max(12 - len(mac), 0)

	return mac + '0' * pad


def get_ple_prev_next(
	playlist_songs,
	*,
	after=None,
	before=None,
	index=None,
	position=None
):
	if (
		(after or before)
		and position
	):
			raise ValueError(
				"Must provide one or both of 'after'/'before' or one of 'index'/'position'."
			)

	if (
		index is not None
		and index not in range(-(len(playlist_songs)), len(playlist_songs) + 1)
	):
		raise ValueError(
			f"'index' must be between {-len(playlist_songs)} and {len(playlist_songs)}."
		)

	if (
		position is not None
		and position not in range(1, len(playlist_songs) + 2)
	):
		raise ValueError(
			f"'position' must be between 1 and {len(playlist_songs) + 1}."
		)

	prev = after or {}
	next_ = before or {}

	if prev or next_:
		if prev:
			index = playlist_songs.index(prev)
			if not next_ and prev != playlist_songs[-1]:
				index += 1
				next_ = playlist_songs[index]

		if next_:
			index = playlist_songs.index(next_)
			if not prev and next_ != playlist_songs[0]:
				prev = playlist_songs[index]
	else:
		if position is not None:
			if position == len(playlist_songs) + 1:
				index = len(playlist_songs)
			else:
				index = position - 1
		elif index is None or index == len(playlist_songs):
			index = len(playlist_songs)
		elif index < 0:
			index = index % len(playlist_songs)

		if index != 0:
			prev = playlist_songs[index - 1]

		if index != len(playlist_songs):
			next_ = playlist_songs[index]

	return prev, next_


def is_valid_mac(mac_string):
	return bool(mac_re.match(mac_string))
