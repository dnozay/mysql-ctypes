import math
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from MySQLdb.constants import field_types


def literal(value):
    return lambda conn, obj: value

def unicode_to_quoted_sql(connection, obj):
    return connection.string_literal(obj.encode(connection.character_set_name()))

def object_to_quoted_sql(connection, obj):
    if hasattr(obj, "__unicode__"):
        return unicode_to_quoted_sql(connection, unicode(obj))
    return connection.string_literal(str(obj))

def fallback_encoder(obj):
    return object_to_quoted_sql

def literal_encoder(connection, obj):
    return str(obj)

def datetime_encoder(connection, obj):
    return connection.string_literal(obj.strftime("%Y-%m-%d %H:%M:%S"))

def set_encoder(connection, obj):
    return connection.string_literal(','.join(obj))

_simple_field_encoders = {
    type(None): lambda connection, obj: "NULL",
    int: literal_encoder,
    bool: lambda connection, obj: str(int(obj)),
    unicode: unicode_to_quoted_sql,
    str: object_to_quoted_sql,
    datetime: datetime_encoder,
    set: set_encoder,
}

def simple_encoder(obj):
    return _simple_field_encoders.get(type(obj))

DEFAULT_ENCODERS = [
    simple_encoder,
    fallback_encoder,
]


def datetime_decoder(value):
    date_part, time_part = value.split(" ", 1)
    return datetime.combine(
        date_decoder(date_part),
        time(*[int(part) for part in time_part.split(":")])
    )

def date_decoder(value):
    return date(*[int(part) for part in value.split("-")])

def time_decoder(value):
    # MySQLdb returns a timedelta here, immitate this nonsense.
    hours, minutes, seconds = value.split(":")
    td = timedelta(
        hours = int(hours),
        minutes = int(minutes),
        seconds = int(seconds),
        microseconds = int(math.modf(float(seconds))[0]*1000000),
    )
    if hours < 0:
        td = -td
    return td

def timestamp_decoder(value):
    if " " in value:
        return datetime_decoder(value)
    raise NotImplementedError

def str_to_unicode(connection):
    return lambda value: value.decode(connection.character_set_name(), 'replace')

def set_decoder(value):
    return set(value.split(','))

_simple_field_decoders = {
    field_types.TINY: int,
    field_types.SHORT: int,
    field_types.LONG: int,
    field_types.LONGLONG: int,
    field_types.YEAR: int,

    field_types.FLOAT: float,
    field_types.DOUBLE: float,

    field_types.DECIMAL: Decimal,
    field_types.NEWDECIMAL: Decimal,

    field_types.LONG_BLOB: str,
    field_types.BLOB: str,
    field_types.VAR_STRING: str,
    field_types.STRING: str,

    field_types.DATETIME: datetime_decoder,
    field_types.DATE: date_decoder,
    field_types.TIME: time_decoder,
    field_types.TIMESTAMP: timestamp_decoder,

    field_types.SET: set_decoder,
}

_advanced_field_decoders = {
    field_types.VAR_STRING: str_to_unicode,
    field_types.STRING: str_to_unicode,
}

def advanced_decoder(connection, field):
    param = _advanced_field_decoders.get(field[1])
    if param:
        return param(connection)

def fallback_decoder(connection, field):
    return _simple_field_decoders.get(field[1])


DEFAULT_DECODERS = [
    advanced_decoder,
    fallback_decoder,
]

# MySQLdb compatibility
conversions = _simple_field_decoders
conversions.update(_simple_field_encoders)
