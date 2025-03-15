from enum import StrEnum


class Action(StrEnum):
    PLAY = "play"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    SKIP = "skip"
    QUEUE = "queue"
    CLEAR = "clear"
    DISCONNECT = "disconnect"
    HELP = "help"
