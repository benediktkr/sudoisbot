#!/usr/bin/python3

import peewee
from peewee import DateTimeField, TextField, DecimalField, IntegerField
from playhouse.db_url import connect

db = peewee.DatabaseProxy()

class BaseModel(peewee.Model):
    class Meta:
        database = db

class Temps(BaseModel):
    timestamp = DateTimeField(index=True)
    name = TextField()
    temp = DecimalField()
    humidity = IntegerField(null=True)
    extra = TextField(null=True)

    class Meta:
        indexes = (
            (('timestamp', 'name'), True),
        )


class Sensor(BaseModel):
    name = TextField()
    sensortype = TextField()
    host = TextField()
    comment = TextField()
    created = DateTimeField()

def create_tables(uri):
    db.initialize(connect(uri))
    with db:
        db.create_tables([Temps])
