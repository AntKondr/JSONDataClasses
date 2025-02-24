from types import NoneType


PRIMITIVES: dict[str, type] = {
    "None": NoneType,
    "NoneType": NoneType,
    "bool": bool,
    "int": int,
    "float": float,
    "str": str
}
SEQUENCES: dict[str, type] = {
    "tuple": tuple,
    "list": list
}


def isJSONPrimitiveType(t: type | str) -> bool:
    if type(t) is str:
        return t in PRIMITIVES
    else:
        return t in PRIMITIVES.values()


def isSequenceType(t: type | str) -> bool:
    if type(t) is str:
        return t in SEQUENCES
    else:
        return t in SEQUENCES.values()
