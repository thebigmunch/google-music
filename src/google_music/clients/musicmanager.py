__all__ = ['MusicManager']

import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import unquote
from uuid import getnode as get_mac

import audio_metadata
import google_music_proto.musicmanager.calls as mm_calls
from google_music_proto.musicmanager.pb import locker_pb2, upload_pb2
from google_music_proto.musicmanager.utils import transcode_to_mp3
from google_music_proto.oauth import (
	MUSICMANAGER_CLIENT_ID,
	MUSICMANAGER_CLIENT_SECRET,
	MUSICMANAGER_SCOPE,
)
from httpx.exceptions import HTTPError
from tenacity import stop_after_attempt

from .base import GoogleMusicClient
from ..utils import create_mac_string


class MusicManager(GoogleMusicClient):
	"""API wrapper class to access Google Music Music Manager functionality.

	>>> from google_music import MusicManager
	>>> mm = MusicManager('username')

	Parameters:
		username (str, Optional):
			Your Google Music username.
			Used to store OAuth tokens for multiple accounts separately.
		uploader_id (str, Optional):
			A unique uploader ID.
			Default: MAC address and username used.
		token (dict, Optional):
			An OAuth token compatible with ``oauthlib``.
	"""

	client = 'musicmanager'
	client_id = MUSICMANAGER_CLIENT_ID
	client_secret = MUSICMANAGER_CLIENT_SECRET
	oauth_scope = MUSICMANAGER_SCOPE

	def __init__(self, username=None, uploader_id=None, *, token=None):
		if self.login(username, token=token):
			if uploader_id is None:
				mac_int = get_mac()
				if (mac_int >> 40) % 2:
					raise OSError("A valid MAC address could not be obtained.")

				mac_string = create_mac_string(mac_int)

				if username:
					uploader_id = f"{mac_string}-{username}"
				else:
					uploader_id = mac_string

			uploader_name = (
				f"{socket.gethostname()} ({self.session.headers['User-Agent']})"
			)

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

		response = self._call(
			mm_calls.Export,
			self.uploader_id,
			song_id
		)
		audio = response.body
		suggested_filename = unquote(
			response.headers['Content-Disposition'].split("filename*=UTF-8''")[-1]
		)

		return (audio, suggested_filename)

	def quota(self):
		"""Get the uploaded track count and allowance.

		Returns:
			tuple: Number of uploaded tracks, number of tracks allowed.
		"""

		response = self._call(
			mm_calls.ClientState,
			self.uploader_id
		)
		client_state = response.body.clientstate_response

		return (client_state.total_track_count, client_state.locker_track_limit)

	def songs(self, *, uploaded=True, purchased=True):
		"""Get a listing of Music Library songs.

		Returns:
			list: Song dicts.
		"""

		if not uploaded and not purchased:
			raise ValueError("'uploaded' and 'purchased' cannot both be False.")

		if purchased and uploaded:
			song_list = []
			for chunk in self.songs_iter(export_type=1):
				song_list.extend(chunk)
		elif purchased:
			song_list = []
			for chunk in self.songs_iter(export_type=2):
				song_list.extend(chunk)
		elif uploaded:
			purchased_songs = []
			for chunk in self.songs_iter(export_type=2):
				purchased_songs.extend(chunk)

			song_list = [
				song
				for chunk in self.songs_iter(export_type=1)
				for song in chunk
				if song not in purchased_songs
			]

		return song_list

	def songs_iter(self, *, continuation_token=None, export_type=1):
		"""Get a paged iterator of Music Library songs.

		Parameters:
			continuation_token (str, Optional):
				The token of the page to return.
				Default: Not sent to get first page.
			export_type (int, Optional):
				The type of tracks to return.
				1 for all tracks,
				2 for promotional and purchased.
				Default: ``1``

		Yields:
			list: Song dicts.
		"""

		def track_info_to_dict(track_info):
			return {
				field.name: value
				for field, value in track_info.ListFields()
			}

		while True:
			response = self._call(
				mm_calls.ExportIDs,
				self.uploader_id,
				continuation_token=continuation_token,
				export_type=export_type,
			)

			items = [
				track_info_to_dict(track_info)
				for track_info in response.body.download_track_info
			]

			if items:
				yield items

			continuation_token = response.body.continuation_token

			if not continuation_token:
				break

	# TODO: Is there a better return value?
	# TODO: Can more of this code be moved into calls and still leave viable control flow?
	def upload(self, song, *, album_art_path=None, no_sample=False):
		"""Upload a song to a Google Music library.

		Parameters:
			song (os.PathLike or str or audio_metadata.Format):
				The path to an audio file or
				an instance of :class:`audio_metadata.Format`.
			album_art_path (os.PathLike or str, Optional):
				The relative filename or absolute filepath to external album art.
			no_sample(bool, Optional):
				Don't generate an audio sample from song;
				send empty audio sample.
				Default: Create an audio sample using ffmpeg/avconv.

		Returns:
			dict: A result dict with keys: ``'filepath'``, ``'success'``, ``'reason'``, and ``'song_id'`` (if successful).
		"""

		if not isinstance(song, audio_metadata.Format):
			try:
				song = audio_metadata.load(song)
			except audio_metadata.UnsupportedFormat:
				raise ValueError("'song' must be FLAC, MP3, or WAV.")

		if album_art_path:
			album_art_path = Path(album_art_path).resolve()

			if album_art_path.is_file():
				with album_art_path.open('rb') as image_file:
					external_art = image_file.read()
			else:
				external_art = None
		else:
			external_art = None

		result = {'filepath': Path(song.filepath)}

		track_info = mm_calls.Metadata.get_track_info(song)
		response = self._call(
			mm_calls.Metadata,
			self.uploader_id, [track_info]
		)

		metadata_response = response.body.metadata_response

		if metadata_response.signed_challenge_info:  # Sample requested.
			sample_request = metadata_response.signed_challenge_info[0]

			try:
				track_sample = mm_calls.Sample.generate_sample(
					song,
					track_info,
					sample_request,
					external_art=external_art,
					no_sample=no_sample,
				)
				response = self._call(
					mm_calls.Sample,
					self.uploader_id,
					[track_sample]
				)
				track_sample_response = response.body.sample_response.track_sample_response[
					0
				]
			except (OSError, ValueError, subprocess.CalledProcessError):
				raise  # TODO
		else:
			track_sample_response = metadata_response.track_sample_response[0]

		response_code = track_sample_response.response_code

		if response_code == upload_pb2.TrackSampleResponse.MATCHED:
			result.update(
				{
					'success': True,
					'reason': 'Matched',
					'song_id': track_sample_response.server_track_id,
				}
			)
		elif response_code == upload_pb2.TrackSampleResponse.UPLOAD_REQUESTED:
			server_track_id = track_sample_response.server_track_id

			self._call(
				mm_calls.UploadState,
				self.uploader_id,
				'START'
			)

			attempts = 0
			should_retry = True

			while should_retry and attempts <= 10:
				try:
					# Call with tenacity.retry_with to disable automatic retries.
					response = self._call.retry_with(stop=stop_after_attempt(1))(
						self,
						mm_calls.ScottyAgentPost,
						self.uploader_id,
						server_track_id,
						track_info,
						song,
						external_art=external_art,
						total_song_count=1,
						total_uploaded_count=0,
					)
				except HTTPError as e:
					should_retry = True
					reason = e.response
				else:
					session_response = response.body

					if 'sessionStatus' in session_response:
						break

					try:
						# WHY, GOOGLE?! WHY???????????
						status_code = session_response['errorMessage']['additionalInfo'][
							'uploader_service.GoogleRupioAdditionalInfo'
						]['completionInfo']['customerSpecificInfo']['ResponseCode']
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
				finally:
					attempts += 1
					time.sleep(2)  # Give the server time to sync.
			else:
				result.update(
					{
						'success': False,
						'reason': f'Could not get upload session: {reason}',
					}
				)

			if 'success' not in result:
				transfer = session_response['sessionStatus']['externalFieldTransfers'][0]

				upload_url = transfer['putInfo']['url']
				content_type = transfer.get('content_type', 'audio/mpeg')
				original_content_type = track_info.original_content_type

				transcode = (
					isinstance(song, audio_metadata.WAV)
					or original_content_type != locker_pb2.Track.MP3
				)

				if (
					transcode
					or original_content_type == locker_pb2.Track.MP3
				):
					if transcode:
						audio_file = transcode_to_mp3(song, quality='320k')
					else:
						with open(song.filepath, 'rb') as f:
							audio_file = f.read()

					# Google Music allows a maximum file size of 300 MiB.
					if len(audio_file) >= 300 * 1024 * 1024:
						result.update(
							{
								'success': False,
								'reason': 'Maximum allowed file size is 300 MiB.',
							}
						)
					else:
						upload_response = self._call(
							mm_calls.ScottyAgentPut,
							upload_url,
							audio_file,
							content_type=content_type,
						).body

						if upload_response.get('sessionStatus', {}).get('state'):
							result.update(
								{
									'success': True,
									'reason': 'Uploaded',
									'song_id': track_sample_response.server_track_id,
								}
							)
						else:
							result.update(
								{
									'success': False,
									'reason': upload_response,  # TODO: Better error details.
								}
							)
				else:
					# Do not upload files if transcode option set to False.
					result.update(
						{
							'success': False,
							'reason': 'Transcoding disabled for file type.',
						}
					)

				self._call(mm_calls.UploadState, self.uploader_id, 'STOPPED')
		else:
			response_codes = upload_pb2._TRACKSAMPLERESPONSE.enum_types[0]
			response_type = response_codes.values_by_number[
				track_sample_response.response_code
			].name

			reason = response_type

			result.update(
				{
					'success': False,
					'reason': f'{reason}'
				}
			)

			if response_type == 'ALREADY_EXISTS':
				result['song_id'] = track_sample_response.server_track_id

		return result
