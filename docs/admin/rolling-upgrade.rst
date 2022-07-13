.. highlight:: sh
.. _rolling_upgrade:

===============
Rolling upgrade
===============

.. rubric:: Table of contents

.. contents::
   :local:

Introduction
============

CrateDB provides an easy way to perform a rolling cluster upgrade with zero
downtime.

A rolling upgrade is possible from one version to the next feature version.
Some examples:

- You can do a rolling upgrade from 4.5.x to 4.6.0
- You can do a rolling upgrade from 4.8.x to 5.0.0
  (because 4.8 is the last feature release within the 4. series).
- You cannot do a rolling upgrade from x.y.z to x.(y + 3).z unless
  the release notes explicitly mention support.

.. WARNING::

    Rolling upgrades are only possible if you are using a stable version of
    CrateDB. If you are upgrading to a testing version you must perform a full
    cluster restart.

    Check the `release notes`_ for the version you are upgrading to for any
    specific instructions that may override this.

To perform a rolling upgrade of a cluster, one node at a time has to be stopped
using the graceful stop procedure (see `Signal Handling`_).

This procedure will disable a node, which will cause it to reject any new
requests but will make sure that any pending requests are finished.

.. NOTE::

   Due to the distributed execution of requests, some client requests might
   fail during a rolling upgrade.

This process will ensure a certain data availability. Which can either be
``none``, ``primaries``, or ``full`` and can be configured using `SET`_.

Using ``full``, all shards currently located on the node will be moved to the
other nodes in order to stop gracefully. Using this setting the cluster will
stay ``green`` the whole time.

Using ``primaries``, only the primaries will be moved to other nodes. Using
this setting means that the cluster will go into the ``yellow`` warning state
if a node that has been stopped contained replicas that are then unavailable.

Using ``none``, there is no data-availability guarantee. The node will stop,
possibly leaving the cluster in the critical ``red`` state if the node
contained a primary that has no replicas that can take over.


Requirements
============

Full minimum data availability
------------------------------

If the ``full`` minimum data availability is configured the cluster needs to
contain enough nodes to hold the number of replicas that are configured even if
one node is missing.

For example if there are only two nodes in a cluster and a table has one
replica configured the ``graceful stop`` procedure will not succeed and abort
as it won't be possible to relocate the replicas.

If a table has a range configured as number of replicas this will take into
account the upper number of replicas.

With two nodes and 0-1 replicas, the ``graceful stop`` procedure will
abort.

In short: for the ``full`` graceful stop to work the following has to be true::

    number_of_nodes > max_number_of_replicas + 1

Primaries minimum data availability
-----------------------------------

If the ``primaries`` minimum data availability is used, take care that there
are still enough replicas in the cluster after a node has been stopped so that
a write-consistency can be guaranteed.

By default write or delete operations only succeed if a quorum (> replicas / 2
+ 1) of active shards is available.

.. NOTE::

    If only 1 replica is configured one active shard suffices in order for
    write and delete operations to succeed.

Upgrade Process
===============

.. WARNING::

    Before upgrading, you should `back up your data`_.

Step 1: Disable allocations
---------------------------

First, you have to prevent the cluster from re-distributing shards and replicas
while certain nodes are not available. You can do that by disabling
re-allocations and only allowing new primary allocations.

Use the `SET`_ command to do so:

.. code-block:: psql

  cr> SET GLOBAL TRANSIENT "cluster.routing.allocation.enable" = 'new_primaries';
  SET OK, 1 row affected (... sec)

.. NOTE::

  This step may be omited if you set the
  ``cluster.graceful_stop.min_availability`` setting to ``full``.

Step 2: Graceful stop
---------------------

To initiate a graceful shutdown that behaves as described in the introduction
of this document, the `Decommission Statement`_ must be used.

Stopping a node via the ``TERM`` user signal (Often invoked via ``Ctrl+C`` or
``systemctl stop crate``), will cause a normal shutdown of CrateDB, **without**
going through the graceful shutdown procedure described earlier.

Depending on the size of your cluster, stopping a ``crate`` node gracefully
might take a while. You might want to check your server logs to see if the
graceful stop process is progressing well. In case of an error or a timeout,
the node will stay up, signaling the error in its log files (or wherever you
put your log messages).

Using the default settings the node will shut down by moving all primary shards
off the node first. This will ensure that no data is lost. However, the cluster
health will most likely turn yellow, because replicas that lived on that node
will be missing.

If you want to ensure green health, you need to change the
``cluster.graceful_stop.min_availability`` setting to ``full``. This will move
all shards off the node before shutting down.

Keep in mind that reallocating shards might take some time depending on the
number of shards and the amount and size of records (and/or blob data). For
that reason you should set the ``timeout`` setting to a reasonable time. By
default the shutdown process aborts and the cluster will start distributing
shards evenly again. If you want to force a shutdown after the timeout, even if
the reallocating is not finished, you can set the ``force`` setting to
``true``.

.. WARNING::

  A forced stop does not ensure the minimum data availability defined in the
  settings and may result in temporary or even permanent loss of data!

.. NOTE::

  When using ``cluster.graceful_stop.min_availability=full`` there have to be
  enough nodes in the cluster to move shards or else the graceful shutdown
  procedure will fail!

  For example, if there are 4 nodes and 3 configured replicas, there will not
  be enough nodes to to fulfill the required replicas.

  Also, if there is not enough disk space on other nodes to move the shards to
  the graceful stop procedure will fail.

By default, only the ``graceful stop`` command considers the cluster settings
described at `Graceful Stop`_.

Observing the reallocation
..........................

If you want to observe the reallocation process triggered by a ``full`` or
``primaries`` graceful-stop, you can issue the following sql queries regularly.

Get the number of shards remaining on your deallocating node:

.. code-block:: psql

  cr> SELECT count(*) as remaining_shards from sys.shards
  ... where _node['name'] = 'your_node_name';
  +------------------+
  | remaining_shards |
  +------------------+
  |                0 |
  +------------------+
  SELECT 1 row in set (... sec)

Get some more details about what shards are remaining on your node:

.. code-block:: psql

  cr> SELECT schema_name as schema, table_name as "table", id, "primary", state
  ... FROM sys.shards
  ... WHERE _node['name'] = 'your_node_name' AND schema_name IN ('blob', 'doc')
  ... ORDER BY schema, "table", id, "primary", state;
  +--------+-------+----+---------+-------+
  | schema | table | id | primary | state |
  +--------+-------+----+---------+-------+
  ...
  SELECT ... rows in set (... sec)

In the case of ``primaries`` availability, only the primary shards of tables
with zero replicas will be reallocated. Use this query to find out which shards
to look for:

.. code-block:: psql

   cr> SELECT table_schema as schema, table_name as "table"
   ... FROM information_schema.tables
   ... WHERE number_of_replicas = 0 and table_schema in ('blob', 'doc')
   ... ORDER BY schema, "table" ;
   +--------+-------...+
   | schema | table ...|
   +--------+-------...+
   ...
   +--------+-------...+
   SELECT ... rows in set (... sec)

.. NOTE::

   If you observe the graceful-stop process using the admin UI, you might see
   the cluster turning red for a small instant when a node finally shuts down.
   This is due to the way the admin UI determines the cluster state.

   If a query fails due to a missing node, the admin UI may falsely consider
   the cluster to be in a critical state.

Step 3: Upgrade CrateDB
-----------------------

After the node is stopped you can safely upgrade your CrateDB installation.
Depending on your installation and operating system you can do it by
downloading the latest tarball or just use the package manager.

Example for RHEL/YUM::

  $sh yum update -y crate

If you are in doubt how to upgrade an installed package, please refer to the
man pages of your operating system or package manager.

Step 4: Start CrateDB
---------------------

Once the upgrade process is completed you can start the CrateDB process again
by either invoking the bin/crate executable from the tarball directly::

  sh$ /path/to/bin/crate

Or using the service manager of your operating system.

Example for RHEL/YUM::

  sh$ service crate start

Step 5: Repeat
--------------

Repeat step two, three, and four for all other nodes.

Step 6: Enable allocations
--------------------------

Finally, when all nodes are updated you can re-enable allocations
again that have been disabled in the first step:

.. code-block:: psql

  cr> SET GLOBAL TRANSIENT "cluster.routing.allocation.enable" = 'all';
  SET OK, 1 row affected (... sec)


.. _back up your data: https://crate.io/docs/crate/reference/en/latest/admin/snapshots.html
.. _versions: https://crate.io/docs/crate/reference/en/latest/sql/system.html#version
.. _release notes: https://crate.io/docs/crate/reference/en/latest/appendices/release-notes/index.html
.. _Signal Handling: https://crate.io/docs/crate/reference/en/latest/cli-tools.html#signal-handling
.. _SET: https://crate.io/docs/crate/reference/en/latest/sql/statements/set.html
.. _Graceful Stop: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#graceful-stop
.. _Decommission Statement: https://crate.io/docs/crate/reference/en/latest/sql/statements/alter-cluster.html#decommission-nodeid-nodename
