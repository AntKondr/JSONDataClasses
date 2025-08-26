from types import GenericAlias, UnionType


class DecodeError(Exception):
    pass


class JSONFieldTypeError(DecodeError):
    def __init__(
        self,
        dataClass: type,
        fieldName: str,
        dataClassFieldType: type | GenericAlias | UnionType,
        jsonFieldType: type
    ) -> None:
        self.dataClass: type = dataClass
        self.fieldName: str = fieldName
        self.dataClassFieldType: type | GenericAlias | UnionType = dataClassFieldType
        self.jsonFieldType: type = jsonFieldType

    def __str__(self) -> str:
        return f"json field type error: does not match to dataclass:\ndataclass: {self.dataClass}; field: {self.fieldName}; expected: {self.dataClassFieldType}; recieved: {self.jsonFieldType}"

    def __repr__(self) -> str:
        return self.__str__()
