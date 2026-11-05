"""Reproduce the pydantic 2.14.2 validation fixes and the JSON key-matching change with synthetic payloads.

Author: Sandeep Belgavi. Original example for the aicassindra.com article "pydantic 2.14.2 Fixes Two Validation
Bypasses in Extra Data, and Changes JSON Parsing". Advisories: GHSA-qpmf-fgh3-ff25, GHSA-3r8g-cqwr-jr29.
Run with one of the pinned requirements files installed: python repro.py
"""
import json
import typing
from typing import Annotated

import pydantic
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, with_config
from pydantic.alias_generators import to_camel


class ToolArgs(BaseModel):
    """GHSA-qpmf: extra keys must match ^x_; JSON mode skipped the key check from 2.13.0 to 2.14.1."""
    model_config = ConfigDict(extra='allow')
    __pydantic_extra__: dict[Annotated[str, Field(pattern=r'^x_')], int]
    case_id: str


@with_config(ConfigDict(extra='allow'))
class Refund(typing.TypedDict):
    """GHSA-3r8g: the field name could override the validated alias value."""
    amount: Annotated[int, Field(alias='refundAmount', le=5000)]


@pydantic.dataclasses.dataclass(config=ConfigDict(extra='allow'))
class RefundDC:
    amount: int = Field(alias='refundAmount', le=5000)


class RefundModel(BaseModel):
    model_config = ConfigDict(extra='allow')
    amount: int = Field(alias='refundAmount', le=5000)


class Page(BaseModel):
    model_config = ConfigDict(extra='forbid', alias_generator=to_camel)
    page_size: int = 10


class PageAllow(BaseModel):
    model_config = ConfigDict(extra='allow', alias_generator=to_camel)
    page_size: int = 10


TOOL_PAYLOAD = '{"case_id": "CASE-4210", "x_priority": 2, "refund_override": 1}'
REFUND = {'refundAmount': 1200, 'amount': 999999}


def outcome(fn):
    try:
        return 'accepted: ' + repr(fn())
    except ValidationError as e:
        return 'ValidationError: ' + e.errors()[0]['type']


def reproduce():
    return {
        'pydantic': pydantic.VERSION,
        'qpmf_json': outcome(lambda: ToolArgs.model_validate_json(TOOL_PAYLOAD).model_extra),
        'qpmf_python': outcome(lambda: ToolArgs.model_validate(json.loads(TOOL_PAYLOAD)).model_extra),
        '3r8g_typeddict': outcome(lambda: TypeAdapter(Refund).validate_python(REFUND)),
        '3r8g_dataclass': outcome(lambda: RefundDC(**REFUND).amount),
        '3r8g_basemodel': outcome(lambda: RefundModel.model_validate(REFUND).amount),
        'page_forbid_json': outcome(lambda: Page.model_validate_json('{"page_size": 50}')),
        'page_forbid_python': outcome(lambda: Page.model_validate({'page_size': 50})),
        'page_allow_json_extras': outcome(lambda: PageAllow.model_validate_json('{"page_size": 50}').model_extra),
    }


if __name__ == '__main__':
    print(json.dumps(reproduce(), indent=1))
