import typing as _typing

import dataclassbase as _dc
from dataclassbase import Field


class ValueInSetField(_dc.Field):
    """Represents a field that requires its assignment to be in a set of fixed values."""

    def __init__(
        self,
        name: str,
        annotation: _typing.Any,
        allowed_values: _typing.Container[_typing.Hashable],
        has_default: bool = False,
        default: _typing.Any = None,
        default_factory: _typing.Callable[[], None] | None = None,
    ) -> None:
        if isinstance(allowed_values, _typing.Iterator):
            allowed_values = set(allowed_values)

        super().__init__(name, annotation, has_default, default, default_factory)

        self._allowed_values = allowed_values

    def check_assignment(self, obj: _typing.Any) -> None:
        if not isinstance(obj, _typing.Hashable) or obj not in self._allowed_values:
            raise ValueError(f'Bad value indicated for field `{self.name}`.')


class CheckOverrideCallbackField(_dc.Field):
    def __init__(
        self,
        name: str,
        annotation: _typing.Any,
        has_default: bool = False,
        default: _typing.Any = None,
        default_factory: _typing.Callable[[], None] | None = None,
        check_overriding_field_callback: _typing.Callable[[_dc.Field], None] = None,
        check_overridden_field_callback: _typing.Callable[[_dc.Field], None] = None,
    ) -> None:
        super().__init__(name, annotation, has_default, default, default_factory)

        self._check_overriding_field_callback = check_overriding_field_callback
        self._check_overridden_field_callback = check_overridden_field_callback

    def check_overridden_field(self, overridden_field: Field) -> None:
        if self._check_overridden_field_callback is not None:
            self._check_overridden_field_callback(overridden_field)

    def check_overriding_field(self, overriding_field: Field) -> None:
        if self._check_overriding_field_callback is not None:
            self._check_overriding_field_callback(overriding_field)
