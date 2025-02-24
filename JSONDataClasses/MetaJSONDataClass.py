from typing import Any, get_type_hints, get_origin, get_args
from types import GenericAlias, UnionType, NoneType, EllipsisType
from dataclasses import dataclass, is_dataclass
from .utils import isJSONPrimitiveType, isSequenceType


class MJSONDataClass(type):
    def __new__(
        cls,
        name: str,
        baseClasses: tuple[type, ...],
        nameSpace: dict[str, Any],
        *,
        init: bool = True,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        match_args: bool = True,
        kw_only: bool = False,
        slots: bool = False,
        weakref_slot: bool = False
    ) -> type:

        NewClass: type = type.__new__(cls, name, baseClasses, nameSpace)
        try:
            typeHints: dict[str, Any] = get_type_hints(NewClass, include_extras=True)
        except NameError as e:
            raise NameError(f"Type hint error in class {NewClass}: {e}. Did you forget to import a type?") from e
        except Exception as e:
            raise RuntimeError(f"Error getting type hints for class {NewClass}: {e}") from e

        # check the correctness JSON fields types
        for fieldName, fieldType in typeHints.items():
            if type(fieldType) in BOUND_TYPES:
                # simple type, like: int, str, bool (primitives); list, tuple (seqs); and user defined classes (metaclass type)
                MJSONDataClass.__checkType(fieldType)

            elif type(fieldType) is UnionType:
                # list[Foo] | Foo | None | Person
                MJSONDataClass.__checkUnion(fieldType)

            elif type(fieldType) is GenericAlias:
                # list[Foo]     or      tuple[int, float, float]
                MJSONDataClass.__checkGeneric(fieldType)

            else:
                print("else:", fieldName, fieldType, type(fieldType))
                raise Exception(f"unhandled type of field: {fieldName}: {fieldType}")
        return dataclass(NewClass, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen, match_args=match_args, kw_only=kw_only, slots=slots, weakref_slot=weakref_slot)

    @staticmethod
    def __checkType(_cls: type) -> None:           # type(_cls) is type     (str, int, ... and user defined class)
        if isJSONPrimitiveType(_cls) or is_dataclass(_cls):
            return None
        elif isSequenceType(_cls):
            raise Exception(f"checkType: need to specify generic type in sequence {_cls}")
        else:
            raise Exception(f"checkType: unhandled simple type {_cls}")

    @staticmethod
    def __checkUnion(_cls: UnionType) -> None:     # type(_cls) is UnionType
        # UnionType must be like    anytype | None  (aka nullable)
        # note: in union `anytype | None` in args `None` casts in NoneType (by function `get_type_hints`)
        unionArgs: tuple[type, ...] = get_args(_cls)
        if len(unionArgs) > 2:
            raise Exception(f"checkUnion: union must have 2 types, but got: {_cls}")
        try:
            noneIndex: int = unionArgs.index(NoneType)                  # raises ValueError if NoneType not in union args
        except ValueError as e:
            raise Exception(f"checkUnion: union must contain None or NoneType, but got: {_cls}") from e
        typeInUnion: type = unionArgs[0 if noneIndex == 1 else 1]       # can be primitive   or   dataclass   or   generic   or   seq
        typeOfTypeInUnion: type = type(typeInUnion)
        if typeOfTypeInUnion in BOUND_TYPES:
            return MJSONDataClass.__checkType(typeInUnion)
        elif typeOfTypeInUnion is GenericAlias:
            return MJSONDataClass.__checkGeneric(typeInUnion)
        else:
            raise Exception(f"checkUnion: unhandled type inside union: {typeInUnion}\tUnionType -> {_cls}")

    @staticmethod
    def __checkGeneric(_cls: GenericAlias) -> None:
        # договоримся, что GenericAlias может использоваться только для последовательности
        # например list[int]   or   list[Person]   or   tuple[int, int, float, Person]
        origin: type = get_origin(_cls)                          # must be tuple or list
        genericArgs: tuple[type, ...] = get_args(_cls)           # tuple of simple type or generic type or union

        if ... in genericArgs or EllipsisType in genericArgs or None in genericArgs or NoneType in genericArgs or UnionType in (type(arg) for arg in genericArgs):     # generic args only generic or type allowed
            raise Exception(f"checkGeneric: invalid generic {_cls}")

        if origin is tuple:
            return MJSONDataClass.__checkTupleGeneric(genericArgs)
        elif origin is list:
            return MJSONDataClass.__checkListGeneric(genericArgs)
        else:
            raise Exception(f"checkGeneric: only sequences generics are allowed, but got {_cls}")

    @staticmethod
    def __checkTupleGeneric(tupleGenericArgs: tuple[type, ...]) -> None:
        for genTyp in tupleGenericArgs:
            if type(genTyp) in BOUND_TYPES:
                return MJSONDataClass.__checkType(genTyp)
            elif type(genTyp) is GenericAlias:
                return MJSONDataClass.__checkGeneric(genTyp)
            else:
                raise Exception(f"checkTupleGeneric: not allowed arg {genTyp} in tuple generic")

    @staticmethod
    def __checkListGeneric(listGenericArgs: tuple[type, ...]) -> None:
        if len(listGenericArgs) > 1:
            raise Exception(f"checkListGeneric: list generic are allowed only one type in args, got: {listGenericArgs}")
        genTyp: type | GenericAlias = listGenericArgs[0]
        if type(genTyp) in BOUND_TYPES:
            return MJSONDataClass.__checkType(genTyp)
        elif type(genTyp) is GenericAlias:
            return MJSONDataClass.__checkGeneric(genTyp)
        else:
            raise Exception(f"checkListGeneric: not allowed arg {genTyp} in list generic")


BOUND_TYPES: tuple[type, ...] = (type, MJSONDataClass)
