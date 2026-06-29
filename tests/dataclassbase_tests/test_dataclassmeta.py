import dataclassbase as _dc

from . import check_field

#
# Base
#


class Base(metaclass=_dc.DataclassMeta):
    field: int


def test_base_fields() -> None:
    check_field(Base, 'field', int)


def test_base_init_args() -> None:
    instance = Base(1)
    assert instance.field == 1


def test_base_init_kwargs() -> None:
    instance = Base(field=1)
    assert instance.field == 1


#
# BaseDefaulting
#


class BaseDefaulting(metaclass=_dc.DataclassMeta):
    field: int = 0


def test_base_defaulting_fields() -> None:
    check_field(BaseDefaulting, 'field', int, 0)


def test_base_defaulting_init() -> None:
    instance = BaseDefaulting()
    assert instance.field == 0


def test_base_defaulting_init_args() -> None:
    instance = BaseDefaulting(1)
    assert instance.field == 1


def test_base_defaulting_init_kwargs() -> None:
    instance = BaseDefaulting(field=1)
    assert instance.field == 1


#
# Inherited
#


class Inherited(Base):
    other: str


def test_inherited_fields() -> None:
    check_field(Inherited, 'field', int)
    check_field(Inherited, 'other', str)


#
# InheritedOverlap
#


class InheritedOverlap(Inherited):
    field: int = 0


def test_inherited_overlap_fields() -> None:
    check_field(InheritedOverlap, 'field', int, 0)
    check_field(InheritedOverlap, 'other', str)


#
# Other
#


def test_incode() -> None:
    class InCode(metaclass=_dc.DataclassMeta):
        field: int
        defaulting: int = 1

    check_field(InCode, 'field', int)
    check_field(InCode, 'defaulting', int, 1)


def test_identity_for_fields() -> None:
    field = _dc.Field('x', int)

    class FieldContainer(metaclass=_dc.DataclassMeta):
        x: int = field

    check_field(FieldContainer, 'x', int)

    assert FieldContainer.__dataclass_fields__['x'] is field
