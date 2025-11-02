from abc import ABC

from pydantic import BaseModel, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_snake


class BasePayload(BaseModel, ABC):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        alias_generator=AliasGenerator(
            validation_alias=to_snake,
            serialization_alias=to_snake,
        ),
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
        validate_assignment=True,
        validate_default=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
    )
