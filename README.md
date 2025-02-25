## Module for simple data objects (compatible with json) description with python classes
## Usage
```python
from JSONDataClasses import JSONDataClass

class Abzug(JSONDataClass):
    id: int
    invNo: int

class Extruder(JSONDataClass):
    id: int
    invNo: int
    name: str | None

class FactoryLine(JSONDataClass, frozen=True):
    id: int
    number: int
    strandsAmt: int
    abzug: Abzug | None
    extruder: Extruder | None

class Factory(JSONDataClass, slots=True):
    id: int
    name: str
    address: str
    factoryLines: list[FactoryLine]

class GraphPoints(JSONDataClass):
    points: list[tuple[int, float, float]]

factory1: Factory = Factory(
    id=5711,
    name="Some name",
    address="Some address",
    factoryLines=[
        FactoryLine(
            id=1,
            number=1,
            strandsAmt=2,
            abzug=Abzug(
                id=1,
                invNo=123
            ),
            extruder=Extruder(
                id=1,
                invNo=123,
                name="extruder name"
            )
        ),
        FactoryLine(
            id=2,
            number=2,
            strandsAmt=2,
            abzug=None,
            extruder=None
        )
    ]
)
json1: str = factory1.toJSON()
json2: str = """{
    "id": 5711,
    "name": "Some name",
    "address": "Some address",
    "factoryLines": []
}"""
factory2: Factory = Factory.fromJSON(json2)
```

For classes definitions it is possible to give boolean args as for simple dataclasses:<br/>
`frozen`, `slots`, `repr`, `order`, `unsafe_hash`, etc.<br/>
```python
class Bar(JSONDataClass, frozen=True, slots=True, order=True):
    id: int
    name: str | None
```
See the [dataclasses] documentation.

[dataclasses]: https://docs.python.org/3/library/dataclasses.html
