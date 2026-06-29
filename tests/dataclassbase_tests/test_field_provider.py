import typing as _typing

import dataclassbase as _dc

from . import check_field, fields


class SubField(_dc.Field):
    pass


def test_field_factory() -> None:
    class Dataclass:
        x: int

    _dc.make_dataclass(Dataclass, SubField)

    dataclass_type = _typing.cast(_dc.DataclassType, _typing.cast(object, Dataclass))

    check_field(dataclass_type, 'x', int, field_type=SubField)


class Base:
    pass


class Child(Base):
    pass


def test_check_overriding_field() -> None:
    base_overridden_by = None
    base_overriding = None
    child_overridden_by = None
    child_overriding = None

    def check_overriding_field_callback_base(field: _dc.Field) -> None:
        nonlocal base_overridden_by
        base_overridden_by = field

    def check_overriding_field_callback_child(field: _dc.Field) -> None:
        nonlocal base_overriding
        base_overriding = field

    def check_overridden_field_callback_base(field: _dc.Field) -> None:
        nonlocal child_overridden_by
        child_overridden_by = field

    def check_overridden_field_callback_child(field: _dc.Field) -> None:
        nonlocal child_overriding
        child_overriding = field

    class BaseDataclass(metaclass=_dc.DataclassMeta):
        x: Base = fields.CallbackField.declare(
            check_overriding_field_callback=check_overriding_field_callback_base,
            check_overridden_field_callback=check_overridden_field_callback_base,
        )

    class ChildDataclass(BaseDataclass):
        x: Child = fields.CallbackField.declare(
            check_overriding_field_callback=check_overriding_field_callback_child,
            check_overridden_field_callback=check_overridden_field_callback_child,
        )

    base_field = BaseDataclass.__dataclass_fields__['x']
    child_field = ChildDataclass.__dataclass_fields__['x']

    assert base_overridden_by is child_field
    assert base_overriding is None
    assert child_overridden_by is None
    assert child_overriding is base_field


def test_check_assignment() -> None:
    reassigned = False

    def check_assignment_callback(obj: _typing.Any) -> None:
        nonlocal reassigned
        reassigned = True

    class Dataclass(metaclass=_dc.DataclassMeta):
        x: int = fields.CallbackField.declare(check_assignment_callback=check_assignment_callback)

    instance = Dataclass(1)

    reassigned = False

    instance.x = 1
    assert reassigned
