import typing as _typing

import pytest as _pytest

import dataclassbase as _dc


@_dc.dataclass(field_provider=_dc.TypeConstrainedField)
class TypeConstrainedDataclass:
    x: int


def test_valid_assignment() -> None:
    assert isinstance(TypeConstrainedDataclass(1).x, int)


def test_invalid_assignment() -> None:

    with _pytest.raises(TypeError):
        assert isinstance(TypeConstrainedDataclass('').x, int)


def test_unsupported_annotation() -> None:

    with _pytest.raises(TypeError):

        @_dc.dataclass(field_provider=_dc.TypeConstrainedField)
        class InvalidTypeConstrainedDataclass:
            x: _typing.Annotated[int, str]


def test_reassignment() -> None:
    instance = TypeConstrainedDataclass(1)

    instance.x = 2

    assert instance.x == 2


def test_invalid_reassignment() -> None:
    instance = TypeConstrainedDataclass(1)

    with _pytest.raises(TypeError):
        instance.x = '1'
