## Module for describing json compatible data objects using python classes

pip:
<pre><code><span style="color: #e5c07b">JSONDataClasses</span> @ git+ssh://git@gitlab.vekarus.loc/VekaProg/jsondataclasses.git@master
</code></pre>

This is similar to standard dataclasses.

`__slots__` is injected into the classes.

4 methods are also added: `__init__`, `toJSON`, `fromJSON` and `fromDict`.

`fromJSON`, `fromDict` are classmethods.

Optional class parameter `_strict` - defines the strictness of parsing the json document. Defaults to True.

In case when **_strict** is True, the primitive fields of json document will not attempt to cast to a type, described in the class schema, and if type of value does not match to type in schema - an exception will be raised.

For example, the field `id: int` will expect exactly `"id": 1` in the json document.
In the case of `"id": "1"` an exception will be raised.

In case when **_strict** is False, the primitive fields of json document will attempt to casts to a type, described in the class schema.
In the case of `"id": "1"`, string `"1"` will attempt to casts to integer `1`.

Simple enums are also supported.

Self-referencing also supported.

## Usage example
```python
from enum import Enum
from JSONDataClasses import JSONCodable

class TransportProto(Enum):
    UDP = "udp"
    TCP = "tcp"

class HostType(Enum):
    STATION_COMPUTER = 1
    NOTEBOOK = 2
    PHONE = 3
    PRINTER = 4
    ROUTER = 5

class Hosts(JSONCodable):
    _strict: bool = True  # it's default, assigning not required

    class Host(JSONCodable):
        id: int
        name: str | None
        ip: str
        type: HostType
        transportProto: TransportProto = TransportProto.TCP
        description: str | None = None

    class Meta(JSONCodable):
        objsCount: int
        pageNumber: int
        pagesCount: int

    hosts: list[Host]
    meta: Meta | None = None

j: str = """{
    "hosts": [
        {
            "id": 1,
            "name": "localhost",
            "ip": "127.0.0.1",
            "type": 1,
            "transportProto": "udp"
        },
        {
            "id": 2,
            "name": "printer in the hall",
            "ip": "10.50.150.22",
            "type": 4
        },
        {
            "id": 3,
            "ip": "10.50.150.25",
            "type": 3,
            "transportProto": "udp"
        }
    ],
    "meta": {
        "objsCount": 3,
        "pageNumber": 1,
        "pagesCount": 5
    }
}"""
print(Hosts.fromJSON(j).toJSON(indent=4))
```

## Self-referencing example

```python
from JSONDataClasses import JSONCodable

class Node(JSONCodable):
    data: str
    left: "Node | None" = None
    right: "Node | None" = None

tree: Node = Node(
    data="qwe",
    left=Node(
        data="asd",
        left=Node(
            data="zxc"
        ),
        right=Node(
            data="qaz"
        )
    ),
    right=Node(
        data="wsx"
    )
)
print(Node.fromJSON(tree.toJSON()).toJSON(2))
```
