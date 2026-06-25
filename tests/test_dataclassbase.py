from typing import Any

import dataclassbase as dc


def check_field(instance: dc.DataclassMeta, name: str, annotation: Any, default: Any = ...) -> None:
    field: dc.Field = instance.__fields__[name]

    assert field.name == name

    assert field.annotation == annotation

    if default is ...:
        assert not field.has_default
        assert field.default is None
    else:
        assert field.has_default
        assert field.default is default


#
# Base
#


class Base(metaclass=dc.DataclassMeta):
    field: int


def test_dataclassmeta_base_fields() -> None:
    check_field(Base, 'field', int)


def test_dataclassmeta_base_init_args() -> None:
    instance = Base(1)
    assert instance.field == 1


def test_dataclassmeta_base_init_kwargs() -> None:
    instance = Base(field=1)
    assert instance.field == 1


#
# BaseDefaulting
#


class BaseDefaulting(metaclass=dc.DataclassMeta):
    field: int = 0


def test_dataclassmeta_base_defaulting_fields() -> None:
    check_field(BaseDefaulting, 'field', int, 0)


def test_dataclassmeta_base_defaulting_init() -> None:
    instance = BaseDefaulting()
    assert instance.field == 0


def test_dataclassmeta_base_defaulting_init_args() -> None:
    instance = BaseDefaulting(1)
    assert instance.field == 1


def test_dataclassmeta_base_defaulting_init_kwargs() -> None:
    instance = BaseDefaulting(field=1)
    assert instance.field == 1


#
# Inherited
#


class Inherited(Base):
    other: str


def test_dataclassmeta_inherited_fields() -> None:
    check_field(Inherited, 'field', int)
    check_field(Inherited, 'other', str)


#
# InheritedOverlap
#


class InheritedOverlap(Inherited):
    field: int = 0


def test_dataclassmeta_inheritedoverlap_fields() -> None:
    check_field(InheritedOverlap, 'field', int, 0)
    check_field(InheritedOverlap, 'other', str)


def test_dataclassmeta_incode() -> None:
    class InCode(metaclass=dc.DataclassMeta):
        field: int
        defaulting: int = 1

    check_field(InCode, 'field', int)
    check_field(InCode, 'defaulting', int, 1)
