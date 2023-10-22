from functools import reduce
from typing import Annotated, Any, Literal

from pydantic import AfterValidator
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict
from pydantic_extra_types.color import Color as PydanticColor


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=lambda name: name.replace("_", " "), populate_by_name=True
    )


# Convert string color value to RGB integer
Color = Annotated[
    str,
    AfterValidator(
        lambda v: reduce(
            lambda x, y: (x << 8) + y, PydanticColor(v).as_rgb_tuple(alpha=False)
        )
    ),
]


def from_mapping(mapping: dict[str, Any]):
    """Construct a pydantic type from mapping.

    Maps from string input (as the key) to the corresponding value."""

    return Annotated[
        Literal[tuple(mapping.keys())], AfterValidator(lambda v: mapping[v])
    ]
