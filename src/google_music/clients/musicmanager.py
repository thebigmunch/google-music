__all__ = ['MusicManager']

import os
import subprocess
import time
from socket import gethostname
from urllib.parse import unquote
from uuid import getnode as get_mac

import audio_metadata
import google_music_proto.musicmanager.calls as mm_calls
from google_music_proto.musicmanager.pb import locker_pb2, upload_pb2
from google_music_proto.musicmanager.utils import transcode_to_mp3
from google_music_proto.oauth import (
	MUSICMANAGER_CLIENT_ID, MUSICMANAGER_CLIENT_SECRET, MUSICMANAGER_SCOPE
)
from tenacity import stop_after_attempt

from .base import GoogleMusicClient
from ..utils import create_mac_string, is_valid_mac


class MusicManager(GoogleMusicClient):
	"""API wrapper class to access Google Music Music Manager functionality.

	>>> from google_music import MusicManager
	>>> mm = MusicManager('username')

	Parameters:
		username (str, Optional): Your Google Music username.
			This is used to store OAuth credentials for different accounts separately.
		uploader_id (str, Optional): A unique uploader ID. Default: MAC address incremented by 1 is used.
		token (dict, Optional): An OAuth token compatible with ``requests-oauthlib``.
	"""

	client = 'musicmanager'
	client_id = MUSICMANAGER_CLIENT_ID
	client_secret = MUSICMANAGER_CLIENT_SECRET
	oauth_scope = MUSICMANAGER_SCOPE

	def __init__(self, username='', uploader_id=None, *, token=None):
		if self.login(username, token=token):
			if uploader_id is None:
				mac_int = get_mac()

				if (mac_int >> 40) % 2:
					raise OSError("A valid MAC address could not be obtained.")
				else:
					mac_int = (mac_int + 1) % (1 << 48)

				mac_string = create_mac_string(mac_int)
				uploader_id = ':'.join(mac_string[x:x + 2] for x in range(0, 12, 2))

			if not is_valid_mac(uploader_id):
				raise ValueError("uploader_id must be a valid MAC address.")

			uploader_name = f"{gethostname()} ({self.session.headers['User-Agent']})"

			self._upauth(uploader_id, uploader_name)

	def __repr__(self):
		return f"MusicManager(username={self.username!r}, uploader_id={self.uploader_id}, token={self.token})"

	def _upauth(self, uploader_id, uploader_name):
		self._call(mm_calls.UpAuth, uploader_id, uploader_name)

		self._uploader_id = uploader_id
		self._uploader_name = uploader_name

	@property
	def uploader_id(self):
		"""The uploader ID of the :class:`MusicManager` instance."""

		return self._uploader_id

	@property
	def uploader_name(self):
		"""The uploader name of the :class:`MusicManager` instance."""

		return self._uploader_name

	def download(self, song):
		"""Download a song from a Google Music library.

		Parameters:
			song (dict): A song dict.

		Returns:
			tuple: Song content as bytestring, suggested filename.
		"""

		song_id = song['id']

		response = self._call(mm_calls.Export, self.uploader_id, song_id)
		audio = response.body
		suggested_filename = unquote(response.headers['Content-Disposition'].split("filename*=UTF-8''")[-1])

		return (audio, suggested_filename)

	def quota(self):
		"""Get the uploaded track count and allowance.

		Returns:
			tuple: Number of uploaded tracks, number of tracks allowed.
		"""

		response = self._call(mm_calls.ClientState, self.uploader_id)
		client_state = response.body.clientstate_response

		return (client_state.total_track_count, client_state.locker_track_limit)

	def songs(self, *, uploaded=True, purchased=True):
		"""Get a listing of Music Library songs.

		Returns:
			list: Song dicts.
		"""

		if not uploaded and not purchased:
			raise ValueError("'uploaded' and 'purchased' cannot both be False.")

		song_list = []

		if purchased and uploaded:
			song_list = [song for chunk in self.songs_iter(export_type=1) for song in chunk]
		if purchased and not uploaded:
			song_list = [song for chunk in self.songs_iter(export_type=2) for song in chunk]
		elif uploaded and not purchased:
			all_songs = [song for chunk in self.songs_iter(export_type=1) for song in chunk]
			purchased_songs = [song for chunk in self.songs_iter(export_type=2) for song in chunk]

			song_list = [song for song in all_songs if song not in purchased_songs]

		return song_list

	def songs_iter(self, *, continuation_token=None, export_type=1):
		"""Get a paged iterator of Music Library songs.

		Parameters:
			continuation_token (str, Optional): The token of the page to return.
				Default: Not sent to get first page.
			export_type (int, Optional): The type of tracks to return. 1 for all tracks, 2 for promotional and purchased.
				Default: ``1``

		Yields:
			list: Song dicts.
		"""

		def track_info_to_dict(track_info):
			return dict((field.name, value) for field, value in track_info.ListFields())

		while True:
			response = self._call(mm_calls.ExportIDs, self.uploader_id, continuation_token=continuation_token, export_type=export_type)

			items = [track_info_to_dict(track_info) for track_info in response.body.download_track_info]

			if items:
				yield items

			continuation_token = response.body.continuation_token

			if not continuation_token:
				break

	# TODO: Is there a better return value?
	# TODO: Can more of this code be moved into calls and still leave viable control flow?
	def upload(self, song, *, album_art_path=None, transcode_lossless=True, transcode_lossy=True, transcode_quality='320k'):
		"""Upload a song to a Google Music library.

		Parameters:
			song (os.PathLike or str or audio_metadata.Format): The path to an audio file or an instance of :class:`audio_metadata.Format`.
			album_art_path (str or list, Optional): The absolute or relative path to external album art file.
				If relative, can be a list of file names to check in the directory of the music file.
			transcode_lossless (bool, Optional): Transcode lossless files to upload as MP3.
				Default: ``True``
			transcode_lossy (bool, Optional): Transcode lossy files to upload as MP3.
				Default: ``True``
			transcode_quality (str or int, Optional): Transcode quality option to pass to ffmpeg/avconv.
				See `ffmpeg documentation <https://trac.ffmpeg.org/wiki/Encode/MP3#VBREncoding>`__ for examples.
				Default: ``'320k'``

		Returns:
			dict: A result dict with keys: ``'filepath'``, ``'success'``, ``'reason'``, and ``'song_id'`` (if successful).
		"""

		if not isinstance(song, audio_metadata.Format):
			try:
				song = audio_metadata.load(song)
			except audio_metadata.UnsupportedFormat:
				raise ValueError("'song' must be FLAC, MP3, or WAV.")

		if album_art_path is not None:
			with open(album_art_path, 'rb') as image_file:
				external_art = image_file.read()
		else:
			external_art = None

		if isinstance(album_art_path, list):
			base_dir = os.path.dirname(song.filepath)

			try:
				rel_path = next(path for path in album_art_path if os.path.isfile(os.path.join(base_dir, path)))
				album_art_path = os.path.join(base_dir, rel_path)
			except StopIteration:
				album_art_path = None

		result = {'filepath': song.filepath}

		track_info = mm_calls.Metadata.get_track_info(song)
		response = self._call(mm_calls.Metadata, self.uploader_id, [track_info])

		metadata_response = response.body.metadata_response

		if metadata_response.signed_challenge_info:  # Sample requested.
			sample_request = metadata_response.signed_challenge_info[0]

			try:
				track_sample = mm_calls.Sample.generate_sample(song, track_info, sample_request, external_art=external_art)
				response = self._call(mm_calls.Sample, self.uploader_id, [track_sample])
				track_sample_response = response.body.sample_response.track_sample_response[0]
			except (OSError, ValueError, subprocess.CalledProcessError) as e:
				raise  # TODO
		else:
			track_sample_response = metadata_response.track_sample_response[0]

		response_code = track_sample_response.response_code

		if response_code == upload_pb2.TrackSampleResponse.MATCHED:
			result.update({
				'success': True,
				'reason': 'Matched',
				'song_id': track_sample_response.server_track_id
			})
		elif response_code == upload_pb2.TrackSampleResponse.UPLOAD_REQUESTED:
			server_track_id = track_sample_response.server_track_id

			self._call(mm_calls.UploadState, self.uploader_id, 'START')

			attempts = 0
			should_retry = True

			while should_retry and attempts <= 10:
				# Call with tenacity.retry_with to disable automatic retries.
				response = self._call.retry_with(stop=stop_after_attempt(1))(
					self, mm_calls.ScottyAgentPost, self.uploader_id, server_track_id,
					track_info, song, external_art=external_art, total_song_count=1, total_uploaded_count=0
				)

				session_response = response.body

				if 'sessionStatus' in session_response:
					break

				try:
					status_code = session_response['errorMessage']['additionalInfo']['uploader_service.GoogleRupioAdditionalInfo']['completionInfo']['customerSpecificInfo']['ResponseCode']  # noqa
				except KeyError:
					status_code = None

				if status_code == 503:  # Upload server still syncing.
					should_retry = True
					reason = "Server syncing"
				elif status_code == 200:  # Song is already uploaded.
					should_retry = False
					reason = "Already uploaded"
				elif status_code == 404:  # Rejected.
					should_retry = False
					reason = "Rejected"
				else:
					should_retry = True
					reason = "Unkown error"

				attempts += 1

				time.sleep(2)  # Give the server time to sync.
			else:
				result.update({
					'success': False,
					'reason': f'Could not get upload session: {reason}'
				})

			if 'success' not in result:
				transfer = session_response['sessionStatus']['externalFieldTransfers'][0]

				upload_url = transfer['putInfo']['url']
				content_type = transfer.get('content_type', 'audio/mpeg')
				original_content_type = track_info.original_content_type

				transcode = isinstance(song, (audio_metadata.FLAC, audio_metadata.WAV)) and transcode_lossless

				if transcode or original_content_type == locker_pb2.Track.MP3 or (original_content_type == locker_pb2.Track.FLAC and not transcode_lossless):
					if transcode:
						audio_file = transcode_to_mp3(song)
						content_type = 'audio/mpeg'
					else:
						with open(song.filepath, 'rb') as f:
							audio_file = f.read()

					upload_response = self._call(mm_calls.ScottyAgentPut, upload_url, audio_file, content_type=content_type).body

					if upload_response.get('sessionStatus', {}).get('state'):
						result.update({
							'success': True,
							'reason': 'Uploaded',
							'song_id': track_sample_response.server_track_id
						})
					else:
						result.update({
							'success': False,
							'reason': upload_response,  # TODO: Better error details.
						})
				else:
					# Do not upload files if transcode option set to False.
					result.update({
						'success': False,
						'reason': 'Transcoding disabled for file type.'
					})

				self._call(mm_calls.UploadState, self.uploader_id, 'STOPPED')
		else:
			response_codes = upload_pb2._TRACKSAMPLERESPONSE.enum_types[0]
			response_type = response_codes.values_by_number[track_sample_response.response_code].name

			reason = response_type

			result.update({
				'success': False,
				'reason': f'{reason}'
			})

			if response_type == 'ALREADY_EXISTS':
				result['song_id'] = track_sample_response.server_track_id

		return result
