.. highlight:: psql

.. _bulk-inserts:

============
Bulk inserts
============

If you have a lot of pre-existing data that you need to import in bulk, follow
this how-to guide if you want to improve performance.

Briefly, when importing data in bulk, keep the following in mind:

- Reduce the number of replicas as much as possible (ideally zero) as
  replication slows down the import process significantly

- Only use as many shards as you need

- Disable the periodic table refresh by setting the refresh interval to zero
  during import

- Adjust the bulk size of the import as necessary given the number of records
  you are importing

- Import table partitions separately using the ``PARTITION`` clause in the
  ``COPY TO`` statement

The rest of this document goes into more detail.

.. TIP::

    Increasing disk `IOPS`_ is the best, and perhaps most straightforward, way
    to increase import speed. SSDs are recommended (as general good practice)
    for this reason.

    Another way to increase import speed is to add more disks by adding more
    nodes. CrateDB is a `distributed database`_, and so, increasing overall
    cluster size is generally a good way to improve performance.

.. rubric:: Table of contents

.. contents::
    :local:

.. SEEALSO::

    :ref:`Insert performance: Methods <insert-methods>`

    :ref:`Best practices: Migrating from MySQL <migrating-mysql>`

    :ref:`Best practices: Migrating from MongoDB <migrating-mongodb>`

    `CrateDB Reference: Import and export`_


.. _bulk-configure-tables:

Configure your tables
=====================


.. _bulk-data-structure:

Data structure
--------------

Before starting the import, you need to carefully define your table structure
in CrateDB. Decisions made at this point will influence the import process
later.

For this example, say you have a single ``users`` table with six columns of
various types. You can create this table with the following statement::

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


.. _bulk-shards-replicas:

Shards and replicas
-------------------

For each table, if you do not set the number of `shards`_ or the number of
`replicas`_, the default configuration is as follows:

**Shards**
    Dependent on the number of data-nodes in the cluster (see `CLUSTERED
    clause`_)

**Replicas**
    One

You should choose the number of shards wisely. The choice depends on the number
of nodes in the cluster as well as on the amount of data that is going into the
table.

Assuming there are six nodes in the cluster, you can put two shards on each
node, giving you a total of 12 shards. This should be enough to handle millions
of records.

Shards can be thought of as "virtual nodes." You should create enough for your
scaling needs, but use as few as possible to keep the resource overhead (e.g.,
file descriptors and memory) as small as possible.

When importing data, you should set the number of replicas to a minimum,
ideally zero. If the import fails, you can `drop`_ the table and import
again. When the import succeeds, adjust the number of replicas according to
your `availability`_ requirements.

For example, the ``CREATE TABLE`` statement we used before could be changed
to the following::

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


.. _bulk-refresh-interval:

Refresh interval
----------------

Another way to speed up importing is to set the `refresh_interval`_ of the
table to zero::

    cr> ALTER TABLE users SET (refresh_interval = 0);
    ALTER OK, -1 rows affected (... sec)

This will disable the periodic `refresh`_ of the table which will, in turn,
will minimize processing overhead during import.

.. HIDE:

    cr> DROP TABLE users;
    DROP OK, 1 row affected (... sec)

You can also set the refresh interval when initially creating the table, like
so::

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

When the import has finished, you can set the refresh interval back to a
reasonable value (milliseconds)::

    cr> ALTER TABLE users SET (refresh_interval = 1000);
    ALTER OK, -1 rows affected (... sec)


.. _bulk-import-data:

Import the data
===============

Once the table is created, you can start importing the data.

When importing, CrateDB has `native support for JSON data`_. Specifically, for
bulk inserts, you can use a format called `JSON Lines`_. In a JSON Lines file,
each line is a JSON string representing a single record. Empty lines are
skipped. The keys of the JSON objects are mapped to columns when
imported. Nonexistent columns will be created if necessary.

For example, a JSON Lines file might look like this:

.. code-block:: json

    {"id": 1, "name": "foo", "day_joined": 1408312800, "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Dornbirn", "country": "Austria"}}
    {"id": 2, "name": "bar", "day_joined": 1408312800, "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Berlin", "country": "Germany"}}


Use the `COPY FROM`_ statement to import JSON data directly from a file::

    cr> COPY users FROM '/tmp/best_practice_data/users.jsonl';
    COPY OK, 150 rows affected (... sec)

Here, CrateDB will check ``/tmp/best_practices_data/`` locally on each node in
the cluster to import data from a file called ``users.jsonl``.

.. HIDE:

    cr> REFRESH TABLE users;
    REFRESH OK, 1 row affected (... sec)

    cr> delete from users;
    DELETE OK, 150 rows affected (... sec)

    cr> REFRESH TABLE users;
    REFRESH OK, 1 row affected (... sec)

.. TIP::

    If you are using Microsoft Windows, you must include the drive letter in
    the filename.

    For example, the above filename should instead be written as
    ``C://tmp/best_practice_data/users.jsonl``.

    Consult the `Windows documentation`_ for more information.

.. CAUTION::

    If the specified file is not found, CrateDB will still return a successful
    status, for example::

        COPY OK, 0 rows affected (... sec)

    Additionally, when importing data using ``COPY FROM``, CrateDB does not
    check whether both the types from the columns and the types from the import
    file match. CrateDB does not `cast`_ the imported data types to the the
    target column type. Instead, CrateDB will import the data *as given* in the
    source file.


.. _bulk-bulk-size:

Bulk size
---------

You can improve on the example above by configuring the `bulk_size`_
option, like so::

    cr> COPY users FROM '/tmp/best_practice_data/users.jsonl'
    ... WITH (bulk_size = 2000);
    COPY OK, 150 rows affected (... sec)

The ``bulk_size`` option specifies the amount of lines that are read at once
while importing. This option defaults to ``10000``.

.. HIDE:

    cr> REFRESH TABLE users;
    REFRESH OK, 1 row affected (... sec)

    cr> delete from users;
    DELETE OK, 150 rows affected (... sec)

    cr> REFRESH TABLE users;
    REFRESH OK, 1 row affected (... sec)

.. TIP::

    In our example use-case, configuring ``bulk_size`` will not make any
    practical difference.

    However, if you have a more complex dataset with a lot of columns and large
    values, it makes sense to decrease the ``bulk_size``.

    A ``bulk_size`` setting that is too high might consume a lot of node
    resources. A low ``bulk_size`` can increase the overhead resource
    utilization per request.


.. _bulk-compression:

Compression
-----------

We recommend that you use `gzip`_ to compress your JSON files.

However, CrateDB does not automatically detect file compression, so you will
need to specify ``gzip`` compression, like so::

    cr> COPY users FROM '/tmp/best_practice_data/users.jsonl.gz'
    ... WITH (compression = 'gzip');
    COPY OK, 150 rows affected (... sec)

.. HIDE:

    cr> REFRESH TABLE users;
    REFRESH OK, 1 row affected (... sec)


.. _bulk-split-partitions:

Split your tables into partitions
=================================

You can split your table into `partitions`_ to improve performance.

.. HIDE:

    cr> DROP TABLE users;
    DROP OK, 1 row affected (... sec)

Partitions can be created using the ``CREATE TABLE`` statement and a
``PARTITIONED BY`` clause to specify a partition column. For example::

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

.. NOTE::

    If a `primary key`_ was explicitly declared, the partition column has to be a
    component of the primary key.

A value identifying the target partition column *should* be defined in the
``COPY FROM`` statement using the ``PARTITION`` clause::

    cr> COPY users PARTITION (day_joined=1408312800)
    ... FROM '/tmp/best_practice_data/users_1408312800.jsonl';
    COPY OK, 23 rows affected (... sec)

When you use the ``PARTITION`` clause, CrateDB doesn't need to resolve the
partition for each row that is imported, which aids performance.

The corresponding JSON Lines file might look like this:

.. code-block:: json

    {"id": 1, "name": "foo", "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Dornbirn", "country": "Austria"}}
    {"id": 2, "name": "bar", "bio": "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.", "address": {"city": "Berlin", "country": "Germany"}}

Here, notice the partition column itself (``day_joined``) has been excluded
from the JSON. You must omit this column if you use the ``PARTITIONED`` clause.

.. CAUTION::

    You *can* import data into partitioned tables without using the
    ``PARTITION`` clause, as long as you *do* specify the column value in the
    source file. However, we do not recommend this method, as doing so may
    degrade performance.

.. SEEALSO::

    `CrateDB Reference: Partitioned tables`_

    `CrateDB Reference: PARTITIONED BY`_

    `CrateDB Reference: Alter a partitioned table`_


.. _bulk-disable-refresh-new-shards:

Disable table refresh for new shards
------------------------------------

When importing data into a table that already has partitions, you can optimize
the insert operation for newly created shards by disabling the
`refresh_interval`_ for those partitions (only) using the `ALTER TABLE ONLY`_
statement.

.. SEEALSO::

    :ref:`Bulk inserts: Shards and replicas <bulk-shards-replicas>`


.. _bulk-increase-shards:

Increase the number of shards
-----------------------------

The ``ALTER TABLE`` clause can also be used to `alter the number of shards`_
for newly created partitions, which may improve performance over the previous
configuration when handling a lot more data than before.

For exmaple::

   ALTER TABLE users SET (number_of_shards=12)

.. CAUTION::

    Configuring too many shards may degrade performance. See the :ref:`prior
    section about shards <bulk-shards-replicas>` for more information.


.. _ALTER TABLE ONLY: https://crate.io/docs/crate/reference/en/latest/sql/partitioned_tables.html#alter-table-only
.. _alter the number of shards: https://crate.io/docs/crate/reference/en/latest/general/ddl/partitioned-tables.html#changing-the-number-of-shards
.. _availability: https://en.wikipedia.org/wiki/High_availability
.. _bulk_size: https://crate.io/docs/crate/reference/en/master/sql/statements/copy-from.html#bulk-size
.. _cast: https://crate.io/docs/crate/reference/en/4.4/general/ddl/data-types.html#cast
.. _CLUSTERED clause: https://crate.io/docs/crate/reference/en/latest/sql/statements/create-table.html#clustered
.. _COPY FROM: https://crate.io/docs/crate/reference/en/latest/sql/reference/copy_from.html
.. _CrateDB Reference\: Alter a partitioned table: https://crate.io/docs/crate/reference/en/latest/sql/partitioned_tables.html#alter
.. _CrateDB Reference\: Import and export: https://crate.io/docs/crate/reference/en/latest/general/dml.html#import-and-export
.. _CrateDB Reference\: PARTITIONED BY: https://crate.io/docs/crate/reference/en/latest/sql/statements/create-table.html#partitioned-by
.. _CrateDB Reference\: Partitioned tables: https://crate.io/docs/crate/reference/en/latest/sql/partitioned_tables.html
.. _distributed database: https://crate.io/docs/crate/reference/en/latest/concepts/clustering.html
.. _drop: https://crate.io/docs/crate/reference/en/4.4/sql/statements/drop-table.html
.. _gzip: https://www.gnu.org/software/gzip/
.. _IOPS: https://en.wikipedia.org/wiki/IOPS
.. _JSON lines: https://jsonlines.org/
.. _native support for JSON data: https://crate.io/docs/crate/reference/en/master/general/ddl/data-types.html#json
.. _partitions: https://crate.io/docs/crate/reference/en/master/general/ddl/partitioned-tables.html
.. _primary key: https://crate.io/docs/crate/reference/en/master/general/ddl/constraints.html#primary-key
.. _refresh_interval: https://crate.io/docs/crate/reference/en/latest/sql/reference/create_table.html#refresh-interval
.. _refresh: https://crate.io/docs/crate/reference/en/latest/sql/refresh.html
.. _replicas: https://crate.io/docs/crate/reference/en/master/general/ddl/replication.html
.. _shards: https://crate.io/docs/crate/reference/en/master/general/ddl/sharding.html
.. _Windows documentation: https://docs.microsoft.com/en-us/dotnet/standard/io/file-path-formats
