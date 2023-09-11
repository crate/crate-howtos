.. _sharding-partitioning:

===============================
About Sharding and Partitioning
===============================

.. rubric:: Table of contents

.. contents::
   :local:


Introduction
============
Sharding and partitioning are techniques used to distribute data evenly across
multiple nodes in a cluster, ensuring data scalability, availability, and performance.
This page provides an in-depth guide on how to configure sharding and partitioning in
CrateDB, presenting best practices and examples.

Sharding
========

One core concept CrateDB uses to distribute data across the cluster is 
:ref:`sharding <crate-reference:ddl-sharding>`. CrateDB splits every table into a
configured number of shards, which are distributed evenly across the cluster. 
You can think of shards as a self-contained part of a table, that includes both 
a subset of records and the corresponding indexing structures. If we 
:ref:`create a table <crate-reference:ddl-create-table>` like the following:

.. code-block:: psql

    CREATE TABLE first_table (
        ts TIMESTAMP,
        val DOUBLE PRECISION
    );

The table is by default split into several shards on a single node cluster. 
You can check this by running:

.. code-block:: psql

    SHOW CREATE TABLE first_table;

Which should output the following:

.. code-block:: psql

    CREATE TABLE IF NOT EXISTS "doc"."first_table" (
        "ts" TIMESTAMP WITH TIME ZONE,
        "val" DOUBLE PRECISION
    )
    CLUSTERED INTO 4 SHARDS

By default, ingested data is distributed evenly across all available shards. 
Although you can influence that distribution by specifying a routing column, in 
many cases it is best to keep the default settings to avoid any unbalanced distribution.

Partitioning
============

CrateDB also supports splitting up data across another dimension with 
:ref:`partitioning <crate-reference:partitioned-tables>`. You can think of a
partition as a set of shards. For each partition, the number of shards defined 
by ``CLUSTERED INTO x SHARDS`` are created, when a first record with a specific 
``partition key`` is inserted.

In the following example - which represents a very simple time-series use-case 
- we added another column ``part`` that automatically generates the current 
month upon insertion from the ``ts`` column. The ``part`` column is further used 
as the ``partition key``.

.. code-block:: psql

    CREATE TABLE second_table (
        ts TIMESTAMP,
        val DOUBLE PRECISION,
        part GENERATED ALWAYS AS date_trunc('month',ts)
    ) PARTITIONED BY(part);

When inserting a record with the following statement:

.. code-block:: psql

    INSERT INTO second_table (ts,val) VALUES (1617823229974, 1.23);

and then querying for the total amount of shards for the table:

.. code-block:: psql

    SELECT COUNT(*) FROM sys.shards
    WHERE table_name = 'second_table';

We can see that the table is split into 4 shards.

Adding another record to the table with a different partition key (i.e. different 
month):

.. code-block:: psql

    INSERT INTO second_table (ts,val) VALUES (1620415701974, 2.31);

We can see that there are now 8 shards for the table ``second_table`` in the 
cluster.

.. danger::

    **Over-sharding and over-partitioning**

    Sharding can drastically improve the performance on large datasets. 
    However, having too many small shards will most likely degrade performance. 
    Over-sharding and over-partitioning are common flaws leading to an overall 
    poor performance.

    **As a rule of thumb, a single shard should hold somewhere between 5 - 100 
    GB of data.**

    To avoid oversharding, CrateDB by default limits the number of shards per 
    node to 1000. Any operation that would exceed that limit, leads to an 
    exception.

How to choose your sharding and partitioning strategy
=====================================================
An optimal sharding and partitioning strategy always depends on the specific 
use case and should typically be determined by conducting 
benchmarks across various strategies. The following steps provide a general guide for a benchmark.

- Identify the ingestion rate
- Identify the record size
- Calculate the Throughput

Then, to calculate the number of shards, you should consider that the size of each
shard should roughly be between 5 - 100 GB, and that each node can only manage
up to 1000 shards.

Time-series example
-------------------

To illustrate the steps above, let's use them on behalf of an example. Imagine
you want to create a *partitioned table* on a *three-node cluster* to store
time-series data with the following assumptions:

- Inserts: 1.000 records / s
- Record size: 128 byte / record
- Throughput: 125 KB / s or 10.3 GB / day

Given the daily throughput is around 10 GB/day, the monthly throughput is 30 times
that (~ 300 GB). The partition column can be day, week, month, quarter, etc. So,
assuming a monthly partition, the next step is to calculate the number of shards
with the **shard size restriction** (5 - 100 GB) and the **number of nodes** in
the cluster in mind.

With three shards, each shard will hold 100 GB (300 GB / 3), which is too
close to the upper limit. With six shards, each shard will manage 50 GB
(300 GB / 6) of data, which is closer to the recommended size range (5 - 100 GB).

.. code-block:: psql

    CREATE TABLE timeseries_table (
        ts TIMESTAMP,
        val DOUBLE PRECISION,
        part GENERATED ALWAYS AS date_trunc('month',ts)
    ) CLUSTERED INTO 6 SHARDS 
    PARTITIONED BY(part);

Assuming a weekly partition for the same example (7 × 10 GB / day = 70 GB / week),
three shards per partition would work well resulting in ~24 GB per shard.

Above, we demonstrated how both monthly partitioning with 6 shards, and weekly
partitioning with 3 shards work for the use case. In general, you should also
consider to evaluate the query patterns of your use case, in order to find a
good partitioning interval matching the characteristics of your data.





