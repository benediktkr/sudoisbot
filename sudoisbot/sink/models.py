#!/usr/bin/python3

import json

import peewee
from peewee import DateTimeField, TextField, DecimalField, CharField
from peewee import MySQLDatabase
from peewee import IntegrityError
from loguru import logger

db_proxy = peewee.DatabaseProxy()

def dbconnect(**mysqlconf):
    db = MySQLDatabase(**mysqlconf)
    db_proxy.initialize(db)
    return db

# db = connect(dburl)
#     models.db.initialize(db)
#         try:
#             with models.db:
#                 models.Temps.create(timestamp=j['timestamp'],
#                                     name=j['name'],
#                                     temp=j['temp'],
#                                     extra=extra)
#         except IntegrityError as e:
#             logger.error(e)

class BaseModel(peewee.Model):
    class Meta:
        database = db_proxy

class Temperatures(BaseModel):
    time = DateTimeField(index=True)
    name = CharField(max_length=32)
    location = TextField()
    environment = TextField()
    source = TextField()
    temp = DecimalField()
    json = TextField(null=False)


    def as_msg(self):
        return json.loads(self.json)

    @classmethod
    def insert_msg(cls, msg):
        name = msg['tags']['name']

        try:
            return cls.create(
                time = msg['time'],
                name = name,
                location = msg['tags']['location'],
                environment = msg['tags']['environment'],
                source = msg['tags']['source'],
                temp = msg['fields']['value'],
                json = json.dumps(msg)
            )
        except IntegrityError as e:
            logger.error(f"error on message from {name}")
            logger.error(e)
            return None


    class Meta:
        indexes = (
            (('time', 'name'), True),
        )

class Humidities(BaseModel):
    time = DateTimeField(index=True)
    name = TextField()
    location = TextField()
    environment = TextField()
    source = TextField()
    humidity = DecimalField()
    json = TextField(null=False)

    @classmethod
    def insert_msg(cls, msg):
        name = msg['tags']['name']

        try:
            return cls.create(
                time = msg['time'],
                name = msg['tags']['name'],
                location = msg['tags']['location'],
                environment = msg['tags']['environment'],
                source = msg['tags']['source'],
                humidity = msg['fields']['value'],
                json = json.dumps(msg)
            )
        except IntegrityError as e:
            logger.error(f"error on message from {name}")
            logger.error(e)
            return None

    class Meta:
        indexes = (
            (('time', 'humidity'), True),
        )

class Sensor(BaseModel):
    name = TextField()
    sensortype = TextField()
    host = TextField()
    comment = TextField()
    created = DateTimeField()
