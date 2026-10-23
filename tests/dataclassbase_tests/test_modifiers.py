import typing as _typing

import pytest as _pytest

import dataclassbase as _dc

# Equatable


def test_eq() -> None:
    @_dc.dataclass(_dc.Equatable)
    class Dataclass:
        x: int

    assert Dataclass(1) == Dataclass(1)


def test_neq() -> None:
    @_dc.dataclass(_dc.Equatable)
    class Dataclass:
        x: int

    assert Dataclass(1) != Dataclass(2)


# Frozen


def test_frozen() -> None:
    @_dc.dataclass(_dc.Frozen)
    class Dataclass:
        x: int

    inst = Dataclass(1)

    with _pytest.raises(RuntimeError):
        inst.x = 2

    assert inst.x == 1


def test_frozen_combo() -> None:
    @_dc.dataclass(_dc.Frozen, _dc.KeywordOnly)
    class A:
        x: int

    @_dc.dataclass(_dc.KeywordOnly, _dc.Frozen)
    class B:
        x: int

    A(x=1)
    B(x=1)


def test_frozen_inheritance() -> None:
    @_dc.dataclass(_dc.Frozen)
    class A:
        x: int

    @_dc.dataclass(_dc.Frozen)
    class B(A):
        x: int

    instance = B(x=1)

    with _pytest.raises(RuntimeError):
        instance.x = 2


def test_frozen_inheritance_nondataclass() -> None:
    @_dc.dataclass(_dc.Frozen)
    @_typing.dataclass_transform()
    class A:
        x: int

    class B(A):
        pass

    instance = B(x=1)

    with _pytest.raises(RuntimeError):
        instance.x = 2


def test_frozen_inheritance_mix() -> None:
    @_dc.dataclass(_dc.Frozen)
    class A:
        x: int

    @_dc.dataclass(_dc.Frozen)
    class B:
        x: int

    @_dc.dataclass(_dc.Frozen)
    class C(A, B):
        pass

    instance = C(x=1)

    with _pytest.raises(RuntimeError):
        instance.x = 2


def test_frozen_inheritance_mix_nondataclass() -> None:
    # A, B are dataclasses, C(A, B) is not.
    # Note that this is a special case that is rather untypical

    @_dc.dataclass(_dc.Frozen)
    class A:
        x: int

    @_dc.dataclass(_dc.Frozen)
    class B:
        x: int

    class C(A, B):
        pass

    instance = C(x=1)

    with _pytest.raises(RuntimeError):
        instance.x = 3


def test_frozen_inheritance_partly() -> None:
    @_dc.dataclass()
    class A:
        x: int

    @_dc.dataclass(_dc.Frozen)
    class B(A):
        y: int

    instance = B(x=1, y=2)

    instance.x = 3

    with _pytest.raises(RuntimeError):
        instance.y = 4


# PositionalOnly


def test_pos_only_accepts_pos() -> None:
    @_dc.dataclass(_dc.PositionalOnly)
    class Dataclass:
        x: int

    inst = Dataclass(1)

    assert inst.x == 1


def test_pos_only_rejects_kw() -> None:
    @_dc.dataclass(_dc.PositionalOnly)
    class Dataclass:
        x: int

    with _pytest.raises(TypeError):
        Dataclass(x=1)


# KeywordOnly


def test_kw_only_accepts_kw() -> None:
    @_dc.dataclass(_dc.KeywordOnly)
    class Dataclass:
        x: int

    inst = Dataclass(x=1)

    assert inst.x == 1


def test_kw_only_rejects_pos() -> None:
    @_dc.dataclass(_dc.KeywordOnly)
    class Dataclass:
        x: int

    with _pytest.raises(TypeError):
        Dataclass(1)


# Representable


def test_repr() -> None:
    @_dc.dataclass(_dc.Representable)
    class Dataclass:
        x: int

    inst = Dataclass(1)

    assert repr(inst) == f'{Dataclass.__name__}(x=1)'
    assert str(inst) == f'{Dataclass.__name__}(x=1)'


def test_repr_no_repr() -> None:
    @_dc.dataclass(_dc.Representable(dict_to_repr=None))
    class Dataclass:
        x: int

    inst = Dataclass(1)

    assert repr(inst) != f'{Dataclass.__name__}(x=1)'
    assert str(inst) == f'{Dataclass.__name__}(x=1)'


def test_repr_no_str() -> None:
    @_dc.dataclass(_dc.Representable(dict_to_str=None))
    class Dataclass:
        x: int

    inst = Dataclass(1)

    assert repr(inst) == f'{Dataclass.__name__}(x=1)'
    # `__str__` forwards to `__repr__` by Python, by default. We thus follow this behavior
    assert str(inst) == f'{Dataclass.__name__}(x=1)'


def test_repr_neither() -> None:
    @_dc.dataclass(_dc.Representable(dict_to_str=None, dict_to_repr=None))
    class Dataclass:
        x: int

    inst = Dataclass(1)

    assert repr(inst) != f'{Dataclass.__name__}(x=1)'
    assert str(inst) != f'{Dataclass.__name__}(x=1)'
