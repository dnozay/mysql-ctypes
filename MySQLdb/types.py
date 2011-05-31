from MySQLdb.constants import field_types


class FieldType(object):
    def __init__(self, *args):
        self.values = frozenset(args)

    def __eq__(self, other):
        if isinstance(other, FieldType):
            return self.values.issuperset(other.values)
        return other in self.values


BINARY = FieldType()
DATETIME = FieldType()
NUMBER = FieldType()
ROWID = FieldType()
STRING = FieldType(field_types.VAR_STRING, field_types.STRING)