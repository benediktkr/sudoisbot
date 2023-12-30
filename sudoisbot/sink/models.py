#!/usr/bin/python3

import json
from datetime import datetime, timedelta

import peewee
from peewee import DateTimeField, TextField, DecimalField, CharField, BooleanField
from playhouse.shortcuts import ReconnectMixin
from retry import retry
from loguru import logger


db_proxy = peewee.DatabaseProxy()

class LoguruRewriter(object):
    @staticmethod
    def warning(fmt, error, delay):
        """retry writes a python-format string, and loguru doesnt handle that correctly.
        """
        old_fmt_parts = fmt.split(' ')
        new_fmt_parts = ["{}" if a.startswith("%") else a for a in old_fmt_parts]
        new_fmt = ' '.join(new_fmt_parts)
        message = new_fmt.format(error, delay)
        logger.warning(message)

class ReconnectMySQLDatabase(ReconnectMixin, peewee.MySQLDatabase):
    pass


def dbconnect(**mysqlconf):
    db = ReconnectMySQLDatabase(**mysqlconf)
    db_proxy.initialize(db)
    return db


def seconds(secs):
    return datetime.now()-timedelta(seconds=secs)


class BaseModel(peewee.Model):
    @classmethod
    def get_last(cls, name):
        # http://docs.peewee-orm.com/en/latest/peewee/querying.html
        return cls.select().where(cls.name == name).order_by(-cls.id).get()

    @classmethod
    def get_last_many(cls, names):
        return [cls.get_last(a) for a in names]

    @classmethod
    def get_recent(cls, name, secs):
        last = cls.get_last(name)
        last_age = datetime.utcnow() - last.time
        if last_age.total_seconds() <= float(secs):
            return last
        else:
            logger.info(f"Last value in {cls.__name__} is older than {secs}s, age: {last_age}")
            raise cls.DoesNotExist

    @classmethod
    def retry_create(cls, *args, **kwargs):
        try:
            return cls._retry_create(*args, **kwargs)
        except peewee.PeeweeException as e:
            logger.error(e)
            raise SystemExit("Aborting.") from e

    @classmethod
    @retry((ConnectionRefusedError, peewee.PeeweeException), tries=4, delay=1, backoff=2, logger=LoguruRewriter)
    def _retry_create(cls, *args, **kwargs):
        """tries 4 times, doubling the backoff time each time.

        after max retries, the method that wraps this method gets the exception and exist/crashes

        1st: 1 seconds
        2nd: 2 seconds
        3rd: 4 seconds
        4th: crash
        """
        try:
            return cls.create(*args, **kwargs)
        except peewee.IntegrityError as e:
            tags = kwargs.get('tags', dict())
            name = tags.get('name')
            logger.error(f"IntegrityError on message from {name}")
            logger.error(e)
            return None

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
        return cls.retry_create(
            time = msg['time'],
            name = name,
            location = msg['tags']['location'],
            environment = msg['tags']['environment'],
            source = msg['tags']['source'],
            temp = msg['fields']['value'],
            json = "" #json = json.dumps(msg)
        )

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
        return cls.retry_create(
            time = msg['time'],
            name = name,
            location = msg['tags']['location'],
            source = msg['tags']['source'],
            temp = msg['fields']['temp'],
            humidity = msg['fields']['humidity'],
            desc = msg['fields']['desc'],
            wind_speed = msg['fields']['wind_speed'],
            wind_deg = msg['fields']['wind_deg'],
            json = ""
            #json = json.dumps(msg)
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
        return cls.retry_create(
            time = msg['time'],
            name = msg['tags']['name'],
            location = msg['tags']['location'],
            environment = msg['tags']['environment'],
            source = msg['tags']['source'],
            humidity = msg['fields']['value'],
            json = ""
            #json = json.dumps(msg)
        )

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
        return cls.retry_create(
            time=new['time'],
            name=new['tags']['name'],
            home=new['fields']['home'],
            location=new['tags']['location'],
            json = ""
            #json=json.dumps(new)
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
