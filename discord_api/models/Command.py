import re
from typing import Optional

from pydantic import BaseModel

from discord_api.models import Action


class Command(BaseModel):
    action: Action
    query: str

    def is_youtube_video(self) -> bool:
        youtube_regex = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/(watch\?v=|embed/|v/|.+)?[A-Za-z0-9_-]{11}"
        return bool(re.match(youtube_regex, self.query))

    def is_youtube_playlist(self) -> bool:
        playlist_regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=[\w-]+&list=[\w-]+|playlist\?list=[\w-]+)"
        return bool(re.match(playlist_regex, self.query))

    def get_youtube_video_id(self) -> Optional[str]:
        patterns = [
            r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtube\.com/v/([A-Za-z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.match(pattern, self.query)
            if match:
                return match.group(1)

        return None


COMMANDS = {
    Action.PLAY: ["play", "pone", "pon", "poneme", "ponme"],
    Action.PAUSE: [
        "pause",
        "pausa",
        "aguanta",
        "espera",
        "pera",
        "para",
        "cortala",
        "deja de joder",
        "no",
        "basta",
    ],
    Action.RESUME: ["resume", "resumir", "resumime", "segui", "dale", "mandale"],
    Action.STOP: ["stop"],
    Action.SKIP: ["skip", "saltear", "salta", "siguiente", "sig", "next"],
    Action.QUEUE: ["queue", "cola", "list"],
    Action.CLEAR: ["clear", "lavate la cola", "limpiate la cola"],
    Action.DISCONNECT: ["disconnect", "desconectar", "salir", "chau", "vete", "raja"],
    Action.HELP: ["help", "ayuda", "comandos", "commands", "halluda"],
}

COMMANDS_HELP = {
    Action.PLAY: "Reproduce una canción. Puede ser una URL de YouTube, un nombre de canción o un nombre de playlist",
    Action.PAUSE: "Pausa la canción actual",
    Action.RESUME: "Reanuda la canción pausada",
    Action.STOP: "Detiene la canción actual",
    Action.SKIP: "Salta a la siguiente canción",
    Action.QUEUE: "Muestra la cola de canciones",
    Action.CLEAR: "Limpia la cola de canciones",
    Action.DISCONNECT: "Desconecta al bot del canal de voz",
    Action.HELP: "Muestra esta ayuda",
}
