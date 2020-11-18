.. highlight:: psql

.. _migrating_from_mysql:

====================
Migrating from MySQL
====================

Various ways exist to migrate your existing data from MySQL_ to CrateDB_.
However, these methods may differ in performance. A fast and reliable way to
migrate is to use CrateDB's existing export and import tools.

.. rubric:: Table of contents

.. contents::
   :local:


Setting up the example table
============================

In this example, you have an existing table ``foo`` in MySQL with the
following schema::

  mysql> CREATE TABLE foo (
  ...       id integer primary key,
  ...       name varchar(255),
  ...       date datetime,
  ...       fruits set('apple', 'pear', 'banana')
  ...    ) CHARACTER SET utf8 COLLATE utf8_unicode_ci;

To import sample data into ``foo``::

  mysql> INSERT INTO foo (id, name, date, fruits)
  ...    VALUES (1, 'foo', '2014-10-31 09:22:56', 'apple,banana'),
  ...           (2, 'bar', null, 'pear');


Exporting data from MySQL
=========================

MySQL does not support ``JSON`` as an output format, but it is possible to
write to a file using the ``csv`` format.

Example::

  mysql> SELECT id, name
  ...    INTO OUTFILE '/tmp/dump.csv'
  ...      CHARACTER SET utf8
  ...      FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  ...      LINES TERMINATED BY '\n'
  ...    FROM foo;

Make sure fields are separated by a comma (``,``), that values are quoted with
a pair of ``"``, and that lines are terminated by the newline character ``\n``.

Note that you specify ``utf8`` as encoding for writing into the outfile. This is
important because CrateDB requires ``utf8`` encoding.

You may need to set the character encoding of the client and ``mysqld`` in the
``my.cnf``:

.. code-block:: ini

  [client]
  default-character-set=utf8
  [mysqld]
  character-set-server=utf8

All values written to ``csv`` are quoted and therefore interpreted as strings
when read from the convert script later.


Converting date/time types
--------------------------

The standard output for `date/time types in MySQL`_ is a string. However,
CrateDB uses a ``long`` type to store timestamps (with millisecond precision).
To prevent problems with dates that have timezone information, use MySQL's
builtin ``UNIX_TIMESTAMP`` function to convert ``date``, ``time``,
``datetime``, ``timestamp`` and ``year`` types into UNIX timestamps directly in
the ``SELECT`` statement.

The output of this function must be multiplied by ``1000`` (converting ``s`` to
``ms``) to obtain the correct ``long`` value that can be used for importing
into CrateDB.

::

  mysql> SELECT UNIX_TIMESTAMP(datetime_column)*1000 from table_name;

The final export query::

  mysql> SELECT id, name, UNIX_TIMESTAMP(date)*1000, fruits
  ...    INTO OUTFILE '/tmp/dump.csv'
  ...      CHARACTER SET utf8
  ...      FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  ...      LINES TERMINATED BY '\n'
  ...    FROM foo;


Importing data into CrateDB
===========================

Use the ``COPY FROM`` statement to import your CSV file into CrateDB.

For more in-depth documentation on ``COPY FROM``, see `COPY FROM`_.

::

  cr> COPY foo_imported FROM '/tmp/dump.csv' WITH (bulk_size=1000);

.. SEEALSO::

   Read :ref:`efficient_data_import` for more information how to import huge
   datasets into CrateDB.


Third-party tool: csvkit
========================

The tools provided by `csvkit`_ allow you to directly insert CSV data into
CrateDB via SQLAlchemy, using CrateDB’s native driver to create the table,
guess the corresponding data types, and insert any data found in the CSV file.

For example:

.. code-block:: sh

  sh$ csvsql --db crate://localhost:4200 --insert /tmp/dump.csv

.. SEEALSO::

  See also the documentation of `csvsql`_. To use the SQLAlchemy driver of
  CrateDB, the latest version of the `CrateDB Python package`_ is required.


.. _COPY FROM: https://crate.io/docs/crate/reference/sql/reference/copy_from.html
.. _CrateDB Python package: https://pypi.org/project/crate/
.. _CrateDB: https://crate.io/
.. _csvkit: https://csvkit.readthedocs.io/en/540/index.html
.. _csvsql: https://csvkit.readthedocs.io/en/540/scripts/csvsql.html
.. _date/time types in MySQL: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-types.html
.. _MySQL: https://www.mysql.com/
