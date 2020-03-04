.. _memory:

====================
Memory configuration
====================

CrateDB is a Java application running on top of a Java Virtual Machine (JVM).
For optimal performance you must configure the amount of memory that is
available to the JVM for **heap** allocations. The **heap** is a memory region
used for allocations of objects. For example, if you invoke a ``SELECT``
statement, parts of the result set are temporarily allocated in the **heap**.

The amount of memory that CrateDB can use for heap allocations is set using the
`CRATE_HEAP_SIZE`_ environment variable.

The right memory configuration depends on your workloads.

Consider the following when determining the right value:

- The JVM has automatic memory management and frees up memory using `Garbage
  Collection`_ (GC). CrateDB, as of version 4.1, defaults to use a garbage
  collection implementation called `G1GC`_. This implementation performs well
  for heap sizes ranging from several GB to ten or more. It tries to provide
  the best balance between latency and throughput. Still, the garbage
  collection times **increase** with a bigger heap, leading to **increased**
  latency. Therefore, your heap size shouldn't be too large.

- CrateDB needs to be able to hold all the structures required to process
  queries in memory. The biggest offender are intermediate or final result
  sets. Therefore, the heap region must be large enough to hold the biggest
  result sets in memory. The size of the intermediate and final result sets
  depend entirely on the type of queries you are running.

- CrateDB also uses `Memory mapped files`_ via `Lucene`_. This reduces the
  amount of heap space required and benefits from the file system cache.

A good starting point for the heap space is 25% of the systems memory. However,
it shouldn't be set above 30.5GB, see the limits section below.


.. rubric:: Table of contents

.. contents::
   :local:

.. _memory-limits:

Limits
======

30.5 gigabytes total
--------------------

On `x64 architectures`_, the `HotSpot Java Virtual Machine`_ (JVM) uses a
performance optimization technique called `Compressed Oops`_ that allows the
JVM to address up to 32 gigabytes of memory.

If you configure the heap to more than 32 gigabytes, this performance
optimization is disabled, and CrateDB will suffer performance degradation as a
result.

On some JVMs this value is as low as 30.5 gigabytes.

For this reason, you should never configure the CrateDB heap to more than 30.5
gigabytes.

.. TIP::

    When configuring heap size via `CRATE_HEAP_SIZE`_, you can specify 30.5
    gigabytes with the value ``30500m``.

If you are running CrateDB on a system with much more memory available, we
recommend that you run multiple CrateDB nodes.

In this instance, each CrateDB node should be configured with a heap size of
30.5 gigabytes. However, in total, you should still leave 50% of the system
memory for Lucene.

You should also add this to your node configurations:

.. code-block:: yaml

    cluster.routing.allocation.same_shard.host: true

This will prevent replica shards from being created on or moved to a CrateDB
node on the same host system as the primary shard.

.. _Compressed Oops: https://wiki.openjdk.java.net/display/HotSpot/CompressedOops
.. _configurations: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _CRATE_HEAP_SIZE: https://crate.io/docs/crate/reference/en/latest/config/environment.html#crate-heap-size
.. _HotSpot Java Virtual Machine: http://www.oracle.com/technetwork/java/javase/tech/index-jsp-136373.html
.. _Lucene: https://lucene.apache.org/
.. _x64 architectures: https://en.wikipedia.org/wiki/X86-64
.. _Garbage Collection: https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)
.. _G1GC: https://docs.oracle.com/javase/9/gctuning/garbage-first-garbage-collector.htm#JSGCT-GUID-0394E76A-1A8F-425E-A0D0-B48A3DC82B42
.. _Memory mapped files: https://en.wikipedia.org/wiki/Memory-mapped_file
