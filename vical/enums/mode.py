from enum import Enum, auto


class Mode(Enum):
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    OPERATOR_PENDING = auto()
    COMMAND = auto()
    PROMPT = auto()