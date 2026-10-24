from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, Field

def assert_harvest_yyyymmdd(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("harvest_time must be a YYYYMMDD integer")
    text = str(value)
    if len(text) != 8:
        raise ValueError("harvest_time must be a real calendar date as YYYYMMDD")
    try:
        datetime.strptime(text, "%Y%m%d")
    except ValueError as exc:
        raise ValueError("harvest_time must be a real calendar date as YYYYMMDD") from exc
    return value

HarvestYyyymmdd = Annotated[
    int,
    Field(ge=20100101, le=22001231),
    AfterValidator(assert_harvest_yyyymmdd),
]