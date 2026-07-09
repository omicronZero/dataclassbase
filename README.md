# dataclassbase: Implement custom dataclasses

## What it is and how to get it

**dataclassbase** is a small toolkit for providing your own dataclasses. For dataclasses, attributes are declared via 
annotations, and constructors are created automatically making development fast.

However, often data in dataclasses shares common properties (e.g., data shape, etc.) or we might want to have more 
control over the fields in dataclasses. This is where **dataclassbase** comes to help: You can define your own 
dataclass-like behavior using `typing.dataclass_transform` or metaclasses, and control the behavior of your dataclass in
a fine-grained manner.

You can install it into your environment from PyPI via

```shell
pip install dataclassbase
```


## General note

While the project is generally usable, it is not yet production-ready. It is, however, being actively developed since I 
plan to use it as a base for further work.

## License

[MIT](./LICENSE)

## Overview

The `dataclasses` module provides very basic dataclasses with little customization. The objective of this package is to
overcome this limitation by providing customizable dataclasses.

A possible definition for the built-in dataclasses is

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
the signature of `dataclassbase.dataclass`, we note that there are two notable parameters: `field_provider` and 
`object_handler`. `field_provider` allows customization of the field generation and processing (if the user provides a
`dataclassbase.Field` as a default value), `object_handler` implements the logic for the initialization (`__init__`) and
attribute assignment (`__setattr__`) of objects of the generated dataclass. We therefore can hook into or override the
behavior of the dataclass.

If you omit the `field_provider` or `object_handler`, the respective default implementations provided in the 
`FieldProvider` and `ObjectHandler` classes, which reproduce the default dataclass behavior, are used instead.
If you provide a callable matching the signature of `dataclassbase.Field` to `field_provider`, a `FieldProvider` is
generated. Therefore, you can directly specify the type of field to use, as long as it matches the respective signature.
You can also replace the `default`-value if it indicates a value you want to process.

Note that while it suffices to call `dataclassbase.dataclass` on a class to initialize dataclass-like behavior, it does
not truly behave like a dataclass to static type checkers since it lacks the `typing.dataclass_transform` decorator.
My reason for that choice is that I would have to fix the `field_specifiers` parameter.
(Instances of the types provided in `field_specifiers` are allowed as default values for fields since they are
assumed to be fields or to be converted into some. We do that conversion in the provided `field_provider`.)
In doing so, I would constrain proper static type checking on the fields. Therefore, I would rather let you indicate the
types yourself.
To achieve true dataclass-like behavior on a type checker, you can call `typing.dataclass_transform` yourself or rely on
a metaclass derived from `DataclassMetaBase[TField]`:

Rather than using `dataclassbase.dataclass` as above, you can define your own dataclass by deriving a metaclass from
class `DataclassMetaBase[TField]` and attaching a `typing.dataclass_transform` to it. `DataclassMetaBase` invokes 
`make_dataclass` when creating the new type (`dataclass` is the decorator-variant of `make_dataclass`). It provides
the methods `_field_provider` and `_object_handler` which act as factories for the field provider and object handler for
the types using the metaclass.

```python
from dataclassbase import DataclassMetaBase, Field, FieldProvider
from typing import dataclass_transform


class CustomField(Field):
    # you can override the methods provided by `Field` to control the behavior of the field in derived classes,
    # superclasses, to check the assignments, etc. You can also change the behavior of `__init__` as long as its 
    # signature matches the one from the base
    pass


@dataclass_transform
class CustomDataclassMeta(DataclassMetaBase[Field]):
    @classmethod
    def _field_provider(cls) -> FieldProvider[Field]:
        # we want it to return our custom field. The factory works since the signature of `CustomField.__init__` matches
        # the one of `Field.__init__`
        return FieldProvider(CustomField)
    
class VariantA(metaclass=CustomDataclassMeta):
    field: int
    defaulting: int = 1
```

`dataclassbase.Field`s themselves can check whether the value assigned to them is valid. Furthermore, they can check 
whether fields in derived classes are valid and, in the opposite direction, whether they are valid overrides of fields
of superclasses. As an example, you can look at the provided `dataclassbase.TypeConstrainedField` which provides
simple type checking via `isinstance`.

The default implementation is `DataclassMeta` which just uses the default values and allows any 
`dataclasses.Field` as a default value for its fields. While it behaves in the same way as the built-in 
`dataclasses`-dataclasses, it does however not give us any benefits over it.

```python
from dataclassbase import DataclassMeta

class VariantB(metaclass=DataclassMeta):
    field: int
    defaulting: int = 1    
```

# Why dataclassbase and not ...?

## Pydantic

Pydantic's objective is to provide fast data validation and serialization [[1]](https://pydantic.dev/docs/validation/latest/get-started/).
The package is much more abstract since it is not constrained to a single use-case such as data validation, and thus 
does (hopefully) not give too strong restrictions on what you can/cannot do.
