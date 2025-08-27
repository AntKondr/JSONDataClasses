from typing import Any, Self, dataclass_transform, get_type_hints, get_origin, get_args
from types import GenericAlias, UnionType, NoneType, EllipsisType
from json import loads, dumps
from .utils import isJSONPrimitiveType
from .Meta import MJSONCodable, BOUND_TYPES
from .exceptions import DecodeError, JSONFieldTypeError


@dataclass_transform()
class JSONCodable(metaclass=MJSONCodable):
    __slots__ = ()
    __defaults__ = {}

    @classmethod
    def __getDefault(cls, field: str) -> Any | EllipsisType:
        return cls.__defaults__.get(field, ...)

    @classmethod
    def __handleType(cls, fieldName: str, fieldType: type, jsonValue: Any) -> Any:      # simple type (when type(fieldType) is type)
        typeOfJSONValue: type = type(jsonValue)
        if jsonValue is None:
            if (dv := cls.__getDefault(fieldName)) is not ...:
                return dv
            raise DecodeError(f"""Default value for field {fieldName} not defined""")
        if isJSONPrimitiveType(fieldType):
            return fieldType(jsonValue)
        elif issubclass(fieldType, JSONCodable):
            if typeOfJSONValue is dict:
                return fieldType.fromDict(jsonValue)
            raise JSONFieldTypeError(cls, fieldName, fieldType, typeOfJSONValue)
        else:
            raise Exception(f"handleType: unhandled type {fieldType} of field {fieldName} into dataclass {cls}")

    @classmethod
    def __handleUnion(cls, fieldName: str, fieldType: UnionType, jsonValue: Any) -> Any:         # union type (when type(fieldType) is UnionType)
        # UnionType must be like:   anytype | None
        if jsonValue is None:
            return None
        unionArgs: tuple[type, ...] = get_args(fieldType)
        noneIndex: int = unionArgs.index(NoneType)                  # raises ValueError if NoneType not in args (checked in `checkUnion`)
        typeInUnion: type = unionArgs[0 if noneIndex == 1 else 1]   # can be primitive   or   dataclass   or   generic   or   seq
        typeOfTypeInUnion: type = type(typeInUnion)
        if typeOfTypeInUnion in BOUND_TYPES:
            return cls.__handleType(fieldName, typeInUnion, jsonValue)
        elif typeOfTypeInUnion is GenericAlias:
            return cls.__handleGeneric(fieldName, typeInUnion, jsonValue)
        else:
            raise Exception(f"handleUnion: unhandled type inside UnionType: {typeInUnion} of field {fieldName} into dataclass {cls}")

    @classmethod
    def __handleGeneric(cls, fieldName: str, fieldType: GenericAlias, jsonValue: Any) -> Any:    # generic type (when type(fieldType) is GenericAlias)
        # договоримся, что GenericAlias может использоваться только для последовательности,
        # например list[int]   or   list[Person]   or   tuple[int, int, float]
        typeOfJSONValue: type = type(jsonValue)                 # dict   or   list   or   primitive
        if typeOfJSONValue is not list:                         # here we know that data is list
            raise JSONFieldTypeError(cls, fieldName, fieldType, typeOfJSONValue)

        origin: type = get_origin(fieldType)                          # must be tuple or list
        genericArgs: tuple[type, ...] = get_args(fieldType)           # tuple of simple type or generic type or union

        if origin is tuple:
            return cls.__handleTupleGeneric(fieldName, genericArgs, jsonValue)
        elif origin is list:
            return cls.__handleListGeneric(fieldName, genericArgs, jsonValue)
        else:
            raise Exception(f"handleGeneric: only tuple or list generics are allowed, but got {fieldType} type of field {fieldName} into dataclass {cls}")

    @classmethod
    def __handleTupleGeneric(cls, fieldName: str, tupleGenericArgs: tuple[type, ...], seq: list) -> tuple:
        if len(tupleGenericArgs) != len(seq):
            raise Exception(f"handleTupleGeneric: class {cls}; field: {fieldName}\namount of tuple generic args != length of data\nexpected: {tupleGenericArgs}; recieved items amt: {len(seq)}")
        for i, (genTyp, seqItem) in enumerate(zip(tupleGenericArgs, seq)):
            if type(genTyp) in BOUND_TYPES:
                seq[i] = cls.__handleType(fieldName, genTyp, seqItem)
            elif type(genTyp) is GenericAlias:
                seq[i] = cls.__handleGeneric(fieldName, genTyp, seqItem)
            else:
                raise Exception(f"handleTupleGeneric: not allowed arg in generic: {genTyp} type of field {fieldName} into dataclass {cls}")
        return tuple(seq)

    @classmethod
    def __handleListGeneric(cls, fieldName: str, listGenericArgs: tuple[type, ...], seq: list) -> list:
        genTyp: type = listGenericArgs[0]
        for i, seqItem in enumerate(seq):
            if type(genTyp) in BOUND_TYPES:
                seq[i] = cls.__handleType(fieldName, genTyp, seqItem)
            elif type(genTyp) is GenericAlias:
                seq[i] = cls.__handleGeneric(fieldName, genTyp, seqItem)
            else:
                raise Exception(f"handleListGeneric: not allowed arg in generic: {genTyp} type of field {fieldName} into dataclass {cls}")
        return seq

    # public methods for usage ----------------------------------------------------------------------
    def toJSON(self, indent: int | None = None, itemSep: str = ",", keySep: str = ":") -> str:
        return dumps(self, indent=indent, separators=(itemSep, keySep), ensure_ascii=False, default=slots)

    @classmethod
    def fromJSON(cls, json: str | bytes | bytearray) -> Self:
        d: dict[str, Any] = loads(json)
        return cls.fromDict(d)

    @classmethod
    def fromDict(cls, d: dict[str, Any]) -> Self:
        p: dict[str, Any] = {}
        typeHints: dict[str, Any] = get_type_hints(cls, include_extras=True)
        for fieldName, fieldType in typeHints.items():
            jsonValue: Any | None = d.get(fieldName)
            if type(fieldType) in BOUND_TYPES:                          # simple concrete type (not union or generic), like int, str (primitives), list (seqs) and user def classes
                p[fieldName] = cls.__handleType(fieldName, fieldType, jsonValue)

            elif type(fieldType) is UnionType:                          # list[Foo] | Foo | None    __args__ - tuple of types included into union
                p[fieldName] = cls.__handleUnion(fieldName, fieldType, jsonValue)

            elif type(fieldType) is GenericAlias:                       # list[Foo]     or      tuple[int, float, float]    __origin__ - main type, __args__ - tuple of types into generic
                p[fieldName] = cls.__handleGeneric(fieldName, fieldType, jsonValue)
        return cls(**p)


def slots(o: JSONCodable) -> dict[str, Any]:
    d = {}
    for f in o.__slots__:
        v = getattr(o, f, None)
        if v is not None:
            d[f] = v
    return d
