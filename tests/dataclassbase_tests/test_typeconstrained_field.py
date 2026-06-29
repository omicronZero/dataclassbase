import typing as _typing

import pytest as _pytest

import dataclassbase as _dc


def test_valid_assignment() -> None:
    @_dc.dataclass(field_provider=_dc.TypeConstrainedField)
    class Dataclass:
        x: int

    assert isinstance(Dataclass(1).x, int)


def test_invalid_assignment() -> None:
    @_dc.dataclass(field_provider=_dc.TypeConstrainedField)
    class Dataclass:
        x: int

    with _pytest.raises(TypeError):
        assert isinstance(Dataclass('').x, int)


def test_unsupported_annotation() -> None:

    with _pytest.raises(TypeError):

        @_dc.dataclass(field_provider=_dc.TypeConstrainedField)
        class Dataclass:
            x: _typing.Annotated[int, str]
