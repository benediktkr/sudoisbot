#!/usr/bin/python3

import json
from datetime import datetime, timezone, timedelta

import peewee
from peewee import DateTimeField, TextField, DecimalField, CharField, BooleanField
from peewee import MySQLDatabase
from peewee import IntegrityError
from loguru import logger

db_proxy = peewee.DatabaseProxy()

def seconds(secs):
    return datetime.now(timezone.utc)-timedelta(seconds=secs)

def dbconnect(**mysqlconf):
    db = MySQLDatabase(**mysqlconf)
    db_proxy.initialize(db)
    return db

class BaseModel(peewee.Model):
    @classmethod
    def get_last(cls, name):
        # http://docs.peewee-orm.com/en/latest/peewee/querying.html
        return cls.select().where(
            cls.name == name).order_by(-cls.id).get()

    @classmethod
    def get_last_many(cls, names):
        return [cls.get_last(a) for a in names]

    @classmethod
    def get_recent(cls, name, secs):
        return cls.select().where(
            cls.time > seconds(secs) and cls.name == name).order_by(
                cls.time.desc()).get()

    def json_msg(self):
        return json.loads(self.json)

    class Meta:
        database = db_proxy

class Temperatures(BaseModel):
    time = DateTimeField(index=True)
    name = CharField(max_length=32, index=True)
    location = TextField()
    environment = TextField()
    source = TextField()
    temp = DecimalField()
    json = TextField(null=False)


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

class Weather(BaseModel):
    time = DateTimeField(index=True)
    name = CharField(max_length=32, index=True)
    location = TextField()
    source = TextField()
    temp = DecimalField()
    humidity = DecimalField()
    desc = CharField(max_length=128)
    wind_speed = DecimalField()
    wind_deg = DecimalField()
    json = TextField(null=False)

    @classmethod
    def insert_msg(cls, msg):
        name = msg['tags']['name']

        try:
            return cls.create(
                time = msg['time'],
                name = name,
                location = msg['tags']['location'],
                source = msg['tags']['source'],
                temp = msg['fields']['temp'],
                humidity = msg['fields']['humidity'],
                desc = msg['fields']['desc'],
                wind_speed = msg['fields']['wind_speed'],
                wind_deg = msg['fields']['wind_deg'],
                json = json.dumps(msg)
            )
        except IntegrityError as e:
            logger.error(f"error on message from {name}")
            logger.error(e)
            return None


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

class People(BaseModel):

    time = DateTimeField(index=True)
    updated = DateTimeField()
    name = CharField(max_length=32, index=True)
    home = BooleanField(null=False)
    location = TextField()
    json = TextField(null=False)

    @classmethod
    def get_home_names(cls, folks):
        return [a for a in folks if cls.get_last(a).home]

    @classmethod
    def insert_msg(cls, new):
        return cls.create(
            time=new['time'],
            name=new['tags']['name'],
            home=new['fields']['home'],
            location=new['tags']['location'],
            json=json.dumps(new)
        )

    @classmethod
    def update_state_if_changed(cls, new):
        try:
            current = cls.get_last(new['tags']['name'])
            if current.home != new['fields']['home']:
                logger.debug(f"state of '{new['tags']['name']}' changed to '{new['fields']['home']}'")
                cls.insert_msg(new)
            else:
                return current
        except People.DoesNotExist:
            cls.insert_msg(new)

    class Meta:
        database = db_proxy
