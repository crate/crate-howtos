.. meta::
    :last-reviewed: 2020-09-29

.. highlight:: psql

.. _efficient_data_import:

====================================
Importing huge datasets into CrateDB
====================================

Introduction
============

Projects often contain pre-existing data that needs to be imported and
sometimes the amount of data is significant.

Assuming that you have an existing application that generates a few hundred
thousand records a day and you would like to migrate to a new technology stack
with CrateDB as the database backend. You will need a strategy to import the
existing millions of records into CrateDB as quickly as possible.

This best practices tutorial will guide you through the process on how to
import your data quickly and safely.


.. rubric:: Table of contents

.. contents::
   :local:


Configuring your tables
=======================

Defining the data structure
---------------------------

Before starting the import, you need to carefully define your table structure
in CrateDB. Decisions made at this point will influence the import process
later.

For this example, say you have a single ``users`` table with 6 columns of
various types. You can create it with the following statement::

  cr> CREATE TABLE users (
  ...   id INT primary key,
  ...   name TEXT,
  ...   day_joined TIMESTAMP,
  ...   bio TEXT INDEX using fulltext,
  ...   address OBJECT (dynamic) AS (
  ...     city TEXT,
  ...     country TEXT
  ...   )
  ... );
  CREATE OK, 1 row affected (... sec)


.. _import_shards_replicas:

Setting shards and replicas
---------------------------

For each table, if you do not set the number of shards and/or number of
replicas, the default configuration will be used:

:shards:
  Depends on the number of data-nodes in the cluster (see `CLUSTERED clause`_)
:replicas:
  1

You should choose the number of shards wisely. The choice depends on the number
of nodes in the cluster as well as on the amount of data that goes into the
table.

Assuming there are 6 nodes in the cluster, you can put 2 shards on each node,
giving you a total of 12 shards. This should be enough for millions of
records.

Shards can be thought of as "virtual nodes". You should create enough for your
scaling needs, but use as few as possible to keep the resource overhead (such
as file descriptors and memory) as small as possible.

When importing data, you should set the number of replicas to a minimum,
ideally to zero. If the import fails, you can drop the table and re-import
again. When the import succeeds, adjust the number of replicas according to
your availability requirements.

The ``CREATE TABLE`` statement now looks like::

  cr> CREATE TABLE users(
  ...   id INT primary key,
  ...   name TEXT,
  ...   day_joined TIMESTAMP,
  ...   bio TEXT INDEX using fulltext,
  ...   address OBJECT (dynamic) AS (
  ...     city TEXT,
  ...     country TEXT
  ...   )
  ... ) CLUSTERED INTO 12 shards
  ... WITH (number_of_replicas = 0);
  CREATE OK, 1 row affected (... sec)

.. SEEALSO::

  - `Replication`_


Setting the refresh interval
----------------------------

Another way to speed up importing is to set the refresh interval of the table
to 0. This will disable the periodic refresh of the table that is needed to
minimize the effect of eventual consistency and also minimize the overhead
during import.

::

  cr> ALTER TABLE users SET (refresh_interval = 0);
  ALTER OK, -1 rows affected (... sec)

.. hide:

  cr> DROP TABLE users;
  DROP OK, 1 row affected (... sec)

You can also set the refresh interval in the ``CREATE TABLE`` statement::

  cr> CREATE TABLE users (
  ...   id INT primary key,
  ...   name TEXT,
  ...   day_joined TIMESTAMP,
  ...   bio TEXT INDEX using fulltext,
  ...   address OBJECT (dynamic) AS (
  ...     city TEXT,
  ...     country TEXT
  ...   )
  ... ) CLUSTERED INTO 12 shards
  ... WITH (
  ...   number_of_replicas = 0,
  ...   refresh_interval = 0
  ... );
  CREATE OK, 1 row affected (... sec)

Once the import is finished, you can set the refresh interval to a reasonable
value (time in ms)::

  cr> ALTER TABLE users SET (refresh_interval = 1000);
  ALTER OK, -1 rows affected (... sec)

.. SEEALSO::

  - `Refresh`_
  - `refresh_interval`_


Importing the data
==================

Once the table is created, you can start importing the data.

JSON import format
------------------

CrateDB has native support for JSON formatted data, where each line is a
JSON string and represents a single record. Empty lines are skipped. The
keys of the JSON objects are mapped to columns when imported - nonexistent
columns will be created if necessary.

For example: ``users.json``

.. code-block:: json

   {"id": 1, "name": "foo", "day_joined": 1408312800, "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Dornbirn", "country": "Austria"}}
   {"id": 2, "name": "bar", "day_joined": 1408312800, "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Berlin", "country": "Germany"}}


``COPY FROM``
-------------

Use the ``COPY FROM`` command to import data into a table efficiently.
For more in-depth documentation on ``COPY FROM``, see `COPY FROM`_.

Upon execution, each node will check the provided path *locally* to see whether
the file exists and to import the data it contains. In this example, this command
will check ``/tmp/best_practices_data/`` on each node in the cluster to import
data from a file called ``users.json``. Please note that if the file is not
found, the command will return successfully, reporting ``COPY OK, 0 rows
affected (... sec)``.

::

  cr> COPY users FROM '/tmp/best_practice_data/users.json';
  COPY OK, 150 rows affected (... sec)

.. hide:

  cr> REFRESH TABLE users;
  REFRESH OK, 1 row affected (... sec)

  cr> delete from users;
  DELETE OK, 150 rows affected (... sec)

  cr> REFRESH TABLE users;
  REFRESH OK, 1 row affected (... sec)

.. NOTE::

  When importing data using ``COPY FROM``, CrateDB does not check whether the
  types from the columns and the types from the import file match. It does not
  cast the types to their target but will always import the data as given in
  the source file.


Bulk size
.........

The bulk size defines the amount of lines that are read at once and imported
into the table. You can specify it in the ``WITH`` clause of the statement and
defaults to 10,000 if not specified.

For example::

  cr> COPY users FROM '/tmp/best_practice_data/users.json'
  ... WITH (bulk_size = 2000);
  COPY OK, 150 rows affected (... sec)

.. hide:

  cr> REFRESH TABLE users;
  REFRESH OK, 1 row affected (... sec)

  cr> delete from users;
  DELETE OK, 150 rows affected (... sec)

  cr> REFRESH TABLE users;
  REFRESH OK, 1 row affected (... sec)

In our example it will not make a difference, but if you have a more complex
dataset with a lot of columns and large values, it makes sense to decrease the
``bulk_size``. Setting ``bulk_size`` too high might consume a lot of node
resources while a low ``bulk_size`` can increase the overhead per request.


Compression
...........

If your data is not stored locally on the nodes, but somewhere on the network
(i.e. on a NAS or on S3), it is recommended to use gzip compressed files to
reduce network traffic.

CrateDB does not automatically detect compression, so you will need to specify
gzip compression in the ``WITH`` clause.

For example::

  cr> COPY users FROM '/tmp/best_practice_data/users.json.gz'
  ... WITH (compression = 'gzip');
  COPY OK, 150 rows affected (... sec)

.. hide:

  cr> REFRESH TABLE users;
  REFRESH OK, 1 row affected (... sec)


Splitting tables into partitions
================================

Sometimes you want to split your table into partitions to be able to handle
large datasets more efficiently (i.e. for queries to run on a reduced set of
rows).

Partitions can be created using the ``CREATE TABLE`` statement using the
``PARTITIONED BY`` clause.

A partition column has to be part of the primary key (if one was explicitly
declared). In this example, this constraint is added to the newly created
partition column.

.. hide:

  cr> DROP TABLE users;
  DROP OK, 1 row affected (... sec)

::

  cr> CREATE TABLE users (
  ...   id INT primary key,
  ...   name TEXT,
  ...   day_joined TIMESTAMP primary key,
  ...   bio TEXT INDEX using fulltext,
  ...   address OBJECT (dynamic) AS (
  ...     city TEXT,
  ...     country TEXT
  ...   )
  ... ) CLUSTERED INTO 6 shards
  ... PARTITIONED BY (day_joined)
  ... WITH (number_of_replicas = 0);
  CREATE OK, 1 row affected (... sec)

To import data into partitioned tables efficiently, you should import each
table partition separately. Since the value of the table partition is not
stored in the column of the table, the JSON source must not contain the
column value.

For example: ``users_1408312800.json``

.. code-block:: json

   {"id": 1, "name": "foo", "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Dornbirn", "country": "Austria"}}
   {"id": 2, "name": "bar", "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Berlin", "country": "Germany"}}

The value of the partition column must be defined in the ``COPY FROM``
statement using the ``PARTITION`` clause::

  cr> COPY users PARTITION (day_joined=1408312800)
  ... FROM '/tmp/best_practice_data/users_1408312800.json';
  COPY OK, 23 rows affected (... sec)

This way, CrateDB does not need to resolve the partition for each row that is
imported, but can store it directly into the correct place resulting in a much
faster import.

However, it is still possible (but not recommended) to import into partitioned
tables without the ``PARTITION`` clause and have the column value in the
source.

When importing data into a partitioned table with existing partitions, it may
be desirable to apply import optimizations, such as to disable the `refresh
interval`_, for newly created partitions only. This can be done by altering the
partitioned table *only* by using the `ALTER TABLE ONLY`_ statement.

Similarly, the number of shards can be adjusted for newly created partitions to
adapt to the increasing data volume! Simply use ``ALTER TABLE users SET
(number_of_shards = X)`` before creating a new partition.

.. SEEALSO::

  - Detailed documentation of `partitioned tables`_
  - Table creation of `PARTITIONED BY clause`_
  - `Alter a partitioned table`_


Summary
=======

Importing huge datasets is not difficult as long as a few things are kept in
mind:

- Reduce the number of replicas as much as possible, ideally to 0. Replication
  slows down the import process significantly.
- Use only as many shards as you really need.
- Disable the periodic table refresh by setting the refresh interval to 0
  during import.
- Adjust the bulk size of the import depending on the size of your records.
- Import table partitions separately using the ``PARTITION`` clause in the
  ``COPY TO`` statement.

.. TIP::

   Import speed significantly increases with increasing disk I/O. Using SSDs for
   CrateDB is recommended anyway, but having one more disk (by adding another
   node) in the cluster can make quite a difference.


Further reading
===============

.. SEEALSO::

  - `Import/Export`_

.. _CLUSTERED clause: http://crate.io/docs/crate/reference/sql/reference/create_table.html#clustered-clause
.. _Replication: https://crate.io/docs/crate/reference/sql/ddl/replication.html#replication
.. _Refresh: https://crate.io/docs/crate/reference/sql/refresh.html
.. _refresh interval: https://crate.io/docs/crate/reference/sql/refresh.html
.. _refresh_interval: https://crate.io/docs/crate/reference/sql/reference/create_table.html#refresh-interval
.. _COPY FROM: https://crate.io/docs/crate/reference/sql/reference/copy_from.html
.. _ALTER TABLE ONLY: https://crate.io/docs/crate/reference/sql/partitioned_tables.html#alter-table-only
.. _partitioned tables: https://crate.io/docs/crate/reference/sql/partitioned_tables.html
.. _PARTITIONED BY clause: https://crate.io/docs/crate/reference/sql/reference/create_table.html#partitioned-by-clause
.. _Alter a partitioned table: https://crate.io/docs/crate/reference/sql/partitioned_tables.html#alter
.. _Import/Export: https://crate.io/docs/crate/reference/sql/dml.html#import-export
