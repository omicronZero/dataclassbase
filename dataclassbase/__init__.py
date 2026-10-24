import abc as _abc
import types as _types
import typing as _typing

from . import _util
from ._util import E as _E
from ._util import throws as _throws


class FieldInitializer[**P](_typing.Protocol):
    """
    A generic factory that creates a new field from a name, an annotation, and additional parameters defined via the
    signature defined via `P`.

    Any such initializer must take the name and annotation as its first two positional arguments.
    """

    # remark: this is less restrictive than `FieldFactory` which requires an exact match between the signature of
    # `Field.__init__` and its `__call__`
    def __call__(self, __name: str, __annotation: _typing.Any, /, *args: P.args, **kwargs: P.kwargs) -> Field:
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
    def declare[**P](cls: FieldInitializer[P], *args: P.args, **kwargs: P.kwargs) -> FieldDeclaration[P]:
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


class FieldDeclaration[**P]:
    """Declares, but does not fully initialize a field. The field will be instantiated when the dataclass gets built."""

    def __init__(self, __factory: FieldInitializer[P], /, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Initializes the current instance.

        :param __factory: The factory that converts the declaration into an actual field.
        :param args: Positional arguments to supply to `__factory` after the values for `name` and `annotation`.
        :param kwargs: Additional keyword arguments to supply to `__factory`.
        """
        self._factory = __factory
        self._args = args
        self._kwargs = kwargs

    def __call__(self, name: str, annotation: _typing.Any) -> Field:
        """
        Instantiates the field from the declaration represented by the current instance.

        :param name: The name to use for the field.
        :param annotation: The annotation to use for the field.
        :return: The instantiated field.
        """
        return self._factory(name, annotation, *self._args, **self._kwargs)


def field[**P](
    __cls: FieldInitializer[P] = Field,  # type: ignore[assignment]
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> FieldDeclaration[P]:
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


@_typing.runtime_checkable
class DataclassType(_typing.Protocol):
    """A protocol that describes the members of dataclass-like classes."""

    __dataclassbase_fields__: _util.MappingProto[str, Field]
    """The fields of the dataclass."""

    def __call__(self, *args: _typing.Any, **kwargs: _typing.Any) -> _typing.Self:
        """
        Initializes the dataclass.

        :param args: The positional arguments to initialize the dataclass type with.
        :param kwargs: The keyword arguments to initialize the dataclass type with.
        """
        ...


class _Unspecified:
    """The class is used as a singleton together with dictionaries."""

    pass


class FieldFactory(_typing.Protocol):
    """A protocol that behaves similar to the factory represented by the :class:`Field` type."""

    def __call__(
        self,
        name: str,
        annotation: _typing.Any,
        has_default: bool = False,
        default: _typing.Any = None,
        default_factory: _typing.Callable[[], None] | None = None,
    ) -> Field:
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


class Fields(_typing.NamedTuple):
    """Represents a pair of declared and inherited fields of a type."""

    declared_fields: dict[str, Field]
    """The fields declared on the type itself."""

    inherited_fields: dict[str, Field]
    """The fields inherited from a base type."""

    def all(self) -> dict[str, Field]:
        """
        Merges the inherited and declared fields and returns the resulting dictionary.

        :return: The dictionary of pairs mapping field names to fields.
        """
        result = self.inherited_fields.copy()
        result.update(self.declared_fields)
        return result

    @staticmethod
    def from_lists(declared_fields: list[Field], inherited_fields: list[Field]) -> Fields:
        return Fields(
            {field.name: field for field in declared_fields}, {field.name: field for field in inherited_fields}
        )


class FieldProvider(_abc.ABC):
    """Defines an abstract class for handling the creation and override behavior of fields."""

    def contextualize(self, cls: type, modifiers: tuple[BehaviorModifier, ...]) -> FieldProvider:
        """
        Returns a field provider to be used together with the indicated type. By default, this returns the current
        instance.

        :param cls: The type to be turned into a dataclass.
        :param modifiers: The modifiers the dataclass has been initialized with.
        :return: The field provider to be used together with the indicated type.
        """
        return self

    def check_overrides(
        self, base_fields: _types.MappingProxyType[str, Field], cls_fields: _types.MappingProxyType[str, Field]
    ) -> None:
        """
        Checks whether a combination of base and child fields are valid.

        By default, this method uses the :py:func:`Field.check_overriding_field` and
        :py:func:`Field.check_overridden_field` methods of :class:`Field`.

        :param base_fields: The fields of the base. These are the fields that get overridden.
        :param cls_fields: The fields of the child. These are the fields that override the base fields.
        """
        for k in base_fields.keys() & cls_fields.keys():
            v = base_fields[k]
            override = cls_fields[k]

            v.check_overriding_field(override)
            override.check_overridden_field(v)

    def gather_fields(self, cls: type) -> Fields:
        """
        Gathers the dataclass fields of a class.

        :param cls: The class from which to determine the fields.
        :return: The mapping of field names to fields.
        """
        field_dict = self._gather_fields_core(cls)

        if not field_dict.declared_fields.keys().isdisjoint(field_dict.inherited_fields):
            raise ValueError('The field names of the declared and inherited fields must be disjoint.')

        for src in (field_dict.inherited_fields, field_dict.declared_fields):
            if any(field.name != k for k, field in src.items()):
                raise RuntimeError('The field names must be preserved by the operations of the field provider.')

        return field_dict

    @_abc.abstractmethod
    def _gather_fields_core(self, cls: type) -> Fields:
        """
        Performs the core logic for gathering the dataclass fields of a class.

        :param cls: The class from which to determine the fields.
        :return: The mapping of field names to fields.
        """
        ...


def _skip_annotation(cls: type, key: str, value: _typing.Any) -> bool:
    """
    Helper function used to determine whether an annotation is to be skipped.

    :param cls: The dataclass to be constructed.
    :param key: The key of the annotation.
    :param value: The value of the annotation.
    :return: `True` if the annotation is to be skipped, `False` if it refers to a dataclass variable.
    """
    return _typing.get_origin(value) is _typing.ClassVar


class BasicFieldProvider(FieldProvider):
    """Implements a basic mechanism for handling the creation and override behavior of fields."""

    def __init__(
        self,
        field_factory: FieldFactory = Field,
        external_field_validator: _E[type[Field] | _typing.Callable[[Field], Field]] = ...,
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

    def _validate_field(self, field: Field) -> Field:
        """
        Validates an externally defined field and (unsafely) casts it to `Field`.

        :param field: The field to validate.
        :return: The converted field.
        """
        if isinstance(self._external_field_validator, type):
            if not isinstance(field, self._external_field_validator):
                raise TypeError(f'Field `{field.name}` was set to a value of an unsupported type.')

            return field

        return self._external_field_validator(field)  # type: ignore

    def instantiate_field[**P](self, name: str, annotation: _typing.Any, declaration: FieldDeclaration[P]) -> Field:
        """
        Instantiates a field from a field declaration.

        :param name: The name of the field.
        :param annotation: The annotation of the field.
        :param declaration: Additional parameters to supply to the field type.
        :return: The instantiated field.
        """
        return self._validate_field(declaration(name, annotation))

    def make_field(self, name: str, annotation: _typing.Any, has_default: bool, default: _typing.Any) -> Field:
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

    def create_field_override(self, original: Field) -> Field:
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

    def _gather_fields_core(self, cls: type) -> Fields:
        base_field_dict: dict[str, Field] = {}

        # 1. gather the fields from the base classes

        for base_type in reversed(cls.__mro__[1:]):
            fields = dataclass_fields(base_type, None)

            if fields is not None:
                base_field_dict.update(fields)

        # 2. create new field representations of fields that we inherited from base classes

        annotations = {k: v for k, v in cls.__annotations__.items() if not _skip_annotation(cls, k, v)}

        inherited: dict[str, Field] = {}
        declared: dict[str, Field] = {}

        for k, field in base_field_dict.items():
            if k in annotations:
                # we leave out those that'll receive an annotation in 3.
                continue

            inherited[k] = self.create_field_override(field)

        # 3. create the fields defined via annotations on the current instance
        for k, annot in annotations.items():
            default = getattr(cls, k, _Unspecified)

            field = self.make_field(k, annot, default is not _Unspecified, None if default is _Unspecified else default)

            declared[k] = field

        return Fields(declared, inherited)


@_typing.overload
def dataclass_fields(cls: DataclassType) -> _types.MappingProxyType[str, Field]: ...


@_typing.overload
def dataclass_fields[TOpt](cls: type, default: TOpt) -> _types.MappingProxyType[str, Field] | TOpt: ...


def dataclass_fields(cls: type | DataclassType, default: _typing.Any = _Unspecified) -> _typing.Any:
    result = getattr(cls, '__dataclassbase_fields__', default)

    if result is _Unspecified:
        raise ValueError('The indicated type is not a dataclass.')

    return result


class BehaviorModifier(_abc.ABC):
    """An abstract base class defining a mechanism for changing the behavior of a dataclass and its instances."""

    @_abc.abstractmethod
    def modify(
        self,
        cls: DataclassType,
        fields: _types.MappingProxyType[str, Field],
        declared_fields: _types.MappingProxyType[str, Field],
    ) -> None:
        """
        Applies the behavior modification to the indicated dataclass type.

        :param cls: The dataclass to modify.
        :param fields: All fields of the dataclass.
        :param declared_fields:
            The fields of the dataclass that were declared on the type itself rather than being inherited.
        """
        pass


class ConstructorlessFactory[T](_typing.Protocol):
    """A protocol that is used to declare functions that may take zero parameters."""

    def __call__(self) -> T:
        """
        Invokes the parameterless function.

        :return: The value returned by the function.
        """
        ...


class Frozen(BehaviorModifier):
    """Used to make dataclass fields immutable."""

    def __init__(self, fields_only: bool = True, freeze_inherited: bool = False) -> None:
        """
        Initializes the current instance.

        :param fields_only: Set to `True` to only freeze fields, set to `False` to freeze all attributes.
        :param freeze_inherited: Set to `True` to freeze inherited fields, too. Note that this parameter is ignored if
            `fields_only` is set to `True`.
        """
        self._fields_only = fields_only
        self._freeze_inherited = freeze_inherited

    @property
    def fields_only(self) -> bool:
        """
        Indicates whether the current class freezes only fields or all attributes.

        :return: `True` if only fields, `False` if all attributes get frozen.
        """
        return self._fields_only

    @property
    def freeze_inherited(self) -> bool:
        """
        Indicates whether the current class freezes all inherited fields, too.

        :return: `True` if parent fields get frozen, too, `False` otherwise.
        """
        return self._freeze_inherited

    def modify(
        self,
        cls: DataclassType,
        fields: _types.MappingProxyType[str, Field],
        declared_fields: _types.MappingProxyType[str, Field],
    ) -> None:
        """
        Makes the indicated dataclass frozen, i.e., after initialization, its fields may no longer be changed.

        :param cls: The dataclass to modify.
        :param fields: All fields of the dataclass.
        :param declared_fields:
            The fields of the dataclass that were declared on the type itself rather than being inherited.
        """
        inner_setattrib = getattr(cls, '__setattr__', None)
        inner_init = getattr(cls, '__init__', None)

        def setattrib(obj: _typing.Any, /, name: str, value: _typing.Any) -> None:
            initialized = getattr(obj, '__dataclassbase_initialized__', False)

            if initialized:
                passes = self.fields_only

                if passes and name in (fields if self.freeze_inherited else declared_fields):
                    passes = False

                if not passes:
                    raise RuntimeError('The current dataclass is frozen.')

            if inner_setattrib is not None:
                inner_setattrib(obj, name, value)

        cls.__setattr__ = setattrib  # type: ignore[assignment, method-assign]

        def init(obj: _typing.Any, /, *args: _typing.Any, **kwargs: _typing.Any) -> None:
            if getattr(obj, '__dataclassbase_initialized__', False):
                raise RuntimeError(
                    'The dataclass has already been initialized before. It cannot be reinitialized since it is frozen.'
                )

            if inner_init is not None:
                inner_init(obj, *args, **kwargs)

        cls.__init__ = init  # type: ignore[misc]


class Equatable(BehaviorModifier):
    """Used to add equality and inequality operators to the dataclasses."""

    def __init__(self, fields_only: bool = True, override_hash: bool = True, override_eq: bool = True) -> None:
        """
        Initializes the current instance.

        :param fields_only: Set to `True` to only consider fields or to `False` to include all attributes in the
            equality comparison.
        :param override_hash: Set to `True` to support :py:func:`hash` by providing an implementation for
            :py:func:`__hash__`. Note that this may be unsafe for mutable classes.
        :param override_eq: Set to `True` if equality and inequality operators are to be overridden on dataclasses
            whose behavior is modified by the current instance. This should typically be `True` unless you want to
            implement the behavior by yourself.
        """
        self._fields_only = fields_only
        self._override_hash = override_hash
        self._override_eq = override_eq

    @property
    def override_hash(self) -> bool:
        """
        Determines whether the current instance implements :py:func:`__hash__`. See :py:func:`__init__` for further
        information.

        :return: `True` if an implementation for :py:func:`__hash__` is generated, `False` if not.
        """
        return self._override_hash

    @property
    def override_eq(self) -> bool:
        """
        Determines whether the current instance implements the equality and inequality operators. See
        :py:func:`__init__` for further information.

        :return: `True` if the equality and inequality operators get implemented, `False` if not.
        """
        return self._override_eq

    @property
    def fields_only(self) -> bool:
        """
        Determines whether only the fields or all attributes are to be considered by the equality and inequality
        operators and the hash function, if provided.

        :return: `True` if only the fields, `False` if all attributes get considered.
        """
        return self._fields_only

    def modify(
        self,
        cls: DataclassType,
        fields: _types.MappingProxyType[str, Field],
        declared_fields: _types.MappingProxyType[str, Field],
    ) -> None:
        """
        Implements, if demanded, the equality and inequality operator and the hash function for the indicated type.

        :param cls: The dataclass to modify.
        :param fields: All fields of the dataclass.
        :param declared_fields:
            The fields of the dataclass that were declared on the type itself rather than being inherited.
        """
        if self.override_eq:

            def eq(obj: DataclassType, other: DataclassType, /) -> bool:
                if type(obj) is not type(other):
                    return False

                names: _typing.Iterable[str]

                if self.fields_only:
                    names = obj.__dict__.keys()

                    if names != other.__dict__.keys():
                        return False
                else:
                    names = cls.__dataclassbase_fields__

                for name in names:
                    if getattr(obj, name) != getattr(other, name):
                        return False

                return True

            def ne(obj: DataclassType, other: DataclassType) -> bool:
                return not eq(obj, other)

            cls.__eq__ = eq  # type: ignore[assignment]
            cls.__ne__ = ne  # type: ignore[assignment]

        if self.override_hash:

            def hashcode(obj: DataclassType) -> int:
                names: _typing.Iterable[str]

                if self.fields_only:
                    names = obj.__dict__.keys()
                else:
                    names = cls.__dataclassbase_fields__

                return hash(tuple(getattr(obj, name) for name in names))

            cls.__hash__ = hashcode  # type: ignore[assignment]


class KeywordOnly(BehaviorModifier):
    """Enforces that the parameters supplied to a dataclass are indicated via keyword."""

    def __init__(self) -> None:
        """Initializes the current instance."""
        pass

    def modify(
        self,
        cls: DataclassType,
        fields: _types.MappingProxyType[str, Field],
        declared_fields: _types.MappingProxyType[str, Field],
    ) -> None:
        """
        Modifies the initializer of the indicated class to allow only keyword arguments.

        :param cls: The dataclass to modify.
        :param fields: All fields of the dataclass.
        :param declared_fields:
            The fields of the dataclass that were declared on the type itself rather than being inherited.
        """
        inner_init = cls.__init__  # type: ignore[misc]

        def init(obj: _typing.Any, /, **kwargs: _typing.Any) -> None:
            inner_init(obj, **kwargs)

        cls.__init__ = init  # type: ignore[misc]


class PositionalOnly(BehaviorModifier):
    """Enforces that the parameters supplied to a dataclass are indicated via position."""

    def __init__(self) -> None:
        """Initializes the current instance."""
        pass

    def modify(
        self,
        cls: DataclassType,
        fields: _types.MappingProxyType[str, Field],
        declared_fields: _types.MappingProxyType[str, Field],
    ) -> None:
        """
        Modifies the initializer of the indicated class to allow only positional arguments.

        :param cls: The dataclass to modify.
        :param fields: All fields of the dataclass.
        :param declared_fields:
            The fields of the dataclass that were declared on the type itself rather than being inherited.
        """
        inner_init = cls.__init__  # type: ignore[misc]

        def init(obj: _typing.Any, /, *args: _typing.Any) -> None:
            inner_init(obj, *args)

        cls.__init__ = init  # type: ignore[misc]


class ObjectHandler:
    """Handles the initialization and set-attribute behavior of a dataclass-like object."""

    def contextualize(self, cls: type, modifiers: tuple[BehaviorModifier, ...]) -> ObjectHandler:
        """
        Returns an object handler to be used together with the indicated type. By default, this returns the current
        instance.

        :param cls: The type to be turned into a dataclass.
        :param modifiers: The modifiers the dataclass has been initialized with.
        :return: The object handler to be used together with the indicated type.
        """
        return self

    def init_instance(
        self,
        cls: DataclassType,
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
        fields = cls.__dataclassbase_fields__

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
        self._initialize_fields(cls, obj, assignments)

    def _initialize_fields(self, cls: DataclassType, obj: _typing.Any, assignments: dict[str, _typing.Any]) -> None:
        """
        Initializes the supplied instance with the indicated field values.

        :param cls: The dataclass type.
        :param obj: The object on which to perform the assignment. This is an instance of the indicated dataclass type.
        :param assignments: The assignments.
        """
        for k, v in assignments.items():
            setattr(obj, k, v)

    def init_instance_post(
        self,
        cls: DataclassType,
        obj: _typing.Any,
        args: tuple[_typing.Any, ...],
        kwargs: dict[str, _typing.Any],
    ) -> None:
        """
        Called during initialization after invoking the user `__init__`-code.

        :param cls: The class of the object to initialize.
        :param obj: The object to initialize.
        :param args: The positional arguments.
        :param kwargs: The keyword arguments.
        """
        # mark dataclass as initialized, but only if it is an actual instance of cls. This may change the behavior of
        # the dataclass

        # invoke postinit, if available
        postinit = getattr(obj, '__postinit__', None)
        if postinit is not None and callable(postinit):
            postinit()

    def init_instance_subtype_pre(
        self,
        cls: DataclassType,
        obj: _typing.Any,
        args: tuple[_typing.Any, ...],
        kwargs: dict[str, _typing.Any],
    ) -> None:
        """
        Called during initialization in a subtype before the user `__init__` gets invoked.

        :param cls: The class of the object to initialize.
        :param obj: The object to initialize.
        :param args: The positional arguments.
        :param kwargs: The keyword arguments.
        """
        pass

    def init_instance_subtype_post(
        self,
        cls: DataclassType,
        obj: _typing.Any,
        args: tuple[_typing.Any, ...],
        kwargs: dict[str, _typing.Any],
    ) -> None:
        """
        Called during initialization in a subtype after the user `__init__` gets invoked.

        :param cls: The class of the object to initialize.
        :param obj: The object to initialize.
        :param args: The positional arguments.
        :param kwargs: The keyword arguments.
        """
        pass

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
        if field is not None and obj.__dataclassbase_initialized__:
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


def dataclass_leaf_types(cls: type) -> tuple[type, ...]:
    """
    Determines the dataclass types of a class that are the nearest from the type itself in its inheritance graph. If
    the class itself is a dataclass, only the class itself is returned. Otherwise, the MRO of the class gets filtered
    for its most direct dataclass type descendants.

    :param cls: The class for which to obtain the dataclasses.
    :return: The tuple of dataclasses obtained for the type. Empty if the supplied class is not a dataclass and does not
        define a dataclass in any base type.
    """
    direct = _typing.cast(tuple[type, ...] | None, cls.__dict__.get('__dataclassbase_types__'))

    if direct is not None:
        return direct
    else:
        s: set[type] = set()
        lst: list[type] = []

        for base in cls.__mro__[1:]:
            if base.__dict__ is None or base in s:
                continue

            dataclass_types = _typing.cast(tuple[type, ...] | None, base.__dict__.get('__dataclassbase_types__'))

            if dataclass_types is None:
                continue

            s.update(base.__mro__)
            lst.append(base)

        return tuple(lst)


def make_dataclass(
    cls: type,
    field_provider: _E[FieldProvider | FieldFactory] = ...,
    object_handler: _E[ObjectHandler] = ...,
    modifiers: tuple[BehaviorModifier | ConstructorlessFactory[BehaviorModifier], ...] = (),
) -> None:
    """
    Makes the indicated class dataclass-like. The class must not be a dataclass, yet.

    :param cls: The class to make a dataclass.
    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    :param modifiers: Additional modifiers changing the behavior of the dataclass.
    """

    # validate

    if '__dataclassbase_fields__' in cls.__dict__:
        raise TypeError('The indicated type already is a dataclass.')

    if issubclass(cls, BehaviorModifier):
        raise RuntimeError('Behavior modifiers cannot be turned into dataclasses.')

    # normalize and prepare parameters

    if field_provider is ...:
        field_provider = BasicFieldProvider()
    elif not isinstance(field_provider, FieldProvider):
        # create the field provider from a `FieldFactory` object
        field_provider = BasicFieldProvider(field_provider)

    if object_handler is ...:
        object_handler = ObjectHandler()

    initialized_modifiers = tuple(
        modifier if isinstance(modifier, BehaviorModifier) else modifier() for modifier in modifiers
    )

    field_provider = field_provider.contextualize(cls, initialized_modifiers)
    object_handler = object_handler.contextualize(cls, initialized_modifiers)

    # retrieve base class and current class fields and merge them

    fields = field_provider.gather_fields(cls)
    merged_fields = fields.all()

    has_default = False

    for field in merged_fields.values():
        if field.has_default:
            has_default = True
        elif has_default:
            raise RuntimeError('Fields with default value must not be followed by fields without a default value.')

    declared_fields = _types.MappingProxyType(fields.declared_fields)
    field_map = _types.MappingProxyType(merged_fields)

    # check that all base classes allow the requested overrides

    for base in cls.__bases__:
        # check with all bases (that are not metaclasses) that our overrides are valid
        if isinstance(base, DataclassMetaBase):
            field_provider.check_overrides(base.__dataclassbase_fields__, field_map)

    # modify `cls` to become a dataclass

    cls.__dataclassbase_fields__ = field_map  # type: ignore[attr-defined]
    cls.__dataclassbase_types__ = (cls,)  # type: ignore[attr-defined]

    # determine the new `__init__` procedure. The old one gets called, too, if there is one (different from the one of
    # `object`)
    user_init = getattr(cls, '__init__', None)

    if user_init is object.__init__ or not callable(user_init):
        user_init = None

    def init(self: _typing.Any, *args: _typing.Any, **kwargs: _typing.Any) -> None:
        # we treat the root dataclass (the one on top of the inheritance tree) differently from the other ones
        is_root_dataclass = cls in dataclass_leaf_types(type(self))

        if is_root_dataclass:
            self.__dataclassbase_initialized__ = False

            # noinspection PyTypeChecker
            object_handler.init_instance(cls, self, args, kwargs)  # type: ignore[arg-type]

            if user_init is not None:
                user_init(self, *args, **kwargs)

            object_handler.init_instance_post(_typing.cast(DataclassType, cls), self, args, kwargs)

            self.__dataclassbase_initialized__ = True
        else:
            object_handler.init_instance_subtype_pre(_typing.cast(DataclassType, cls), self, args, kwargs)

            if user_init is not None:
                user_init(self, *args, **kwargs)

            object_handler.init_instance_subtype_post(_typing.cast(DataclassType, cls), self, args, kwargs)

    cls.__init__ = init  # type: ignore[method-assign]

    if object_handler.override_set_attribute:
        inner_set_attribute = getattr(cls, '__setattr__', None)

        def setattrib(self: _typing.Any, key: str, value: _typing.Any) -> None:
            field = field_map.get(key)
            object_handler.handle_set_attribute(self, field, key, value, inner_set_attribute)

        cls.__setattr__ = setattrib  # type: ignore[method-assign]

    if object_handler.override_delete_attribute:
        inner_del_attribute = getattr(cls, '__delattr__', None)

        def delattrib(self: _typing.Any, item: str) -> None:
            field = field_map.get(item)
            object_handler.handle_delete_attribute(self, field, item, inner_del_attribute)

        cls.__delattr__ = delattrib  # type: ignore[method-assign]

    cls.__dataclassbase_modifiers__ = initialized_modifiers  # type: ignore[attr-defined]

    dc = _typing.cast(DataclassType, _typing.cast(object, cls))

    for modifier in initialized_modifiers:
        modifier.modify(dc, field_map, declared_fields)


@_typing.dataclass_transform()
@_typing.overload
def dataclass[TCls: type](
    *modifiers: BehaviorModifier | ConstructorlessFactory[BehaviorModifier],
    field_provider: _E[FieldProvider | FieldFactory] = ...,
    object_handler: _E[ObjectHandler] = ...,
) -> _typing.Callable[[TCls], TCls]:
    """
    Returns a function that that makes the classes supplied to it dataclass-like. The classes must not be dataclasses,
    yet.

    Intended to be used as a decorator.

    :param modifiers: Additional modifiers changing the behavior of the dataclass.
    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    """
    ...


@_typing.dataclass_transform()
@_typing.overload
def dataclass[TCls: type](
    cls: TCls,
    /,
    *modifiers: BehaviorModifier | ConstructorlessFactory[BehaviorModifier],
    field_provider: _E[FieldProvider | FieldFactory] = ...,
    object_handler: _E[ObjectHandler] = ...,
) -> TCls:
    """
    Makes the indicated class dataclass-like. The class must not be a dataclass, yet.

    Intended to be used as a decorator.

    :param cls: The class to turn into a dataclass.
    :param modifiers: Additional modifiers changing the behavior of the dataclass.
    :param field_provider: A field provider used to initialize the fields of the dataclass. Depending on the type of
        field provider, fields may expose different types of behavior during initialization and attribute assignment.
    :param object_handler: Implements the initialization and attribute assignment of instances of the dataclass.
    :return: The class supplied in `cls` now turned into a dataclass.
    """
    ...


@_typing.dataclass_transform()
def dataclass(
    *modifiers: type | BehaviorModifier | ConstructorlessFactory[BehaviorModifier],
    field_provider: _E[FieldProvider | FieldFactory] = ...,
    object_handler: _E[ObjectHandler] = ...,
) -> _typing.Any:
    if len(modifiers) > 0 and isinstance(modifiers[0], type) and not issubclass(modifiers[0], BehaviorModifier):
        cls = _typing.cast(type, modifiers[0])
        modifiers = _typing.cast(tuple[BehaviorModifier | ConstructorlessFactory[BehaviorModifier], ...], modifiers[1:])
        make_dataclass(cls, field_provider, object_handler, modifiers)
        return cls

    def handle[T: type](cls: T) -> T:
        make_dataclass(
            cls,
            field_provider,
            object_handler,
            _typing.cast(tuple[BehaviorModifier | ConstructorlessFactory[BehaviorModifier], ...], modifiers),
        )

        return cls

    return handle


class DataclassMetaBase(type):
    """
    A base class for metaclasses inducing dataclass-like behavior. The :py:func:`make_dataclass` gets invoked on
    subclasses.

    Note that this class is not intended to be used directly as a metaclass. The :py:func:`typing.dataclass_transform`
    method is not applied to the current type since it requires specific field specifiers. In derived classes, however,
    the field specifiers may not be limited to the :class:`Field`-class. Therefore, you should define a metaclass that
    is derived from the :class:`DataclassMetaBase` class if you want to define a class with custom field specifiers and
    add a :py:func:`typing.dataclass_transform`-decoration to them. Use the :py:func:`_field_provider` to control the
    conversion of the field specifies into fields.

    Note that this class is not intended to be used directly as a metaclass of a dataclass. The
    :py:func:`typing.dataclass_transform` method does not get applied to the current type since it would constrain the
    parameters of :py:func:`typing.dataclass_transform` to a specific choice. Use a derived class and apply
    `:py:func:`typing.dataclass_transform` to it or use the default implementation :py:class:`DataclassMeta`.
    """

    __dataclassbase_fields__: _types.MappingProxyType[str, Field]
    __dataclassbase_initialized__: bool
    __dataclassbase_modifiers__: tuple[BehaviorModifier, ...]
    __dataclassbase_types__: tuple[DataclassType, ...]

    def __new__(mcs, name: str, bases: tuple[type, ...], dct: dict[str, _typing.Any]) -> type:
        cls = type.__new__(mcs, name, bases, dct)

        make_dataclass(cls, mcs._field_provider(), mcs._object_handler(), mcs._modifiers())

        return cls

    @classmethod
    def _field_provider(cls) -> FieldProvider:
        """
        The field provider to use to control the creation and override behavior of fields.

        :return: The field provider.
        """
        return BasicFieldProvider()

    @classmethod
    def _object_handler(cls) -> ObjectHandler:
        """
        The object handler to use to control the object initialization and set-attribute behavior.

        :return: The object handler.
        """
        return ObjectHandler()

    @classmethod
    def _modifiers(cls) -> tuple[BehaviorModifier | ConstructorlessFactory[BehaviorModifier], ...]:
        return ()


@_typing.dataclass_transform(field_specifiers=(Field, FieldInitializer))
class DataclassMeta(DataclassMetaBase):
    """
    Provides a basic :class:`Field`-based metaclass. When used as a metaclass, the class and any subclass inherit a
    dataclass-like behavior. See :class:`DataclassMetaBase` and :py:func:`make_dataclass` for further information.
    """

    pass


class DataclassBase:
    """
    A base class for classes inducing dataclass-like behavior. The :py:func:`make_dataclass` gets invoked during the
    initialization of the subclasses.

    Note that this class is not intended to be used directly as a base class of a dataclass. The
    :py:func:`typing.dataclass_transform` method does not get applied to the current type since it would constrain the
    parameters of :py:func:`typing.dataclass_transform` to a specific choice. Use a derived class and apply
    `:py:func:`typing.dataclass_transform` to it or use the default implementation :py:class:`Dataclass`.
    """

    __dataclassbase_fields__: _types.MappingProxyType[str, Field]
    __dataclassbase_initialized__: bool
    __dataclassbase_modifiers__: tuple[BehaviorModifier, ...]
    __dataclassbase_types__: tuple[DataclassType, ...]

    def __init_subclass__(cls) -> None:
        make_dataclass(cls, cls._field_provider(), cls._object_handler(), cls._modifiers())

    @classmethod
    def _field_provider(cls) -> FieldProvider:
        """
        The field provider to use to control the creation and override behavior of fields.

        :return: The field provider.
        """
        return BasicFieldProvider()

    @classmethod
    def _object_handler(cls) -> ObjectHandler:
        """
        The object handler to use to control the object initialization and set-attribute behavior.

        :return: The object handler.
        """
        return ObjectHandler()

    @classmethod
    def _modifiers(cls) -> tuple[BehaviorModifier | ConstructorlessFactory[BehaviorModifier], ...]:
        return ()


@_typing.dataclass_transform(field_specifiers=(Field, FieldInitializer))
class Dataclass(DataclassBase):
    """
    Provides a basic :class:`Field`-based metaclass. When used as a metaclass, the class and any subclass inherit a
    dataclass-like behavior. See :class:`DataclassMetaBase` and :py:func:`make_dataclass` for further information.
    """

    pass


@_typing.runtime_checkable
class DataclassbaseInstance(_typing.Protocol):
    """
    A protocol that describes the instances of the dataclass-like classes created by this module via
    :py:func:`make_dataclass`, etc.
    """

    __dataclassbase_initialized__: bool
    """Determines the dataclass instance has been initialized."""

    __dataclassbase_fields__: _typing.ClassVar[_util.MappingProto[str, Field]]
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


def as_dict(
    obj: DataclassbaseInstance,
    child_dataclass_to_dict: _E[_typing.Callable[[DataclassbaseInstance], _typing.Any]] | None = ...,
    fields_only: bool = True,
) -> dict[str, _typing.Any]:
    """
    Builds a dictionary from the fields of the indicated dataclass instance.

    :param obj: The dataclass instance to build the dictionary from.
    :param child_dataclass_to_dict: A function to call for child dataclasses.
    :param fields_only: If `True`, only fields of the dataclass are added to the dictionary. Otherwise, all attributes
        get processed.
    :return: The dictionary of fields or attributes.
    """
    if child_dataclass_to_dict is ...:

        def child_dataclass_to_dict(obj: DataclassbaseInstance) -> _typing.Any:
            return as_dict(obj, child_dataclass_to_dict=child_dataclass_to_dict, fields_only=fields_only)

    dct = {k: getattr(obj, k) for k in type(obj).__dataclassbase_fields__} if fields_only else obj.__dict__.copy()

    if child_dataclass_to_dict is not None:
        for k, v in dct.items():
            if isinstance(v, DataclassbaseInstance):
                dct[k] = child_dataclass_to_dict(v)

    return dct


def _default_format_dict(obj: DataclassbaseInstance, dct: dict[str, _typing.Any]) -> str:
    """
    Formats the indicated dictionary: We assume that the dataclass supports getting initialized with the parameters
    indicated in the supplied dictionary. We display the parameters as keyword-only arguments.

    :param obj: The type of the object the dictionary corresponds to.
    :param dct: The dictionary.
    :return: The string representation.
    """
    parts = [type(obj).__name__, '(']

    for i, (k, v) in enumerate(dct.items()):
        if i > 0:
            parts.append(', ')

        parts.append(k)
        parts.append('=')
        parts.append(repr(v))

    parts.append(')')

    return ''.join(parts)


def _default_dict_to_repr(obj: DataclassbaseInstance, dct: dict[str, _typing.Any]) -> str:
    """
    The default implementation for returning the representation (:py:func:`repr`) of the object with the attributes or
    fields supplied as a dict.

    :param obj: The object to represent.
    :param dct: The dictionary of fields or attributes.
    :return: The default representation of the object.
    """
    return _default_format_dict(obj, dct)


def _default_dict_to_str(obj: DataclassbaseInstance, dct: dict[str, _typing.Any]) -> str:
    """
    The default implementation for returning the string representation (:py:func:`str`) of the object with the
    attributes or fields supplied as a dict.

    :param obj: The object to turn into a string.
    :param dct: The dictionary of fields or attributes.
    :return: The default str-representation of the object.
    """
    return _default_format_dict(obj, dct)


class Representable(BehaviorModifier):
    """
    Used to add functionality for string representation (:py:func:`str`) and object representation (:py:func:`repr`)
    to the dataclass.
    """

    def __init__(
        self,
        obj_as_dict: _E[_typing.Callable[[DataclassbaseInstance], _typing.Any]] = ...,
        dict_to_str: _E[_typing.Callable[[DataclassbaseInstance, dict[str, _typing.Any]], str]] | None = ...,
        dict_to_repr: _E[_typing.Callable[[DataclassbaseInstance, dict[str, _typing.Any]], str]] | None = ...,
    ) -> None:
        """
        Initializes the current instance.

        :param obj_as_dict: Invoked to turn a dataclass into a dictionary representation.
        :param dict_to_str: Used to format a dataclass dictionary as a string (Used for :py:func:`str`). If `None`, the
            :py:func:`__str__` method of the dataclass does not get overridden. Note that Python falls back to
            :py:func:`__repr__` if :py:func:`__repr__` is not overridden.
        :param dict_to_repr: Used to format a dataclass dictionary as a representation (Used for :py:func:`repr`). If
            `None`, the :py:func:`__repr__` method does not get overridden.
        """
        if obj_as_dict is ...:
            obj_as_dict = as_dict

        if dict_to_repr is ...:
            dict_to_repr = _default_dict_to_repr

        if dict_to_str is ...:
            dict_to_str = _default_dict_to_str

        self._obj_as_dict = obj_as_dict
        self._dict_to_str = dict_to_str
        self._dict_to_repr = dict_to_repr

    def modify(
        self,
        cls: DataclassType,
        fields: _types.MappingProxyType[str, Field],
        declared_fields: _types.MappingProxyType[str, Field],
    ) -> None:
        """
        Overrides :py:func:`__str__` and/or :py:func:`__repr__` according to the behavior defined during initialization.

        :param cls: The class to modify.
        :param fields: All fields of the dataclass.
        :param declared_fields:
            The fields of the dataclass that were declared on the type itself rather than being inherited.
        """
        dict_to_repr = self._dict_to_repr
        dict_to_str = self._dict_to_str

        if dict_to_repr is not None:

            def repr_impl(obj: _typing.Any, /) -> str:
                return dict_to_repr(obj, self._obj_as_dict(obj))

            cls.__repr__ = repr_impl  # type: ignore[assignment, method-assign]

        if dict_to_str is not None:

            def str_impl(obj: _typing.Any, /) -> str:
                return dict_to_str(obj, self._obj_as_dict(obj))

            cls.__str__ = str_impl  # type: ignore[assignment, method-assign]
