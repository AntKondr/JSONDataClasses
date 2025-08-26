## Module for simple data objects (compatible with json) description with python classes

pip:
<pre><code><span style="color: #e5c07b">JSONDataClasses</span> @ git+ssh://git@gitlab.vekarus.loc/VekaProg/jsondataclasses.git@master
</code></pre>

## Usage
```python
from JSONDataClasses import JSONCodable

class Abzug(JSONCodable):
    id: int
    invNo: int

class Extruder(JSONCodable):
    id: int
    invNo: int
    name: str | None

class FactoryLine(JSONCodable):
    id: int
    number: int
    strandsAmt: int
    abzug: Abzug | None
    extruder: Extruder | None

class Factory(JSONCodable):
    id: int
    name: str
    address: str
    factoryLines: list[FactoryLine]

class GraphPoints(JSONCodable):
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
print(factory2.toJSON(indent=2))
```
