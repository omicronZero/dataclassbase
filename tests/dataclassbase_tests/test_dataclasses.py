import pytest as _pytest

import dataclassbase as _dc

from . import check_field

#
# Base
#


class BaseMeta(metaclass=_dc.DataclassMeta):
    field: int


class Base(_dc.Dataclass):
    field: int


@_pytest.mark.parametrize('cls', [BaseMeta, Base])
def test_base_fields(cls: type[BaseMeta] | type[Base]) -> None:
    check_field(cls, 'field', int)


@_pytest.mark.parametrize('cls', [BaseMeta, Base])
def test_base_init_args(cls: type[BaseMeta] | type[Base]) -> None:
    instance = cls(1)
    assert instance.field == 1


@_pytest.mark.parametrize('cls', [BaseMeta, Base])
def test_base_init_kwargs(cls: type[BaseMeta] | type[Base]) -> None:
    instance = cls(field=1)
    assert instance.field == 1


#
# BaseDefaulting
#


class BaseDefaultingMeta(metaclass=_dc.DataclassMeta):
    field: int = 0


class BaseDefaulting(_dc.Dataclass):
    field: int = 0


@_pytest.mark.parametrize('cls', [BaseDefaultingMeta, BaseDefaulting])
def test_base_defaulting_fields(cls: type[BaseDefaultingMeta] | type[BaseDefaulting]) -> None:
    check_field(cls, 'field', int, 0)


@_pytest.mark.parametrize('cls', [BaseDefaultingMeta, BaseDefaulting])
def test_base_defaulting_init(cls: type[BaseDefaultingMeta] | type[BaseDefaulting]) -> None:
    instance = cls()
    assert instance.field == 0


@_pytest.mark.parametrize('cls', [BaseDefaultingMeta, BaseDefaulting])
def test_base_defaulting_init_args(cls: type[BaseDefaultingMeta] | type[BaseDefaulting]) -> None:
    instance = cls(1)
    assert instance.field == 1


@_pytest.mark.parametrize('cls', [BaseDefaultingMeta, BaseDefaulting])
def test_base_defaulting_init_kwargs(cls: type[BaseDefaultingMeta] | type[BaseDefaulting]) -> None:
    instance = cls(field=1)
    assert instance.field == 1


#
# Inherited
#


class InheritedMeta(BaseMeta):
    other: str


class Inherited(Base):
    other: str


@_pytest.mark.parametrize('cls', [InheritedMeta, Inherited])
def test_inherited_fields(cls: type[InheritedMeta] | type[Inherited]) -> None:
    check_field(cls, 'field', int)
    check_field(cls, 'other', str)


#
# InheritedOverlap
#


class InheritedOverlapMeta(InheritedMeta):
    other: str = ''


class InheritedOverlap(InheritedMeta):
    other: str = ''


@_pytest.mark.parametrize('cls', [InheritedOverlapMeta, InheritedOverlap])
def test_inherited_overlap_fields(cls: type[InheritedOverlapMeta] | type[InheritedOverlap]) -> None:
    check_field(cls, 'field', int)
    check_field(cls, 'other', str, '')


# Test initialization


class ThreeFieldsMeta(metaclass=_dc.DataclassMeta):
    x: int
    y: str = 'y'
    z: float = 1.0


class ThreeFields(_dc.Dataclass):
    x: int
    y: str = 'y'
    z: float = 1.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_pos_init_full(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1, '2', 3.0)

    assert instance.x == 1
    assert instance.y == '2'
    assert instance.z == 3.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_pos_init_partial(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1, '2')

    assert instance.x == 1
    assert instance.y == '2'
    assert instance.z == 1.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_kw_init_full(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(x=1, y='2', z=3.0)

    assert instance.x == 1
    assert instance.y == '2'
    assert instance.z == 3.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_kw_init_partial(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(x=1, z=3.0)

    assert instance.x == 1
    assert instance.y == 'y'
    assert instance.z == 3.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_mixed_init_full(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1, y='2', z=3.0)

    assert instance.x == 1
    assert instance.y == '2'
    assert instance.z == 3.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_mixed_init_partial(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1, z=3.0)

    assert instance.x == 1
    assert instance.y == 'y'
    assert instance.z == 3.0


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_extra_fields_pos(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    with _pytest.raises(TypeError):
        cls(1, '2', 3.0, 4)  # type: ignore[call-arg]


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_extra_fields_kw(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    with _pytest.raises(TypeError):
        cls(x=1, y='2', z=3.0, w=4)  # type: ignore[call-arg]


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_extra_fields_mixture(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    with _pytest.raises(TypeError):
        cls(1, 2, z=3.0, w=4)  # type: ignore[call-arg, arg-type]


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_extra_fields_overlap(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    with _pytest.raises(TypeError):
        cls(1, '2', y='x')  # type: ignore[misc]


# Test __setattr__


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_reassignment(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1)

    instance.x = 12
    assert instance.x == 12


# Test __delattr__


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_field_deletion(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1)

    with _pytest.raises(RuntimeError):
        del instance.x


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_nonfield_assignment(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1)

    instance.undefined_attr = 1  # type: ignore[union-attr]

    assert hasattr(instance, 'undefined_attr')


@_pytest.mark.parametrize('cls', [ThreeFieldsMeta, ThreeFields])
def test_nonfield_deletion(cls: type[ThreeFieldsMeta] | type[ThreeFields]) -> None:
    instance = cls(1)

    instance.undefined_attr = 1  # type: ignore[union-attr]

    del instance.undefined_attr  # type: ignore[union-attr]

    with _pytest.raises(AttributeError):
        _ = instance.undefined_attr  # type: ignore[union-attr]


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
        x: int = field  # type: ignore[assignment]

    check_field(FieldContainer, 'x', int)

    assert FieldContainer.__dataclassbase_fields__['x'] is field


def test_initialized() -> None:
    x = BaseMeta(0)

    assert x.__dataclassbase_initialized__  # type: ignore


def test_error_nondefault_after_default() -> None:
    # fields with a default value must not be followed by fields without a default value
    with _pytest.raises(RuntimeError):

        class InvalidDefaultingMixture(metaclass=_dc.DataclassMeta):
            x: int = 0
            y: int  # type: ignore[misc]
