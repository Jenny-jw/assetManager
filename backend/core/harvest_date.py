from datetime import date
from typing import Annotated

from pydantic import AfterValidator, Field

def assert_harvest_yyyymmdd(value: int) -> int:
    text = str(value)
    if len(text) != 8:
        raise ValueError("harvest_time must be a real calendar date as YYYYMMDD")
    try:
        date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as exc:
        raise ValueError("harvest_time must be a real calendar date as YYYYMMDD") from exc
    return value

HarvestYyyymmdd = Annotated[
    int,
    Field(ge=20100101, le=22001231),
    AfterValidator(assert_harvest_yyyymmdd),
]