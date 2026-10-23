import types as _types
import typing as _typing

type E[T] = T | _types.EllipsisType


def throws(f: _typing.Callable[[], _typing.Any], *exception_types: type[BaseException]) -> bool:
    """
    Makes the indicated call and returns whether an exception of one of the indicated types occurred. Exceptions of
    other types do not get caught.

    :param f: The function to invoke.
    :param exception_types: The exception types to check for.
    :return: `True` if an exception occurred that satisfied one of the supplied exception types, `False` if no exception
        occurred.
    """
    try:
        f()
    except BaseException as ex:
        if isinstance(ex, exception_types):
            return True

        raise

    return False


@_typing.runtime_checkable
class MappingProto[TKey, TValue](_typing.Protocol):
    def keys(self) -> _typing.AbstractSet[TKey]: ...

    def values(self) -> _typing.Iterable[TValue]: ...

    def items(self) -> _typing.Iterable[tuple[TKey, TValue]]: ...

    def __getitem__(self, item: TKey, /) -> TValue: ...

    def __iter__(self) -> _typing.Iterator[TKey]: ...

    def __contains__(self, item: object, /) -> bool: ...

    def __len__(self) -> int: ...
