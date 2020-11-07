#!/usr/bin/python3

from dataclasses import asdict, dataclass


@dataclass
class Typed:
    def __post_init__(self):
        for (name, field_type) in self.__annotations__.items():
            if not isinstance(self.__dict__[name], field_type):
                current_type = type(self.__dict__[name])
                raise ValueError(f"The field '{name}' was  '{current_type}' instead of '{field_type}'")

    def as_dict(self):
        return asdict(self)

    def __getitem__(self, key):
        from loguru import logger
        logger.warning("not sure if i will keep this, prob use .as_dict()?")
        return self.__dict__[key]


@dataclass
class Tags(Typed):
    name: str
    location: str
    kind: str

@dataclass
class Message(Typed):
    time: str
    measurement: str
    fields: dict
    tags: Tags

    @classmethod
    def from_msg(cls, topic, msg):

        # thee type of the 'fields' type
        fields_type = cls.__annotations__['fields']

        return cls(
            measurement=topic.decode(),
            time=msg['time'],
            tags=Tags(**msg['tags']),
            fields=fields_type(**msg['fields'])
        )

    @classmethod
    def from_topic(cls, topic, msg):
        if topic == b'rain':
            return RainMessage.from_msg(topic, msg)
        else:
            return Message.from_msg(topic, msg)



@dataclass
class RainFields(Typed):
    value: bool
    value_int: int

@dataclass
class RainMessage(Message):
    time: str
    measurement: str
    fields: RainFields
    tags: Tags

    def as_csv(self):
        return f"{self.time},{self.tags.name},{self.fields.value_int}"


@dataclass
class InfluxDBDatapoint(Typed):
    time: str
    measurement: str
    fields: dict
    tags: dict
