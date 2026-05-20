from datetime import datetime
from typing import Annotated

from pydantic import PlainSerializer

# Serializes datetime as "2026-05-20T21:22:40" — no microseconds, no timezone offset.
DatetimeFormatted = Annotated[
    datetime,
    PlainSerializer(lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S"), return_type=str),
]
