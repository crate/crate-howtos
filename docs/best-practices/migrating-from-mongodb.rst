.. meta::
    :last-reviewed: 2020-08-31

.. highlight:: psql

======================
Migrating from MongoDB
======================

.. rubric:: Table of contents

.. contents::
   :local:


Exporting data from MongoDB
===========================

When exporting data from a MongoDB collection, it is exported in the `MongoDB
Extended JSON`_ file format, which includes additional type information. This
additional information makes the format unsuitable for importing into a CrateDB
table. To help with this problem, we have created a `MongoDB migration tool`_
that can export a MongoDB collection while converting it into a CrateDB friendly
format.

First, download & install the tool according to the instructions on the repo.
You can then export a collection into a JSON file, as follows:

.. code-block:: sh

    $ migr8 export --host <mongodb hostname> --port <mongodb port> --database <dbname> --collection <data> > data.json


Importing data into CrateDB
===========================

Before the converted file can be imported into CrateDB a table has to be
created.

A basic CREATE TABLE statement looks as follows::

    cr> CREATE TABLE mytable (
    ...     name TEXT,
    ...     obj OBJECT (DYNAMIC)
    ... ) CLUSTERED INTO 5 SHARDS WITH (number_of_replicas = 0);
    CREATE OK, 1 row affected (... sec)

In CrateDB each field is indexed by default. It is not necessary to create
any additional indices.

However, if some fields are never used for filtering, indexing can be turned
off::

    cr> CREATE TABLE mytable2 (
    ...     name TEXT,
    ...     obj OBJECT (DYNAMIC),
    ...     dummy TEXT INDEX OFF
    ... ) CLUSTERED INTO 5 SHARDS WITH (number_of_replicas = 0);
    CREATE OK, 1 row affected (... sec)

For fields that contain text consider using a full-text analyzer. This will
enable great full-text search capabilities. See `Indices and Fulltext Search`_
for more information.

CrateDB is able to create dynamically defined table schemas, which can be
extended as data is inserted, so it is not necessary to define all the columns
up front::

    cr> CREATE TABLE mytable3 (
    ...     name TEXT,
    ...     obj OBJECT (DYNAMIC),
    ...     dumm TEXT index off
    ... ) CLUSTERED INTO 5 SHARDS WITH (number_of_replicas = 0, column_policy = 'dynamic')

Given the table above, it is possible to insert new columns at the top level of
the table and insert arbitrary objects into the **obj** column::

    cr> INSERT INTO mytable3 (name, obj, newcol, dummy) VALUES
    ... ('Trillian', {gender = 'female'}, 2804, 'dummy');
    INSERT OK, 1 row affected (... sec)

    cr> REFRESH TABLE mytable3;
    REFRESH OK, 1 row affected (... sec)

.. Hidden: wait for schema update so that newcol is available

    cr> _wait_for_schema_update('doc', 'mytable3', 'newcol')

::

    cr> SELECT * FROM mytable3;
    +-------+----------+--------+----------------------+
    | dummy | name     | newcol | obj                  |
    +-------+----------+--------+----------------------+
    | dummy | Trillian |   2804 | {"gender": "female"} |
    +-------+----------+--------+----------------------+
    SELECT 1 row in set (... sec)

However, this has some limitations. For example timestamps in long format won't
be recognised as timestamps. Due to this limitation it is recommended to
specify fields up front.

In these cases, the `MongoDB migration tool`_ can be used to autogenerate
a schema to fit your collection. For example, to create the above schema without
resorting to using a dynamic table definition:

.. code-block:: sh

    $ migr8 extract --host <mongodb host> --port <mongodb port> --database <dbname> --collection <data> --scan full --out schema.json
    $ migr8 translate --infile schema.json

    MongoDB -> CrateDB Exporter :: Schema Extractor

    Collection 'mytable':
    CREATE TABLE IF NOT EXISTS "doc"."mytable" (
        "name" TEXT,
        "obj" OBJECT (DYNAMIC) AS (
            "gender" TEXT
        ),
        "newcol" INTEGER,
        "dummy" TEXT
    );

This can be useful for collections with complex or heavily-nested schemas.

.. SEEALSO::

 - `Data Definition`_
 - `CREATE TABLE`_


After the table has been created the file can be imported using
`COPY FROM`_.

There is an entire section dedicated on how to do a data import efficiently.
Continue reading there: :ref:`efficient_data_import`.

.. _Indices and Fulltext Search: https://crate.io/docs/crate/reference/sql/ddl/indices_full_search.html
.. _Data Definition: https://crate.io/docs/crate/reference/sql/ddl/index.html
.. _CREATE TABLE: https://crate.io/docs/crate/reference/sql/reference/create_table.html
.. _COPY FROM: https://crate.io/docs/crate/reference/sql/reference/copy_from.html
.. _MongoDB Extended JSON: http://docs.mongodb.org/manual/reference/mongodb-extended-json/
.. _MongoDB migration tool: https://github.com/crate/mongodb-cratedb-migration-tool
