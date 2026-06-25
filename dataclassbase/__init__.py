import types as _types
import typing as _typing


class Field:
    def __init__(
        self,
        name: str,
        annotation: _typing.Any,
        has_default: bool = False,
        default: _typing.Any = None,
        default_factory: _typing.Callable[[], None] | None = None,
    ) -> None:
        if not has_default and default is not None:
            raise ValueError('If `has_default` is `False`, `default` must be `None`.')
        if default_factory is not None and default is not None:
            raise ValueError('If `default_factory` is set to a value, `default_factory` must be `None`.')

        self._name = name
        self._has_annotation = annotation
        self._annotation = annotation
        self._has_default = has_default
        self._default = default

    @property
    def name(self) -> str:
        return self._name

    @property
    def annotation(self) -> _typing.Any:
        return self._annotation

    @property
    def has_default(self) -> bool:
        return self._has_default

    @property
    def default_factory(self) -> _typing.Callable[[], _typing.Any] | None:
        return None

    @property
    def default(self) -> bool:
        return self._default

    def check_assignment(self, obj: _typing.Any) -> None:
        pass

    def check_override(self, other: Field) -> None:
        pass


class _Unspecified:
    pass


class DataclassMetaBase[TField: Field](type):
    __fields__: _types.MappingProxyType[str, Field]

    def __new__(mcs, name: str, bases: tuple[type, ...], dct: dict[str, _typing.Any]) -> type:

        tp = type.__new__(mcs, name, bases, dct)

        annotations = {}

        for stp in reversed(tp.__mro__):
            if not isinstance(stp, DataclassMetaBase):
                continue

            annot = getattr(stp, '__annotations__', None)

            if isinstance(annot, dict):
                annotations.update(annot)

        fields = []

        for k, annot in annotations.items():
            default = dct.get(k, _Unspecified)

            field = mcs._make_field(k, annot, default is not _Unspecified, None if default is _Unspecified else default)

            fields.append(field)

        field_dict = {field.name: field for field in fields}
        mcs._postprocess_fields(field_dict)

        field_map = _types.MappingProxyType(field_dict)

        tp.__fields__ = field_map

        # check with all bases (that are not metaclasses) that our overrides are valid
        for base in bases:
            if issubclass(base, DataclassMetaBase):
                base._check_overrides(base, field_map)

        user_init = getattr(tp, '__init__', None)

        if user_init is object.__init__ or not callable(user_init):
            user_init = None

        def init(self, *args: _typing.Any, **kwargs: _typing.Any) -> None:
            # noinspection PyTypeChecker
            mcs._init_instance(tp, self, args, kwargs)

            if user_init is not None:
                user_init(self, *args, *kwargs)

        tp.__init__ = init

        if mcs._route_set_attribute():
            inner_set_attribute = getattr(tp, '__setattr__', None)

            def setattrib(self, name: str, value: _typing.Any) -> None:
                mcs._handle_set_attribute(self, name, value, inner_set_attribute)

            tp.__setattr__ = setattrib

        return tp

    @classmethod
    def _make_field(cls, name: str, annotation: _typing.Any, has_default: bool, default: _typing.Any) -> TField:
        if has_default and isinstance(default, Field):
            return default

        return Field(name, annotation=annotation, has_default=has_default, default=default)

    @classmethod
    def _postprocess_fields(cls, fields: dict[str, Field]) -> None:
        pass

    @classmethod
    def _check_overrides(cls, base_type: type[DataclassMetaBase], fields: _types.MappingProxyType[str, Field]) -> None:
        cls_fields = base_type.__fields__
        for k in cls_fields.keys() & fields.keys():
            v = cls_fields[k]

            v.check_override(fields[k])

    @classmethod
    def _route_set_attribute(cls) -> bool:
        return False

    @classmethod
    def _handle_set_attribute(
        cls,
        self: _typing.Any,
        name: str,
        value: _typing.Any,
        inner_set_attribute: _typing.Callable[[str, _typing.Any], None] | None,
    ) -> None:

        if inner_set_attribute is None:
            self.__dict__[name] = value
        else:
            inner_set_attribute(name, value)

    @classmethod
    def _init_instance(
        cls,
        tp: type[DataclassMetaBase],
        self: _typing.Any,
        args: tuple[_typing.Any, ...],
        kwargs: dict[str, _typing.Any],
    ) -> None:
        fields = tp.__fields__

        # Ensure that `args` and `kwargs` are not overlapping and point to existing fields

        if len(args) + len(kwargs) > len(fields):
            raise TypeError('The number of parameter values exceeds the number of fields of the instance.')

        if not (kwargs.keys() <= fields.keys()):
            raise TypeError(
                'The following parameters do not correspond to field names of the instance: '
                + ', '.join(kwargs.keys() - fields.keys())
                + '.'
            )

        if any(field_name in kwargs for arg, field_name in zip(args, fields)):
            raise TypeError(
                'Multiple assignments to the following fields: '
                + ', '.join(field_name for arg, field_name in zip(args, fields) if field_name in kwargs)
                + '.'
            )

        if any(not f.has_default and i >= len(args) and f.name not in kwargs for i, f in enumerate(fields.values())):
            raise TypeError(
                'Missing assignment for the following fields: '
                + ', '.join(
                    f.name
                    for i, f in enumerate(fields.values())
                    if not f.has_default and i >= len(args) and f.name not in kwargs
                )
                + '.'
            )

        # gather the assignments

        assignments = dict()

        for field, v in zip(fields.values(), args):
            field.check_assignment(v)

            assignments[field.name] = v

        for k, v in kwargs.items():
            field = fields[k]

            field.check_assignment(v)

            assignments[k] = v

        for k, field in fields.items():
            if k not in assignments:
                field.check_assignment(field.default)
                assignments[k] = field.default

        # assign on current instance
        for k, v in assignments.items():
            setattr(self, k, v)

        # invoke postinit, if available
        postinit = getattr(self, '__postinit__', None)
        if postinit is not None and callable(postinit):
            postinit()


@_typing.dataclass_transform(field_specifiers=(Field,))
class DataclassMeta[TField: Field](DataclassMetaBase[TField]):
    pass
