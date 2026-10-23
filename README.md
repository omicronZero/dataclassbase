# dataclassbase: Implement custom dataclasses

See [Documentation](https://dataclassbase.readthedocs.io/en/latest/) for the latest documentation.

## What it is and how to get it

**dataclassbase** is a small toolkit for providing your own dataclasses.

For dataclasses, attributes are declared via annotations, and initializers are created automatically making development
fast. However, often data, in dataclasses, share common properties (e.g., data shape, etc.) or we might want to have
more control over the fields in dataclasses. This is where **dataclassbase** comes to help: You can define your own
dataclass-like behavior and control the behavior of your dataclass in a fine-grained manner.

You can install it into your environment from PyPI via

```shell
pip install dataclassbase
```

## General note

While the project is generally usable, it is not yet production-ready. It is, however, being actively developed since I
plan to use it as a base for further work.

## License

[MIT](./LICENSE)

## The Basics

The `dataclasses` module provides very basic dataclasses with little customization. The objective of this package is to
overcome this limitation by providing customizable dataclasses.

A possible definition using the built-in dataclasses is

```python
from dataclasses import dataclass


@dataclass
class SomeClass:
    some_field: str
    some_defaulting_field: int = 1
```

In this framework, a similar approach is possible:

```python
from dataclassbase import dataclass


@dataclass
class SomeClass:
    some_field: str
    some_defaulting_field: int = 1
```

The most obvious difference above is that we import from `dataclassbase` rather than `dataclasses`. However, looking at
the signature of `dataclassbase.dataclass`, we notice that there are two notable parameters: `field_provider` and
`object_handler`. `field_provider` allows customization of the field generation and processing, `object_handler`
implements the logic for the initialization (`__init__`) and attribute assignment (`__setattr__`) of objects of the
generated dataclass. We therefore can hook into or override the behavior of the dataclass.

If you omit the `field_provider` or `object_handler`, the respective default implementations are used. These imitate the
behavior of the default dataclass behavior; their implementation can be found in the `BasicFieldProvider` and
`ObjectHandler` classes.
If you provide a callable to `field_provider` it must match the signature of `dataclassbase.Field`: A
`BasicFieldProvider` gets generated using the initializer as a factory
You can thus directly specify the type of field to use, as long as it matches the signature of the initializer of
`dataclassbase.Field`.
In your custom field implementation, you may, for example, further process the value supplied to the `default`
parameter to transform custom values into fields.

Variants to `dataclassbase.dataclass` are the classes `DataclassMetaBase` and `DataclassMeta` which is a subclass of the
former. `dataclassbase.dataclass` gets applied using a decorator whereas the other two are metaclasses from which to
inherit. Their benefit lies mainly in the fact that the static attributes created for dataclasses get recognized by the
static type checker - for `dataclassbase.dataclass`, these are not available even though they get declared nonetheless.
A more in-depth explanation is given below.

```python
from dataclassbase import DataclassMeta


class SomeOtherClass(metaclass=DataclassMeta):
    field: int
```

## Fine-tuning the behavior dataclass members

`dataclassbase.dataclass` comes with quite a lot of nice additions: We can freeze the dataclass, equality and unequality
operators get generated, a hash function may be provided, and so forth. This behavior can be imitated using the classes
derived from the `BehaviorModifier` type. For now, these are

* `Frozen`: Dataclasses cannot be assigned new values and cannot be reinitialized
* `Representable`: Adds a string representation via `__repr__` and `__str__`
* `Equatable`: Adds overloads for `__eq__` and `__ne__`, and, optionally, for `__hash__`
* `PositionalOnly`: The initializer only allows positional arguments
* `KeywordOnly`: The initializer only allows keyword arguments

Add these as `modifiers` when calling `dataclass` or `make_dataclass` or return them as `_modifiers` in metaclasses
derived from `DataclassMetaBase` or types derived from `DataclassBase`.

Note that some of the behaviors are "unsafe", and it is up to you to decide whether your use-case is safe. For
example, hash codes typically change once fields of the dataclass change. Using such a class as a key is unsafe. You
thus will typically combine `Frozen` and `Equatable`. Note that `Frozen` does not affect nested dataclasses: If these
are not frozen, the dataclass itself may still be mutable. Another unsafe example is the combination of `PositionalOnly`
and `KeywordOnly` which does not make any sense, but is not caught for now.
I may add such safeguards later or implement them via inheritance, but for now it is obvious that such combinations do
not make any sense.

A more powerful mechanism is provided in the `ObjectHandler` type which can be supplied to `dataclass` and
`make_dataclass`. It provides the actual implementations handling initialization, set-attribute, and delete-attribute.

## Customizing dataclass fields

`dataclassbase.Field`s themselves can check whether the value assigned to them is valid. Furthermore, they can check
whether fields in derived classes are valid and, in the opposite direction, whether they are valid overrides of fields
of superclasses. To control the behavior, you need to create a new type that inherits from `dataclassbase.Field` and
override the respective methods. You then create a `dataclassbase.FieldProvider` that provides the field in the newly
created type and supply it to the `field_provider` parameter of `dataclass`/`make_dataclass` or `_field_provider`
function of types inheriting from `DataclassMetaBase`/`DataclassBase`).
If the field's initializer matches the one of `dataclassbase.Field`, you can also use supply it directly without
wrapping it in a custom field provider - the framework does it for you.

As an example, you can look at the provided `dataclassbase.TypeConstrainedField` which provides simple type checking
via `isinstance`.

Generally, you can also directly declare fields or instances of `FieldInitializer` on a dataclass, e.g., obtained from
`TField.declare` where `TField` is your field type. The `dataclassbase.FieldProvider` has a method for both parametric
construction and validating preexisting fields.

## dataclass vs. make_dataclass vs. Dataclass (Meta) vs. Dataclass (Meta)Base

There are three (and a half) functions you may use to initialize a dataclass on a type:

* `dataclass`
* `make_dataclass`
* `DataclassMeta`/`Dataclass`
* `DataclassMetaBase`/`DataclassBase`

`dataclass` is to be used as a decorator whereas `make_dataclass` implements the actual logic behind it. Typically,
it will not be necessary to call the latter. Another way to initialize a dataclass is to use `DataclassMeta` as a
metaclass or `Dataclass` as a base class. `Dataclass` and `DataclassBase` are non-meta classes, i.e., you can use them
with another abstract base class right away.

`Dataclass` and `DataclassMeta` basically do the same as `dataclass`, but enable better static type-checking:
`make_dataclass` creates a couple of static attributes on the type made into a dataclass. Using `dataclass`, these
are not visible to static type checkers and analyzers since the current version of Python typing does not allow
annotating the addition of new members to existing objects.

In Python, dataclasses are reported to static type checkers by calling `typing.dataclass_transform` on their creating
function, an abstract base class, or an inherited class (as described
[here](https://typing.python.org/en/latest/spec/dataclasses.html)). These are, however, static, i.e., we cannot supply
behavior modifiers to `make_dataclass` and expect the differing behavior to be recognized by a static type checker.
Therefore, you can use the `DataclassMetaBase` and `DataclassBase` classes to derive your own dataclasses:

```python
from dataclassbase import DataclassMetaBase, Field, BasicFieldProvider
from typing import dataclass_transform


class CustomField(Field):
    # you can override the methods provided by `Field` to control the behavior of the field in derived classes,
    # superclasses, to check the assignments, etc. You can also change the behavior of `__init__` as long as its
    # signature matches the one from the base
    pass


@dataclass_transform
class CustomDataclassMeta(DataclassMetaBase):
    @classmethod
    def _field_provider(cls) -> BasicFieldProvider:
        # we want it to return our custom field. The factory works since the signature of `CustomField.__init__` matches
        # the one of `Field.__init__`
        return BasicFieldProvider(CustomField)


class VariantA(metaclass=CustomDataclassMeta):
    field: int
    defaulting: int = 1
```

`Dataclass` and `DataclassMeta` provide default implementations for `DataclassBase` and `DataclassMetaBase`,
respectively. These predeclare the `dataclass_transform` with default field specifiers (`Field` and `FieldInitializer`),
and they do neither add any behavior modifiers nor inform static type checkers about such behaviors being applied.

Between the metaclass and non-metaclass variant, it does not really make a difference which one you choose if you do not
have another metaclass you would like to inherit from (e.g. `abc.ABC` includes metaclass `abc.ABCMeta`): `DataclassBase`
uses `__init_subclass__` rather than the `type.__new__` overridden in the metaclass. There are various methods declared
as class-methods either on the base class or the metaclass.

# When to use dataclassbase and not ...?

## Pydantic

Pydantic's objective is to provide fast data validation and
serialization [[1]](https://pydantic.dev/docs/validation/latest/get-started/).
dataclassbase aims to be much more abstract since it is not constrained to a single use-case such as data validation,
and thus does (hopefully) not give too strong restrictions on what you can/cannot do.
