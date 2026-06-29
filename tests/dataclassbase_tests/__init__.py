import typing as _typing

import dataclassbase as _dc


class SomeFactory:
    def __init__(self) -> None:
        raise TypeError('Do not create an instance of this type.')


def check_field(
    instance: _dc.DataclassType,
    name: str,
    annotation: _typing.Any,
    default: type[SomeFactory] | _typing.Any = ...,
    field_type: type[_dc.Field] = _dc.Field,
    type_exact: bool = True,
) -> None:
    field: _dc.Field = instance.__dataclass_fields__[name]

    if field.name != name:
        raise ValueError("The field's name disagrees with `name`.")

    if field.annotation != annotation:
        raise ValueError("The field's annotation disagrees with `annotation`.")

    if default is ...:
        if field.has_default:
            raise ValueError('No default value was indicated, but the field has a default value.')

        if field.default is not None:
            raise ValueError("The field's default value was not `None` though its `has_default`-value was `False`.")
    else:
        if not field.has_default:
            raise ValueError('The field does not have a default value, but `default` is set to a value.')
        if field.default_factory is None:
            if default is SomeFactory:
                raise ValueError('The field defines a constant default value, but `default` implies a factory.')
            if field.default != default:
                raise ValueError("The field's default value is not equal to `default`.")
        elif default is not SomeFactory:
            raise ValueError('The field defines a default factory, but `default` implies a constant default value.')

    if type_exact:
        assert type(field) is field_type
    else:
        assert isinstance(field, field_type)
