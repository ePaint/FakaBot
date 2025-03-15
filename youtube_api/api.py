import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse, parse_qs

import yt_dlp

from datetime import datetime, timedelta
from pyyoutube import Client
from logger import logger
from settings import SETTINGS
from youtube_api.models import Video


class YoutubeApi:
    def __init__(self, api_key: str, client_id: str, client_secret: str, refresh_token: str, channel_id: str):
        self.channel_id = channel_id
        self.api_key_client = Client(api_key=api_key)
        self.oauth_client = Client(client_id=client_id, client_secret=client_secret)
        # print(self.oauth_client.get_authorize_url())
        # print(self.oauth_client.generate_access_token(code='4/0AQSTgQEyc6ssBCM6K9zdF7W1WlCxhkhcxP8CQefPOhxTu3edhU2Jm1517ajJH885u2VNkQ'))
        # exit()
        self.refresh_token = refresh_token
        self.access_token = None
        self.expire_datetime = None
        self.downloads_cache_path = Path('youtube_api/cache/downloads')
        self.access_token_cache_file = Path('youtube_api/cache/access_token.json')
        self.read_access_token()

    def read_access_token(self):
        try:
            logger.info('Reading access token from file')
            data = json.loads(self.access_token_cache_file.read_text())
            self.access_token = data['access_token']
            self.expire_datetime = datetime.fromisoformat(data['expire_datetime'])
            self.oauth_client.access_token = self.access_token
            logger.info('Successfully read access token from file')
        except FileNotFoundError:
            logger.info('Access token file not found')

    def save_access_token(self):
        logger.info('Saving access token to file')
        json_data = {
            'access_token': self.access_token,
            'expire_datetime': self.expire_datetime.isoformat()
        }
        self.access_token_cache_file.write_text(json.dumps(json_data))
        logger.info('Successfully saved access token to file')

    def refresh_access_token(self):
        if self.expire_datetime is None or self.expire_datetime < datetime.now():
            logger.info('Refreshing access token')
            access_token_object = self.oauth_client.refresh_access_token(refresh_token=self.refresh_token)
            self.expire_datetime = datetime.now() + timedelta(seconds=access_token_object.expires_in)
            self.access_token = access_token_object.access_token
            self.oauth_client.access_token = self.access_token
            self.save_access_token()
            logger.info('Successfully refreshed access token')
        else:
            logger.info('Reusing access token')

        return self.access_token

    def search(self, query: str, max_results: int = 5, region_code: str = 'AR') -> list[Video]:
        self.refresh_access_token()
        logger.info(f'Searching for "{query}"')
        search = self.oauth_client.search.list(q=query, part='snippet', maxResults=20, regionCode=region_code)
        video_ids = [item.id.videoId for item in search.items if item.id.videoId is not None][:max_results]
        results = self.get_video_content_details(video_ids=video_ids)
        logger.info(f'Search results for "{query}". Found {len(results)} videos')
        return results

    def get_video_from_url(self, url: str) -> Video:
        self.refresh_access_token()
        logger.info(f"Getting video from URL {url}")
        parsed_url = urlparse(url)
        video_id = parse_qs(parsed_url.query)["v"][0]
        video = self.get_video_content_details(video_ids=[video_id])[0]
        logger.info(f'Got video from URL {url}')
        return video

    def get_all_videos_in_playlist(self, playlist_id: str) -> list[str]:
        do_request = True
        next_page_token = None
        video_ids = []
        while do_request:
            self.refresh_access_token()
            logger.info(f'Getting videos from playlist {playlist_id}')
            playlist = self.oauth_client.playlistItems.list(playlist_id=playlist_id, part='snippet', max_results=50, page_token=next_page_token)
            video_ids += [item.snippet.resourceId.videoId for item in playlist.items]
            next_page_token = playlist.nextPageToken
            do_request = next_page_token is not None
        return video_ids

    def get_playlist_videos_from_url(self, url: str) -> list[Video]:
        self.refresh_access_token()
        logger.info(f'Getting videos from playlist URL {url}')
        parsed_url = urlparse(url)
        playlist_id = parse_qs(parsed_url.query)['list'][0]
        index = int(parse_qs(parsed_url.query).get('index', [0])[0]) + 1 if 'index' in parse_qs(parsed_url.query) else 0
        playlist_video_ids = self.get_all_videos_in_playlist(playlist_id=playlist_id)
        results = self.get_video_content_details(video_ids=playlist_video_ids[index:])
        logger.info(f'Got videos from playlist URL {url}. Found {len(results)} videos')
        return results

    def get_video_content_details(self, video_ids: list[str]) -> list[Video]:
        self.refresh_access_token()
        logger.info(f'Getting video content details for {video_ids}')
        batch_size = 50
        batches = [video_ids[i:i + batch_size] for i in range(0, len(video_ids), batch_size)]
        videos = []
        for batch in batches:
            response = self.oauth_client.videos.list(part='snippet,contentDetails', video_id=','.join(batch))
            videos += response.items
        logger.info(f'Got video content details for {video_ids}')
        results = []
        for video_id, item in zip(video_ids, videos):
            results.append(Video(
                id=video_id,
                title=item.snippet.title,
                duration=item.contentDetails.get_video_seconds_duration(),
                thumbnail_url=item.snippet.thumbnails.default.url,
            ))
        return results

    def get_video_file(self, video: Video) -> Path:
        if not video.cache_path.exists():
            self.download_video(video=video)
        return video.cache_path

    def download_video(self, video: Video):
        self._download_video_from_url(url=video.url, path=video.cache_path)

    @staticmethod
    def _download_video_from_url(url: str, path: Path):
        logger.info(f'Downloading video from {url}. Path: {path}')
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": path.with_suffix("").as_posix(),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info(f"Downloaded video from {url}. Path: {path}")


YOUTUBE_API = YoutubeApi(
    api_key=SETTINGS.YOUTUBE_API_KEY,
    client_id=SETTINGS.YOUTUBE_CLIENT_ID,
    client_secret=SETTINGS.YOUTUBE_CLIENT_SECRET,
    refresh_token=SETTINGS.YOUTUBE_REFRESH_TOKEN,
    channel_id=SETTINGS.YOUTUBE_CHANNEL_ID,
)

