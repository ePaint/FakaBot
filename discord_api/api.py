import json
from datetime import datetime, timedelta
from settings import Settings


class YoutubeApi:
    def __init__(self, api_key: str, client_id: str, client_secret: str, refresh_token: str):
        self.api_key_client = Client(api_key=api_key)
        self.oauth_client = Client(client_id=client_id, client_secret=client_secret)
        self.refresh_token = refresh_token
        self.access_token = None
        self.expire_datetime = None
        self.read_access_token()

    def read_access_token(self):
        try:
            logger.info('Reading access token from file')
            data = json.load(open('access_token.json', 'r'))
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
        json.dump(json_data, open('access_token.json', 'w+'))
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

    def channel_list(self, channel_id: str) -> ChannelListResponse:
        self.refresh_access_token()
        logger.info(f'Getting channel list for channel id {channel_id}')
        channels = self.oauth_client.channels.list(channel_id=channel_id)
        logger.info(f'Got channel list for channel id {channel_id}')
        return channels

    def get_channel(self, channel_id: str) -> Channel | None:
        channels = self.channel_list(channel_id=channel_id)
        return channels.items[0] if channels.items else None

    def upload_video(self, channel_id: str, filename: str, title: str, description: str, tags: list[str] = None):
        """
            Upload a video to a channel, the video will be uploaded as Private and will not notify subscribers
            :param channel_id:
            :param filename:
            :param title:
            :param description:
            :param tags:
            :return:
        """

        self.refresh_access_token()
        logger.info(f'Starting video upload {channel_id} - {title} - {filename}')
        media_upload = self.oauth_client.videos.insert(
            body=Video(
                snippet=VideoSnippet(
                    title=title,
                    description=description,
                    tags=tags or []
                ),
                status=VideoStatus(
                    privacyStatus='unlisted'
                ),
            ),
            media=Media(
                filename=filename,
            ),
            parts=['snippet'],
            notify_subscribers=False,
        )

        response = None
        while response is None:
            logger.info(f'Uploading video {channel_id} - {title} - {filename}')
            status, response = media_upload.next_chunk()
            if status is not None:
                logger.info(f'Uploaded {status.progress()} bytes')

        video = Video.from_dict(response)
        logger.info(f'Uploaded video {channel_id} - {title} - {filename}')
        return video


YOUTUBE_API = YoutubeApi(
    api_key=Settings().YOUTUBE_API_KEY,
    client_id=Settings().YOUTUBE_CLIENT_ID,
    client_secret=Settings().YOUTUBE_CLIENT_SECRET,
    refresh_token=Settings().YOUTUBE_REFRESH_TOKEN
)

