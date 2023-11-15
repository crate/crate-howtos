.. _config_tuning:

================================
Configuration tuning for inserts
================================

This document outlines a number of hardware and software configuration changes
you can make to tune your setup for inserts performance.

.. rubric:: Table of contents

.. contents::
   :local:

Hardware
========

Solid-state drives
------------------

Switch to `Solid-State Drives`_ (SSDs) if you can.

SSDs are generally much faster than hard-disk drives, and usually offer the
most cost-effective hardware upgrade for a CrateDB setup.

Use the ``iostat`` tool to display disk I/O statistics, which should include
output like this:

.. code-block:: text

    sh$ iostat
    ...
    avg-cpu:  %user   %nice %system %iowait  %steal   %idle
               0.53    0.01    0.05    0.01    0.00   99.41
    ...

Here, the most interesting metric is ``%iowait``. This tells you how
time the CPU is waiting for disk I/O. You can expect better insert performance
from CrateDB relative to how low this value is.

CPUs
----

If your table schemas are complex or make use of `fulltext indexes`_, the
additional CPU overhead during the analyzing phase of insert query processing
might result in a CPU performance bottleneck.

If this becomes the case, you might want to try using different fulltext
analyzers or maybe even turn off fulltext indexing entirely. If neither of
these are an option, upgrading your CPUs will be a cost-effective way to boost
CrateDB performance.

Software
========

Replicas
--------

The biggest performance cost occurred when you go from zero replicas to one
configured replica for a table. After that point, load increases linearly. This
is because a write is made to the primary first, and then afterwards, writes
are made concurrently to the replicas.

However, using tables with zero replicas is not recommended for anything except
one-off data imports. You should have at least one configured replica for every
table in a cluster that has three nodes or more.

Replicas improve availability and durability (in the event of node failure or
cluster partitions) but they do incur a performance cost.

Shards and partitioning
-----------------------

The :ref:`sharding guide <sharding_guide>` has a section that covers
:ref:`ingestion performance <sharding_ingestion>`.

Indexing
--------

By default, all table columns are indexed. Regular columns use the ``plain``
index, and fulltext columns use the ``fulltext`` index.

Indexes are expensive, so `turning column indexes off`_ will always improve
performance. Sometimes significantly. But the downside is that you cannot use
those columns in the where clause.

Primary keys
------------

If your data does not have a `natural primary key`_ (i.e. data that uniquely
identifies each row), use the ``_id`` `system column`_ as a primary key. This
is better than creating your own `surrogate primary key`_ (e.g. manually
generating a UUID for each row) because there is one less column to index.

Translog
--------

If `translog.durability`_ is set to ``REQUEST`` (the default), the translog
gets flushed after every operation. Setting this to ``ASYNC`` will improve
insert performance, but it also worsens durability. If a node crashes before a
translog has been synced, those opperations will be lost.

Overload Protection
-------------------

The `Overload Protection`_ settings control how many resources operations like 
``INSERT INTO FROM QUERY`` or ``COPY`` can use.

The default values serve as a starting point for an algorithm that dynamically 
adapts the effective concurrency limit based on the round-trip time of requests. 
Whenever one of these settings is updated, the previously calculated effective 
concurrency is reset.

Please update the settings accordingly, especially if you are benchmarking insert
performance.

Refresh interval
----------------

With the exception of primary key lookups, data that has been written to a
shard cannot be read back until the shard index has been refreshed.

The `refresh_interval`_ table setting specifies how frequently shard indexes
are refreshed. The default value is every 1000 milliseconds.

If you know that your client application can tollerate a higher refresh
interval, you can expect to see performance improvements if you increase this
value.

Calculating statistics
----------------------

After loading larger amounts of data into new or existing tables, it is recommended
to re-calculate the statistics by executing the ``ANALYZE`` command. 
The statistics will be used by the query optimizer to generate better execution plans. 

The calculation of statistics happens periodically. The bandwidth used for collecting statistics
is limited by applying throttling based on the maximum amount of bytes per second that can
be read from data nodes.

Please refer to the `ANALYZE`_ documentation for further information how to change the
calculation interval, and how to configure throttling settings.

Manual optimizing
-----------------

CrateDB uses an append-only strategy for writing data to the disk. Tables are
written to disk as a collection of segment files. As tables grow, so does the
number of underlying segments.

CrateDB can optimize tables by merging segments and discarding
data that is no longer used. This process is occasionally triggered by CrateDB,
and under normal circumstances, you do not have to worry about optimizing
tables yourself.

However, if you are doing a lot of inserts, you may want to optimize tables (or
even specific partitions) on your own schedule. If so, you can use the
`OPTIMIZE`_ command.

.. _fulltext indexes: https://crate.io/docs/crate/reference/en/latest/sql/fulltext.html
.. _natural primary key: https://en.wikipedia.org/wiki/Natural_key
.. _OPTIMIZE: https://crate.io/docs/crate/reference/en/latest/sql/reference/optimize.html
.. _ANALYZE: https://cratedb.com/docs/crate/reference/en/latest/sql/statements/analyze.html
.. _refresh_interval: https://crate.io/docs/crate/reference/en/latest/sql/reference/create_table.html#refresh-interval
.. _Solid-State Drives: https://en.wikipedia.org/wiki/Solid-state_drive
.. _surrogate primary key: https://en.wikipedia.org/wiki/Surrogate_key
.. _system column: https://crate.io/docs/crate/reference/en/latest/sql/administration/system_columns.html
.. _translog.durability: https://crate.io/docs/crate/reference/en/latest/sql/reference/create_table.html#translog-durability
.. _turning column indexes off: https://crate.io/docs/crate/reference/en/latest/sql/ddl/indices_full_search.html#disable-indexing
.. _Overload Protection: https://cratedb.com/docs/crate/reference/en/latest/config/cluster.html#overload-protection
