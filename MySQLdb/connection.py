import contextlib
from ctypes import (addressof, cast, create_string_buffer, string_at, c_char,
    c_uint, POINTER)

from MySQLdb import cursors, libmysql, converters
from MySQLdb.constants import error_codes


class Connection(object):
    # This alias is for use in stuff called via __del__, which needs to be sure
    # it has a hard ref, so it isn't None'd out.
    _mysql_close = libmysql.c.mysql_close

    MYSQL_ERROR_MAP = {
        error_codes.PARSE_ERROR: "ProgrammingError",
        error_codes.NO_SUCH_TABLE: "ProgrammingError",

        error_codes.DATA_TOO_LONG: "DataError",

        error_codes.DUP_ENTRY: "IntegrityError",
        error_codes.ROW_IS_REFERENCED_2: "IntegrityError",
    }

    from MySQLdb.libmysql_exceptions import (Warning, Error, InterfaceError,
        DataError, DatabaseError, OperationalError, IntegrityError,
        InternalError, ProgrammingError, NotSupportedError)

    def __init__(self, host=None, user=None, passwd=None, db=None, port=0,
        client_flag=0, charset=None, init_command=None, connect_timeout=None,
        sql_mode=None, encoders=None, decoders=None, use_unicode=True,
        conv=None):

        self._db = libmysql.c.mysql_init(None)

        if connect_timeout is not None:
            connect_timeout = c_uint(connect_timeout)
            res = libmysql.c.mysql_options(self._db,
                libmysql.MYSQL_OPT_CONNECT_TIMEOUT,
                cast(addressof(connect_timeout), POINTER(c_char))
            )
            if res:
                self._exception()
        if init_command is not None:
            res = libmysql.c.mysql_options(self._db,
                libmysql.MYSQL_INIT_COMMAND, init_command
            )
            if res:
                self._exception()

        res = libmysql.c.mysql_real_connect(self._db, host, user, passwd, db, port, None, client_flag)
        if not res:
            self._exception()

        if encoders is None:
            encoders = converters.DEFAULT_ENCODERS
        if decoders is None:
            decoders = converters.DEFAULT_DECODERS
        self.real_encoders = encoders
        self.real_decoders = decoders

        # MySQLdb compatibility.
        if conv is not None:
            self.real_decoders.insert(1, lambda conn, field: conv.get(field[1]))
        conv = conv or converters.conversions
        self.encoders = dict(conv.iteritems())

        if charset is not None:
            res = libmysql.c.mysql_set_character_set(self._db, charset)
            if res:
                self._exception()

        if sql_mode is not None:
            with contextlib.closing(self.cursor()) as cursor:
                cursor.execute("SET SESSION sql_mode=%s", (sql_mode,))

        self.autocommit(False)

    def __del__(self):
        if not self.closed:
            self.close()

    def _check_closed(self):
        if self.closed:
            raise self.InterfaceError(0, "")

    def _has_error(self):
        return libmysql.c.mysql_errno(self._db) != 0

    def _exception(self):
        err = libmysql.c.mysql_errno(self._db)
        if not err:
            err_cls = self.InterfaceError
        else:
            if err in self.MYSQL_ERROR_MAP:
                err_cls = getattr(self, self.MYSQL_ERROR_MAP[err])
            elif err < 1000:
                err_cls = self.InternalError
            else:
                err_cls = self.OperationalError
        raise err_cls(err, libmysql.c.mysql_error(self._db))

    @property
    def closed(self):
        return self._db is None

    def close(self):
        self._check_closed()
        self._mysql_close(self._db)
        self._db = None

    def autocommit(self, flag):
        self._check_closed()
        res = libmysql.c.mysql_autocommit(self._db, chr(flag))
        if ord(res):
            self._exception()

    def commit(self):
        self._check_closed()
        res = libmysql.c.mysql_commit(self._db, "COMMIT")
        if ord(res):
            self._exception()

    def rollback(self):
        self._check_closed()
        res = libmysql.c.mysql_rollback(self._db)
        if ord(res):
            self._exception()

    def cursor(self, cursor_class=None, encoders=None, decoders=None):
        if cursor_class is None:
            cursor_class = cursors.Cursor
        if encoders is None:
            encoders = self.real_encoders[:]
        if decoders is None:
            decoders = self.real_decoders[:]
        return cursor_class(self, encoders=encoders, decoders=decoders)

    def string_literal(self, obj):
        self._check_closed()
        obj = str(obj)
        buf = create_string_buffer(len(obj) * 2)
        length = libmysql.c.mysql_real_escape_string(self._db, buf, obj, len(obj))
        return "'%s'" % string_at(buf, length)

    def character_set_name(self):
        self._check_closed()
        return libmysql.c.mysql_character_set_name(self._db)

    def get_server_info(self):
        self._check_closed()
        return libmysql.c.mysql_get_server_info(self._db)

    def ping(self):
        res = libmysql.c.mysql_ping(self._db)
        if res:
            self._exception()

def connect(*args, **kwargs):
    return Connection(*args, **kwargs)
