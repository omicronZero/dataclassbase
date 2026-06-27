import types as _types
import typing as _typing


class Field:
    """
    A class that describes a field of a dataclass-like class.

    See :class:`DataclassMetaBase` for instructions of how to use subclasses of :class:`Field` to further constrain and
    modify fields. Any member of instances of derived subclasses should be intended to be immutable.
    """

    def __init__(
            self,
            name: str,
            annotation: _typing.Any,
            has_default: bool = False,
            default: _typing.Any = None,
            default_factory: _typing.Callable[[], None] | None = None,
    ) -> None:
        """
        Initializes the current instance.

        :param name: The name of the field. This must be a valid Python identifier.
        :param annotation: The annotation of the field.
        :param has_default: Indicates whether the field has a default value, which is then specified in the
            ``default``-parameter or the ``default_factory`` parameter. If ``True``, either ``default`` or
            ``default_factory`` is to be set to a value.
        :param default: If ``has_default`` is ``True``, this may specify a constant default value the field takes on.
            If ``has_default`` is ``False`` or ``default_factory`` is set to a value, this must be ``None``.
        :param default_factory: If ``has_default`` is ``True``, this may specify a factory that generates a default
            value for the field.
            If ``has_default`` is ``False`` or ``default`` is set to a value, this must be ``None``.
        """
        if not has_default and default is not None:
            raise ValueError('If `has_default` is `False`, `default` must be `None`.')
        if default_factory is not None and default is not None:
            raise ValueError('If `default_factory` is set to a value, `default_factory` must be `None`.')

        if not name.isidentifier():
            raise ValueError('The name of the field must be a valid identifier.')

        self._name = name
        self._has_annotation = annotation
        self._annotation = annotation
        self._has_default = has_default
        self._default = default

    @property
    def name(self) -> str:
        """
        The name of the field.

        :return: The name.
        """
        return self._name

    @property
    def annotation(self) -> _typing.Any:
        """
        The annotation hinting at the type of field.

        :return: The annotation.
        """
        return self._annotation

    @property
    def has_default(self) -> bool:
        """
        Indicates whether the current field has a constant default value indicated via :py:func:`default_factory` or
        a default value factory indicated via :py:func:`default_factory`. If :py:func:`has_default` is `True`,
        either :py:func:`default_factory` is not ``None``, implying that the :py:func:`default_factory` provides the
        default value, or :py:func:`default` is to be used as the default value.

        :return: A value indicating whether the current field has a default value.
        """
        return self._has_default

    @property
    def default_factory(self) -> _typing.Callable[[], _typing.Any] | None:
        """
        If :py:func:`has_default` is set to `True`, this may provide a factory responsible for the generation of default
        values.

        See :py:func:`has_default` for further information.

        :return: `None` if either :py:func:`has_default` is `False` or :py:func:`default` provides a constant default
            value, or, otherwise, a factory function generating a default value.
        """
        return None

    @property
    def default(self) -> _typing.Any:
        """
        If :py:func:`has_default` is set to `True`, this provides a constant default value unless
        :py:func:`default_factory` is not `None`.

        See :py:func:`has_default` for further information.

        :return: `None` if :py:func:`has_default` is `False` or :py:func:`default_factory` is set to a value different
            from `None`. Otherwise, this provides a constant default value.
        """
        return self._default

    def check_assignment(self, obj: _typing.Any) -> None:
        """
        In derived classes, this checks whether an assignment `obj` to the current field is suitable for the class.

        By convention, the function must raise either a :class:`TypeError` or a :class:`ValueError` for invalid values.

        :param obj: The assignment made to the current field.
        """
        pass

    def check_overriding_field(self, overriding_field: Field) -> None:
        """
        In derived classes, this checks whether a field override overriding the current field is valid.
        This can, for example, be used to ensure that an overriding field allows only assignments that are also accepted
        by the current instance.

        In combination with :py:func:`check_overridden_field`, this provides a mechanism ensuring integrity on derived
        fields.

        By convention, the function must raise either a :class:`TypeError` or a :class:`ValueError` for invalid values.

        :param overriding_field: The field that is to override the current instance.
        """
        pass

    def check_overridden_field(self, overridden_field: Field) -> None:
        """
        In derived classes, this checks whether the current field can override another field.

        In combination with :py:func:`check_overriding_field`, this provides a mechanism ensuring integrity on derived
        fields.

        By convention, the function must raise either a :class:`TypeError` or a :class:`ValueError` for invalid values.

        :param overridden_field: The field to be overridden.
        """
        pass


class _Unspecified:
    """The class is used as a singleton together with dictionaries."""
    pass


class FieldProvider[TField: Field]:
    """Handles the creation and override behavior of fields."""

    def make_field(self, name: str, annotation: _typing.Any, has_default: bool, default: _typing.Any) -> TField:
        """
        Initializes a new field.

        :param name: The name of the field.
        :param annotation: The annotation the field was declared with.
        :param has_default: Indicates whether the field has a default value or not.
        :param default: The default value of the field.
        :return: The field created for the given parameters.
        """
        if has_default and isinstance(default, Field):
            return default

        return Field(name, annotation=annotation, has_default=has_default, default=default)

    def check_overrides(self,
                        base_fields: _types.MappingProxyType[str, Field],
                        cls_fields: _types.MappingProxyType[str, Field]) -> None:
        """
        Checks whether a combination of base and child fields are valid.

        By default, this method uses the :py:func:`Field.check_overriding_field` and
        :py:func:`Field.check_overridden_field` methods of :class:`Field`.

        :param base_fields: The fields of the base. These are the fields that get overridden.
        :param cls_fields: The fields of the child. These are the fields that override the base fields.
        :return:
        """
        for k in base_fields.keys() & cls_fields.keys():
            v = base_fields[k]
            override = cls_fields[k]

            v.check_overriding_field(override)
            override.check_overridden_field(v)


class ObjectHandler[TField: Field]:
    """Handles the initialization and set-attribute behavior of a dataclass-like object."""

    def init_instance(
            self,
            tp: type[DataclassMetaBase],
            obj: _typing.Any,
            args: tuple[_typing.Any, ...],
            kwargs: dict[str, _typing.Any],
    ) -> None:
        """
        Initializes the instance given positional and keyword arguments. The positional and keyword arguments get mapped
        to their respective fields.

        This method gets called during the `__init__` method call of `obj`.

        :param tp: The class of the object to initialize.
        :param obj: The object to initialize.
        :param args: The positional arguments.
        :param kwargs: The keyword arguments.
        """
        fields = tp.__dataclass_fields__

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

        # gather the assignments as a dictionary

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
            setattr(obj, k, v)

        # invoke postinit, if available
        postinit = getattr(obj, '__postinit__', None)
        if postinit is not None and callable(postinit):
            postinit()

    def handle_set_attribute(
            self,
            obj: _typing.Any,
            field: Field | None,
            name: str,
            value: _typing.Any,
            inner_set_attribute: _typing.Callable[[str, _typing.Any], None] | None,
    ) -> None:
        """
        This method gets called when `__setattr__` is invoked for an object.

        :param obj: The object for which to set the field's value.
        :param field: The field that gets assigned a new value. If the attribute does not correspond to a field, this
            value is `None`.
        :param name: The name of the attribute to which the new value is assigned.
        :param value: The new value to assign to the attribute.
        :param inner_set_attribute: The original `__setattr__`-procedure, if there was one; `None` otherwise.
        """
        if field is not None:
            field.check_assignment(obj)

        if inner_set_attribute is None:
            obj.__dict__[name] = value
        else:
            inner_set_attribute(name, value)

    @property
    def route_set_attribute(self) -> bool:
        """
        Indicates whether the `__setattr__` behavior is to be overridden to route to the
        :py:func:`handle_set_attribute`-method.
        Typically, it should, since assignments to fields need be checked. In some cases, however, this behavior may not
        be required (e.g., if the dataclass is to be frozen, anyway).

        :return: `True` if `__setattr__` is to be overridden, `False` otherwise.
        """
        return False


def make_dataclass[TField: Field](cls: type,
                                  field_provider: FieldProvider[TField] = ...,
                                  object_handler: ObjectHandler[TField] = ...) -> None:
    """
    Makes the indicated class dataclass-like. The class must not be a dataclass, yet.

    :param cls: The class to make a dataclass.
    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    """
    if '__dataclass_fields__' in cls.__dict__:
        raise TypeError('The indicated type already is a dataclass.')

    if field_provider is ...:
        field_provider = FieldProvider()

    if object_handler is ...:
        object_handler = ObjectHandler()

    field_map = _gather_fields(cls, field_provider)

    cls.__dataclass_fields__ = field_map

    # check with all bases (that are not metaclasses) that our overrides are valid
    for base in cls.__bases__:
        if issubclass(base, DataclassMetaBase):
            field_provider.check_overrides(base.__dataclass_fields__, field_map)

    # determine the new `__init__` procedure. The old one gets called, too, if there is one (different from the one of
    # `object`)
    user_init = getattr(cls, '__init__', None)

    if user_init is object.__init__ or not callable(user_init):
        user_init = None

    def init(self, *args: _typing.Any, **kwargs: _typing.Any) -> None:
        # noinspection PyTypeChecker
        object_handler.init_instance(cls, self, args, kwargs)

        if user_init is not None:
            user_init(self, *args, *kwargs)

    cls.__init__ = init

    if object_handler.route_set_attribute:
        inner_set_attribute = getattr(cls, '__setattr__', None)

        def setattrib(self, name: str, value: _typing.Any) -> None:
            field = field_map.get(name)
            object_handler.handle_set_attribute(self, field, name, value, inner_set_attribute)

        cls.__setattr__ = setattrib


@_typing.overload
def dataclass[TField: Field, TCls: type](*,
                                         field_provider: FieldProvider[TField] = ...,
                                         object_handler: ObjectHandler[TField] = ...) -> _typing.Callable[[TCls], TCls]:
    """
    Returns a function that that makes the classes supplied to it dataclass-like. The classes must not be dataclasses,
    yet.

    Intended to be used as a decorator.

    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    """
    ...


@_typing.overload
def dataclass[TField: Field, TCls: type](cls: TCls, /,
                                         field_provider: FieldProvider[TField] = ...,
                                         object_handler: ObjectHandler[TField] = ...) -> TCls:
    """
    Makes the indicated class dataclass-like. The class must not be a dataclass, yet.

    :param cls: The class to make a dataclass.
    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    """
    ...


def dataclass[TField: Field, TCls: type](cls: TCls = ..., /,
                                         field_provider: FieldProvider[TField] = ...,
                                         object_handler: ObjectHandler[TField] = ...) \
        -> TCls | _typing.Callable[[TCls], TCls]:
    if cls is ...:
        def handle[T: type](cls: T) -> T:
            make_dataclass(cls, field_provider, object_handler)
            return cls

        return handle
    else:
        make_dataclass(cls, field_provider, object_handler)
        return cls


def _gather_fields[TField: Field](cls: type,
                                  field_provider: FieldProvider[TField]) \
        -> _types.MappingProxyType[str, TField]:
    """
    Gathers the fields of a dataclass from the annotations of its MRO.

    :param cls: The class from which to determine the fields.
    :param field_provider: The field provider used to initialize the fields.
    :return: The mapping of field names to fields.
    """
    fields = []

    # 1. gather the annotations from the MRO (`cls` itself is in the MRO)
    annotations = {}

    for stp in reversed(cls.__mro__):
        if not isinstance(stp, DataclassMetaBase):
            continue

        annot = getattr(stp, '__annotations__', None)

        if isinstance(annot, dict):
            annotations.update(annot)

    # 2. create fields for the gathered annotations. A valid field *requires* an annotation.
    for k, annot in annotations.items():
        default = getattr(cls, k, _Unspecified)

        field = field_provider.make_field(k,
                                          annot,
                                          default is not _Unspecified,
                                          None if default is _Unspecified else default)

        fields.append(field)

    field_dict = {field.name: field for field in fields}

    return _types.MappingProxyType(field_dict)


class DataclassMetaBase[TField: Field](type):
    """
    A base class for metaclasses inducing dataclass-like behavior. The :py:func:`make_dataclass` gets invoked on
    subclasses.

    Note that this class is not intended to be used directly as a metaclass. The :py:func:`typing.dataclass_transform`
    method is not applied to the current type since it requires specific field specifiers. In derived classes, however,
    the field specifiers may not be limited to the :class:`Field`-class. Therefore, you should define a metaclass that
    is derived from the :class:`DataclassMetaBase` class if you want to define a class with custom field specifiers and
    add a :py:func:`typing.dataclass_transform`-decoration to them. Use the :py:method:`_field_provider` to control the
    conversion of the field specifies into fields.
    """
    __dataclass_fields__: _types.MappingProxyType[str, Field]

    def __new__(mcs, name: str, bases: tuple[type, ...], dct: dict[str, _typing.Any]) -> type:
        cls = type.__new__(mcs, name, bases, dct)

        make_dataclass(cls, mcs._field_provider(), mcs._object_handler())

        return cls

    @classmethod
    def _field_provider(cls) -> FieldProvider[TField]:
        """
        The field provider to use to control the creation and override behavior of fields.

        :return: The field provider.
        """
        return FieldProvider()

    @classmethod
    def _object_handler(cls) -> ObjectHandler[TField]:
        """
        The object handler to use to control the object initialization and set-attribute behavior.

        :return: The object handler.
        """
        return ObjectHandler()


@_typing.dataclass_transform(field_specifiers=(Field,))
class DataclassMeta[TField: Field](DataclassMetaBase[TField]):
    """
    Provides a basic :class:`Field`-based metaclass. When used as a metaclass, the class and any subclass inherit a
    dataclass-like behavior. See :class:`DataclassMetaBase` and :py:func:`make_dataclass` for further information.
    """
    pass
