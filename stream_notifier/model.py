from functools import reduce
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel as PydanticBaseModel, WrongConstantError
from pydantic.color import Color as PydanticColor


class BaseModel(PydanticBaseModel):
    class Config:
        alias_generator = lambda name: name.replace("_", " ")
        allow_population_by_field_name = True


class Color:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        color = PydanticColor(v)
        return reduce(lambda x, y: (x << 8) + y, color.as_rgb_tuple(alpha=False))


def from_mapping(mapping: dict[str, Any]):
    """Construct a pydantic type from mapping.

    Maps from string input (as the key) to the corresponding value."""

    class MappingType:
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            try:
                return mapping[v]
            except KeyError:
                raise WrongConstantError(permitted=list(mapping.keys()))

    return MappingType


class CheckerConfig(BaseModel):
    color: Color = 0
    check_interval: int = 10
