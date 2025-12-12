from dataclasses import dataclass
from logging import getLogger, DEBUG
from typing import Literal

log = getLogger("uvicorn")
log.setLevel(DEBUG)

@dataclass
class APIResponse:
    status: Literal["ok", "error"]
    message: str

@dataclass
class LoginData:
    username: str
    password: str
