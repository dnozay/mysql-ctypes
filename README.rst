mysql-ctypes
============

A ``ctypes`` implementation of a PEP 249 (DB API 2.0) compliant database
driver for use with MySQL. It is importable as ``MySQLdb`` for compatibility
with the extremely common C-extension, by the same name. It is tested under
CPython 2.6, CPython 2.7, and PyPy 1.5.

There are a number of things to note:

 * This was originally developed for use with PyPy, though it works with both
   CPython and PyPy, where performance is concerned it will try to favor PyPy.
 * The original ``MySQLdb``, with which we attempt to remain compatible, is
   not always 100% in line with the DB API spec, where it was necessary for
   use with the project this was developed for, we've followed ``MySQLdb``
   rather than the spec, sadly.
 * Not all errors are appropriately upgraded to a ``DatabaseError`` subclass
   (e.g. ``ProgrammingError`` or ``IntegrityError``) these will be done on an
   ongoing bases, as tests for the conditions (or reasons they are impossible
   to write) are developed.
 * This project is strictly test-driven-developed, if you're interested in
   contributing, we appreciate patches, but please make sure they include
   tests.

Tests are run using ``py.test``, you can invoke it directly on the command
line::

    $ py.test

Or use ``tox`` to automatically test it against CPython 2.6 and 2.7, as well as
PyPy::

    $ tox

You may need to create the test database with::

    $ mysql
    mysql> create database test_mysqldb;


