import types as _types
import typing as _typing

from ._util import E as _E
from ._util import throws as _throws


class FieldInitializer[**P, TField: Field](_typing.Protocol):
    """
    A generic factory that creates a new field from a name, an annotation, and additional parameters defined via the
    signature defined via `P`.

    Any such initializer must take the name and annotation as its first two positional arguments.
    """

    # remark: this is less restrictive than `FieldFactory` which requires an exact match between the signature of
    # `Field.__init__` and its `__call__`
    def __call__(self, __name: str, __annotation: _typing.Any, /, *args: P.args, **kwargs: P.kwargs) -> TField:
        """
        Creates a new instance of the field.

        :param __name: The name of the field.
        :param __annotation: The annotation of the field.
        :param args: Any additional positional arguments.
        :param kwargs: Any additional keyword arguments.
        """
        ...


class Field:
    """
    A class that describes a field of a dataclass-like class.

    See :py:func:`make_dataclass` for instructions of how to use subclasses of :class:`Field` to further constrain and
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

    @classmethod
    def declare[**P, TField: Field](
        cls: FieldInitializer[P, TField], *args: P.args, **kwargs: P.kwargs
    ) -> FieldDeclaration[P, TField]:
        """
        Declares, but does not fully initialize a field. The field will be instantiated when the dataclass gets built.

        Use this function to explicitly specify a field instance instead of letting it get initialized implicitly.

        Example:
        >>> class Dataclass(DataclassMeta):
        ...     x: list = Field.declare(default_factory=list)

        :param args: Positional arguments to supply to `__factory` after the values for `name` and `annotation`.
        :param kwargs: Additional keyword arguments to supply to `__factory`.
        :return: The generated field declaration.
        """
        return field(cls, *args, **kwargs)


class FieldDeclaration[**P, TField: Field]:
    """Declares, but does not fully initialize a field. The field will be instantiated when the dataclass gets built."""

    def __init__(self, __factory: FieldInitializer[P, TField], /, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Initializes the current instance.

        :param __factory: The factory that converts the declaration into an actual field.
        :param args: Positional arguments to supply to `__factory` after the values for `name` and `annotation`.
        :param kwargs: Additional keyword arguments to supply to `__factory`.
        """
        self._factory = __factory
        self._args = args
        self._kwargs = kwargs

    def __call__(self, name: str, annotation: _typing.Any) -> TField:
        """
        Instantiates the field from the declaration represented by the current instance.

        :param name: The name to use for the field.
        :param annotation: The annotation to use for the field.
        :return: The instantiated field.
        """
        return self._factory(name, annotation, *self._args, **self._kwargs)


def field[**P, TField: Field](
    __cls: FieldInitializer[P, TField] = Field,  # type: ignore[assignment]
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> FieldDeclaration[P, TField]:
    """
    Declares, but does not fully initialize a field. The field will be instantiated when the dataclass gets built.

    Use this function to explicitly specify a field instance instead of letting it get initialized implicitly. For
    derived field types, consider :py:func:`Field.declare`.

    Example:
    >>> class Dataclass(DataclassMeta):
    ...     x: list = field(default_factory=list)

    :param __cls: The field type or, more general, a factory that generates the field.
    :param args: Positional arguments to supply to `__factory` after the values for `name` and `annotation`.
    :param kwargs: Additional keyword arguments to supply to `__factory`.
    :return: The generated field declaration.
    """

    return FieldDeclaration(__cls, *args, **kwargs)


class _Unspecified:
    """The class is used as a singleton together with dictionaries."""

    pass


class FieldFactory[TField: Field](_typing.Protocol):
    """A protocol that behaves similar to the factory represented by the :class:`Field` type."""

    def __call__(
        self,
        name: str,
        annotation: _typing.Any,
        has_default: bool = False,
        default: _typing.Any = None,
        default_factory: _typing.Callable[[], None] | None = None,
    ) -> TField:
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
        ...


class FieldProvider[TField: Field]:
    """Handles the creation and override behavior of fields."""

    def __init__(
        self,
        field_factory: FieldFactory[TField] = Field,  # type: ignore[assignment]
        external_field_validator: _E[type[TField] | _typing.Callable[[Field], TField]] = ...,
    ) -> None:
        """
        Initializes the current instance.

        :param field_factory: The factory used to initialize a field. It must have the same signature as the initializer
            of the :class:`Field` class.
        :param external_field_validator: Used to validate fields that were externally supplied. Either specify a
            field type, or a handler to invoke. If not supplied, `field_factory` is used if it is a type. If
            `field_factory` is not a type, `external_field_validator` must be explicitly set to a value.
        """

        if external_field_validator is ...:
            if not isinstance(field_factory, type):
                raise ValueError(
                    'If `field_factory` is not a type, `external_field_validator` must be indicated explicitly.'
                )

            external_field_validator = field_factory  # type: ignore[assignment]

        self._field_factory = field_factory
        self._external_field_validator = external_field_validator

    def _validate_field(self, field: Field) -> TField:
        """
        Validates an externally defined field and (unsafely) casts it to `TField`.

        :param field: The field to validate.
        :return: The converted field.
        """
        if isinstance(self._external_field_validator, type):
            if not isinstance(field, self._external_field_validator):
                raise TypeError(f'Field `{field.name}` was set to a value of an unsupported type.')

            return _typing.cast(TField, field)

        return self._external_field_validator(field)  # type: ignore

    def instantiate_field[**P](
        self, name: str, annotation: _typing.Any, declaration: FieldDeclaration[P, TField]
    ) -> TField:
        """
        Instantiates a field from a field declaration.

        :param name: The name of the field.
        :param annotation: The annotation of the field.
        :param declaration: Additional parameters to supply to the field type.
        :return: The instantiated field.
        """
        return self._validate_field(declaration(name, annotation))

    def make_field(self, name: str, annotation: _typing.Any, has_default: bool, default: _typing.Any) -> TField:
        """
        Initializes a new field.

        :param name: The name of the field.
        :param annotation: The annotation the field was declared with.
        :param has_default: Indicates whether the field has a default value or not.
        :param default: The default value of the field.
        :return: The field created for the given parameters.
        """
        if has_default:
            if isinstance(default, Field):
                return self._validate_field(default)
            elif isinstance(default, FieldDeclaration):
                return self.instantiate_field(name, annotation, default)

        return self._field_factory(name, annotation=annotation, has_default=has_default, default=default)

    def create_field_override(self, original: Field) -> TField:
        """
        Creates a new field from an original field declared on a base class.

        :param original: The original field.
        :return: The new field.
        """
        return self._field_factory(
            original.name,
            annotation=original.annotation,
            has_default=original.has_default,
            default=original.default,
            default_factory=original.default_factory,
        )

    def check_overrides(
        self, base_fields: _types.MappingProxyType[str, Field], cls_fields: _types.MappingProxyType[str, Field]
    ) -> None:
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
        cls: DataclassType[TField],
        obj: _typing.Any,
        args: tuple[_typing.Any, ...],
        kwargs: dict[str, _typing.Any],
    ) -> None:
        """
        Initializes the instance given positional and keyword arguments. The positional and keyword arguments get mapped
        to their respective fields.

        This method gets called during the `__init__` method call of `obj`.

        :param cls: The class of the object to initialize.
        :param obj: The object to initialize.
        :param args: The positional arguments.
        :param kwargs: The keyword arguments.
        """
        fields = cls.__dataclass_fields__

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

        obj.__dataclass_initialized__ = False

        # assign on current instance
        for k, v in assignments.items():
            setattr(obj, k, v)

        obj.__dataclass_initialized__ = True

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
        inner_set_attribute: _typing.Callable[[_typing.Any, str, _typing.Any], None] | None,
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
        if field is not None and obj.__dataclass_initialized__:
            field.check_assignment(value)

        if inner_set_attribute is None:
            obj.__dict__[name] = value
        else:
            inner_set_attribute(obj, name, value)

    @property
    def override_set_attribute(self) -> bool:
        """
        Indicates whether the `__setattr__` behavior is to be overridden to route to the
        :py:func:`handle_set_attribute`-method. Defaults to `True`.

        Typically, set-attribute gets overridden, since assignments to fields need be checked. In some cases, however,
        this behavior may not be required (e.g., if the dataclass is to be frozen, anyway).

        :return: `True` if `__setattr__` is to be overridden, `False` otherwise.
        """
        return True

    def handle_delete_attribute(
        self,
        obj: _typing.Any,
        field: Field | None,
        name: str,
        inner_delete_attribute: _typing.Callable[[_typing.Any, str], None] | None,
    ) -> None:
        """
        This method gets called when `__delattr__` is invoked for an object.

        :param obj: The object on which the attribute gets deleted.
        :param field: The field whose attribute gets deleted.
        :param name: The name of the attribute of the field.
        :param inner_delete_attribute: The original `__delattr__`-procedure, if there was one; `None` otherwise.
        """
        if field is not None:
            raise RuntimeError('The deletion of attributes is not allowed for dataclass fields.')

        if inner_delete_attribute is not None:
            inner_delete_attribute(obj, name)

    @property
    def override_delete_attribute(self) -> bool:
        """
        Indicates whether the `__delattr_` behavior is to be overridden to route the
        :py:func:`handle_delete_attribute`-method. Defaults to `True`.

        Typically, delete-attribute gets overridden to prevent users from deleting attributes from the dataclasses.
        :return: `True` if `__delattr__` is to be overridden, `False` otherwise.
        """
        return True


def make_dataclass[TField: Field](
    cls: type,
    field_provider: _E[FieldProvider[TField] | FieldFactory[TField]] = ...,
    object_handler: _E[ObjectHandler[TField]] = ...,
) -> None:
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
    elif not isinstance(field_provider, FieldProvider):
        # create the field provider from a `FieldFactory` object
        field_provider = FieldProvider(field_provider)

    if object_handler is ...:
        object_handler = ObjectHandler()

    field_map = _gather_fields(cls, field_provider)

    cls.__dataclass_fields__ = field_map  # type: ignore[attr-defined]

    # check with all bases (that are not metaclasses) that our overrides are valid
    for base in cls.__bases__:
        if isinstance(base, DataclassMetaBase):
            field_provider.check_overrides(base.__dataclass_fields__, field_map)

    # determine the new `__init__` procedure. The old one gets called, too, if there is one (different from the one of
    # `object`)
    user_init = getattr(cls, '__init__', None)

    if user_init is object.__init__ or not callable(user_init):
        user_init = None

    def init(self: _typing.Any, *args: _typing.Any, **kwargs: _typing.Any) -> None:
        # noinspection PyTypeChecker
        object_handler.init_instance(cls, self, args, kwargs)  # type: ignore[arg-type]

        if user_init is not None:
            user_init(self, *args, *kwargs)

    cls.__init__ = init  # type: ignore[misc]

    if object_handler.override_set_attribute:
        inner_set_attribute = getattr(cls, '__setattr__', None)

        def setattrib(self: _typing.Any, key: str, value: _typing.Any) -> None:
            field = field_map.get(key)
            object_handler.handle_set_attribute(self, field, key, value, inner_set_attribute)

        cls.__setattr__ = setattrib  # type: ignore[method-assign, assignment]

    if object_handler.override_delete_attribute:
        inner_del_attribute = getattr(cls, '__delattr__', None)

        def delattrib(self: _typing.Any, item: str) -> None:
            field = field_map.get(item)
            object_handler.handle_delete_attribute(self, field, item, inner_del_attribute)

        cls.__delattr__ = delattrib  # type: ignore[method-assign, assignment]


@_typing.overload
def dataclass[TField: Field, TCls: type](
    *,
    field_provider: _E[FieldProvider[TField] | FieldFactory[TField]] = ...,
    object_handler: ObjectHandler[TField] = ...,
) -> _typing.Callable[[TCls], TCls]:
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
def dataclass[TField: Field, TCls: type](
    cls: TCls,
    /,
    field_provider: _E[FieldProvider[TField] | FieldFactory[TField]] = ...,
    object_handler: ObjectHandler[TField] = ...,
) -> TCls:
    """
    Makes the indicated class dataclass-like. The class must not be a dataclass, yet.

    :param cls: The class to make a dataclass.
    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    """
    ...


def dataclass[TField: Field, TCls: type](
    cls: _E[TCls] = ...,
    /,
    field_provider: _E[FieldProvider[TField] | FieldFactory[TField]] = ...,
    object_handler: _E[ObjectHandler[TField]] = ...,
) -> TCls | _typing.Callable[[TCls], TCls]:
    if cls is ...:

        def handle[T: type](cls: T) -> T:
            make_dataclass(cls, field_provider, object_handler)
            return cls

        return handle
    else:
        make_dataclass(cls, field_provider, object_handler)
        return cls


def _gather_fields[TField: Field](
    cls: type, field_provider: FieldProvider[TField]
) -> _types.MappingProxyType[str, TField]:
    """
    Gathers the fields of a dataclass from the annotations of its MRO.

    :param cls: The class from which to determine the fields.
    :param field_provider: The field provider used to initialize the fields.
    :return: The mapping of field names to fields.
    """
    field_dict = {}

    # 1. gather the fields from the base classes

    for stp in reversed(cls.__mro__[1:]):
        fields = getattr(stp, '__dataclass_fields__', None)

        if fields is not None:
            field_dict.update(fields)

    # 2. create new field representations of fields that we inherited from base classes

    annotations = cls.__annotations__

    for k, field in field_dict.items():
        if k in annotations:
            # we leave out those that'll receive an annotation in 3.
            continue

        field_dict[k] = field_provider.create_field_override(field)

    # 3. create the fields defined via annotations on the current instance
    for k, annot in annotations.items():
        default = getattr(cls, k, _Unspecified)

        field = field_provider.make_field(
            k, annot, default is not _Unspecified, None if default is _Unspecified else default
        )

        field_dict[k] = field

    if any(field.name != k for k, field in field_dict.items()):
        raise ValueError('The field names must be preserved by the operations of the field provider.')

    return _types.MappingProxyType(field_dict)


class DataclassMetaBase[TField: Field](type):
    """
    A base class for metaclasses inducing dataclass-like behavior. The :py:func:`make_dataclass` gets invoked on
    subclasses.

    Note that this class is not intended to be used directly as a metaclass. The :py:func:`typing.dataclass_transform`
    method is not applied to the current type since it requires specific field specifiers. In derived classes, however,
    the field specifiers may not be limited to the :class:`Field`-class. Therefore, you should define a metaclass that
    is derived from the :class:`DataclassMetaBase` class if you want to define a class with custom field specifiers and
    add a :py:func:`typing.dataclass_transform`-decoration to them. Use the :py:func:`_field_provider` to control the
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


@_typing.runtime_checkable
class DataclassType[TField](_typing.Protocol):
    """A protocol that describes the members of dataclass-like classes."""

    __dataclass_fields__: _typing.Mapping[str, TField]
    """The fields of the dataclass."""


class TypeConstrainedField(Field):
    """
    A field that can be used to provide simple `isinstance`-based type checking using the field's annotation.

    The annotation must provide an `__instancecheck__` to perform assignment checks. Note that the instance check gets
    invoked once with `None` during initialization to eliminate the .
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
        :param annotation: The annotation of the field. This must provide a suitable `__instancecheck__` method.
        :param has_default: Indicates whether the field has a default value, which is then specified in the
            ``default``-parameter or the ``default_factory`` parameter. If ``True``, either ``default`` or
            ``default_factory`` is to be set to a value.
        :param default: If ``has_default`` is ``True``, this may specify a constant default value the field takes on.
            If ``has_default`` is ``False`` or ``default_factory`` is set to a value, this must be ``None``.
        :param default_factory: If ``has_default`` is ``True``, this may specify a factory that generates a default
            value for the field.
            If ``has_default`` is ``False`` or ``default`` is set to a value, this must be ``None``.
        """
        instance_check = getattr(annotation, '__instancecheck__', None)

        if instance_check is None or _throws(lambda: instance_check(None), TypeError, ValueError):
            raise TypeError('`annotation` must provide an `__instancecheck__` method usable for type checking.')

        super().__init__(name, annotation, has_default, default, default_factory)

        self._instance_check = instance_check

    def check_assignment(self, obj: _typing.Any) -> None:
        if not self._instance_check(obj):
            raise TypeError(f'The object is not a valid assignment to field `{self.name}`.')
