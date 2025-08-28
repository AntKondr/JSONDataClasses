from typing import Any, Final, get_type_hints, get_origin, get_args
from types import GenericAlias, UnionType, NoneType, EllipsisType
from enum import Enum, EnumType
from .utils import isJSONPrimitiveType, isSequenceType


class MJSONCodable(type):
    __MAIN_CLASS_NAME: Final[str] = "JSONCodable"
    __mainClassNotCreated: bool = True

    def __new__(cls, name: str, baseClasses: tuple[type, ...], attrs: dict[str, Any], /) -> "MJSONCodable":
        annotations: dict[str, type] = attrs["__annotations__"]
        annotations.pop("__slots__", None)
        annotations.pop("_defaults", None)
        annotations.pop("_strict", None)
        if name == cls.__MAIN_CLASS_NAME:
            if cls.__mainClassNotCreated:
                cls.__mainClassNotCreated = False
                return super().__new__(cls, name, baseClasses, attrs)
            else:
                raise Exception(f"{cls.__MAIN_CLASS_NAME} primary class has been already created! Secondary not allowed!")

        defaults: dict[str, Any] = {}
        for field in annotations:
            if (value := attrs.pop(field, ...)) is not ...:
                defaults[field] = value

        attrs["__slots__"] = tuple((field for field in annotations if not field.startswith("_")))
        attrs["_defaults"] = defaults
        cls.__setInit(attrs, annotations, defaults)
        NewClass: type = super().__new__(cls, name, baseClasses, attrs)
        annotations = get_type_hints(NewClass, include_extras=True)
        # check the correctness JSON fields types
        for fieldName, fieldType in annotations.items():
            if type(fieldType) in BOUND_TYPES:
                cls.__checkType(fieldType)

            elif type(fieldType) is UnionType:
                cls.__checkUnion(fieldType)

            elif type(fieldType) is GenericAlias:
                cls.__checkGeneric(fieldType)

            else:
                raise Exception(f"unhandled type of field: {fieldName}: {fieldType}")
        return NewClass

    @classmethod
    def __setInit(cls, classAttrs: dict[str, Any], annotations: dict[str, type], defaults: dict[str, Any]) -> None:
        n: str = "\n"
        paramsSB: list[str] = []
        bodySB: list[str] = []
        for f in annotations:
            if f in defaults:
                paramsSB.append(f"{f} = None")
                bodySB.append(f"""\tself.{f} = self._defaults["{f}"] if {f} is None else {f}""")
            else:
                paramsSB.append(f"{f}")
                bodySB.append(f"\tself.{f} = {f}")

        initStr: str = f"""def __init__(self, {", ".join(paramsSB)}):\n{n.join(bodySB)}"""
        exec(initStr, globals(), local := {})
        classAttrs["__init__"] = local["__init__"]

    @classmethod
    def __checkType(cls, _cls: type) -> None:
        if isJSONPrimitiveType(_cls) or issubclass(_cls, Enum) or type(_cls) is cls:
            return None
        elif isSequenceType(_cls):
            raise Exception(f"checkType: need to specify generic type for sequence {_cls}")
        else:
            raise Exception(f"checkType: unhandled simple type {_cls}")

    @classmethod
    def __checkUnion(cls, _cls: UnionType) -> None:
        # UnionType must be like    anytype | None  (aka nullable)
        # note: in union `anytype | None` in args `None` casts in NoneType (by function `get_type_hints`)
        unionArgs: tuple[type, ...] = get_args(_cls)
        if len(unionArgs) > 2:
            raise Exception(f"checkUnion: union must have 2 types, but got: {_cls}")
        try:
            noneIndex: int = unionArgs.index(NoneType)                  # raises ValueError if NoneType not in union args
        except ValueError:
            raise Exception(f"checkUnion: union must contain None or NoneType, but got: {_cls}")
        typeInUnion: type = unionArgs[0 if noneIndex == 1 else 1]       # can be type (primitive or user def class) or generic
        typeOfTypeInUnion: type = type(typeInUnion)
        if typeOfTypeInUnion in BOUND_TYPES:
            return cls.__checkType(typeInUnion)
        elif typeOfTypeInUnion is GenericAlias:
            return cls.__checkGeneric(typeInUnion)
        else:
            raise Exception(f"checkUnion: unhandled type inside union: {typeInUnion}\tUnionType -> {_cls}")

    @classmethod
    def __checkGeneric(cls, _cls: GenericAlias) -> None:
        # GenericAlias can use only for sequence
        # for example: list[int]   or   list[Person]   or   tuple[int, int, float, Person]
        origin: type = get_origin(_cls)                          # must be tuple or list
        genericArgs: tuple[type, ...] = get_args(_cls)           # must be tuple or list of simple type generic type

        if ... in genericArgs or EllipsisType in genericArgs or None in genericArgs or NoneType in genericArgs or UnionType in (type(arg) for arg in genericArgs):     # generic args only generic or type allowed
            raise Exception(f"checkGeneric: invalid generic {_cls}")

        if origin is tuple:
            return cls.__checkTupleGeneric(genericArgs)
        elif origin is list:
            return cls.__checkListGeneric(genericArgs)
        else:
            raise Exception(f"checkGeneric: only sequences generics are allowed, but got {_cls}")

    @classmethod
    def __checkTupleGeneric(cls, tupleGenericArgs: tuple[type, ...]) -> None:
        for genTyp in tupleGenericArgs:
            if type(genTyp) in BOUND_TYPES:
                return cls.__checkType(genTyp)
            elif type(genTyp) is GenericAlias:
                return cls.__checkGeneric(genTyp)
            else:
                raise Exception(f"checkTupleGeneric: not allowed arg {genTyp} in tuple generic")

    @classmethod
    def __checkListGeneric(cls, listGenericArgs: tuple[type, ...]) -> None:
        if len(listGenericArgs) > 1:
            raise Exception(f"checkListGeneric: list generic are allowed only one type in args, got: {listGenericArgs}")
        genTyp: type | GenericAlias = listGenericArgs[0]
        if type(genTyp) in BOUND_TYPES:
            return cls.__checkType(genTyp)
        elif type(genTyp) is GenericAlias:
            return cls.__checkGeneric(genTyp)
        else:
            raise Exception(f"checkListGeneric: not allowed arg {genTyp} in list generic")


BOUND_TYPES: tuple[type, ...] = (type, MJSONCodable, EnumType)
