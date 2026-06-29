import typing as _typing

import dataclassbase as _dc
from dataclassbase import Field


class CallbackField(_dc.Field):
    def __init__(
        self,
        name: str,
        annotation: _typing.Any,
        has_default: bool = False,
        default: _typing.Any = None,
        default_factory: _typing.Callable[[], None] | None = None,
        check_overriding_field_callback: _typing.Callable[[_dc.Field], None] = None,
        check_overridden_field_callback: _typing.Callable[[_dc.Field], None] = None,
        check_assignment_callback: _typing.Callable[[_typing.Any], None] = None,
    ) -> None:
        super().__init__(name, annotation, has_default, default, default_factory)

        self._check_overriding_field_callback = check_overriding_field_callback
        self._check_overridden_field_callback = check_overridden_field_callback
        self._check_assignment_callback = check_assignment_callback

    def check_overridden_field(self, overridden_field: Field) -> None:
        if self._check_overridden_field_callback is not None:
            self._check_overridden_field_callback(overridden_field)

    def check_overriding_field(self, overriding_field: Field) -> None:
        if self._check_overriding_field_callback is not None:
            self._check_overriding_field_callback(overriding_field)

    def check_assignment(self, obj: _typing.Any) -> None:
        if self._check_assignment_callback is not None:
            self._check_assignment_callback(obj)
