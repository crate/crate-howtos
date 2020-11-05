.. _multi-zone-setup:

========================
CrateDB multi-zone setup
========================

If possible, we recommend running all CrateDB nodes of a cluster inside the
same physical space to minimize network latency and maximize speed between the
nodes. These factors can have a significant impact on the performance of
CrateDB clusters. This is especially true when running clusters in multiple
regions.

This is because replicas are written *synchronously* and making a `write
operation`_ wait for all the replicas to write somewhere in a data center
hundreds of miles away can lead to noticeable latency and cause the cluster to
slow down.

In some cases, it may be necessary to run a cluster across multiple data
centers or availability zones (*zones*, for short). This guide shows you how
to set up a multi-zone CrateDB cluster.

.. rubric:: Table of contents

.. contents::
   :local:


.. _multi-zone-requirements:

Multi-zone requirements
=======================

For a multi-zone setup, CrateDB clusters need to fulfill the following:

1. Data inserts should be replicated in a way where at least one full `replica`_
   is present in each zone.

2. All data still needs to be fully available if a zone becomes unavailable.

3. When querying data, all data should only be collected from shards that are
   inside the same zone as the initial request.

To achieve these requirements, make use of `shard allocation awareness`_, which
allows you to configure `shard`_ and replica allocation. If you are new to setting
up a multi-node CrateDB cluster, you should read our :ref:`multi-node setup
<multi_node_setup>` guide first.


.. _tag-assignments:

Tag assignments
===============

Once you have fulfilled the :ref:`multi-zone requirements
<multi-zone-requirements>`, assign a tag containing the name of the zone to
the cluster nodes. This enables `shard allocation awareness`_.

You can assign arbitrary tags to nodes in your `configuration`_ file with
`node custom attributes`_ or via the ``-C`` option at startup.

.. SEEALSO::

    Read our in-depth `configuration guide`_ for more details on CrateDB
    configuration options.

For example, you can assign a zone tag in your `configuration`_ file like this:

.. code-block:: yaml

    node.attr.zone: us-east-1

The ``node.attr`` namespace is given a ``zone`` key and tagged with a
``us-east-1`` value, which is an availability zone of a cloud computing
provider.

Alternatively, you can configure this at startup with a command-line option.
For example:

.. code-block:: console

    sh$ bin/crate \
            -Cnode.attr.zone=us-east-1

.. NOTE::

   These tags and settings cannot be changed at runtime and need to be
   set on startup.


.. _allocation-awareness:

Allocation awareness
====================

Once you have assigned zone tags, they can be set as attributes for `shard
allocation awareness`_ with the
``cluster.routing.allocation.awareness.attributes`` setting.

For example, use the ``zone`` tag that you just assigned to your node as an
attribute in your `configuration`_ file, like this:

.. code-block:: yaml

    cluster.routing.allocation.awareness.attributes: zone

This means that CrateDB will try to allocate `shards`_ and their `replicas`_
according to the ``zone`` tags, so that a shard and its replica are not on a
node with the same ``zone`` value.

Add a second and a third node in a different zone (``us-west-1``) and tag
them accordingly:

.. code-block:: yaml

    node.attr.zone: us-west-1
    cluster.routing.allocation.awareness.attributes: zone

Now start your cluster and then `create a table`_ with 6 shards and 1 replica.

As an example, you can create such a table by executing a statement like this
in the `CrateDB Shell`_:

.. code-block:: sql

    cr> CREATE TABLE my_table (
          first_column INTEGER,
          second_column TEXT
        ) CLUSTERED INTO 6 SHARDS
        WITH (number_of_replicas = 1);

The 6 shards will be distributed evenly across the nodes (2 shards on
each node) and the replicas will be allocated on nodes with a different
``zone`` value than its primary shard.

If this is not possible (i.e. ``num replicas > num zones - 1``), CrateDB will
still allocate the replicas on nodes with the same ``zone`` value to avoid
`unassigned shards`_.

.. NOTE::

   Allocation awareness only means that CrateDB *tries* to conform to the
   awareness attributes. To avoid such allocations, you can :ref:`force the
   awareness <force-awareness>`.


.. _force-awareness:

Force awareness
===============

To fulfill the third :ref:`multi-zone requirement <multi-zone-requirements>`,
you need to ensure that when running a query on a node with a certain ``zone``
value, it only executes the request on `shards`_ allocated on nodes with the same
``zone`` value.

This means you need to know the different ``zone`` attribute values to force
awareness on nodes.

You can force `awareness`_ on certain attributes with the
``cluster.routing.allocation.awareness.force.*.values`` setting, where ``*``
is a placeholder for the awareness attribute, which can be defined using the
``cluster.routing.allocation.awareness.attributes`` setting.

For example, to force awareness on the pre-configured ``zone`` attribute for
the ``us-east-1`` and ``us-west-1`` values, you can put the following in your
`configuration`_ file:

.. code-block:: yaml

    cluster.routing.allocation.awareness.force.zone.values: us-east-1,us-west-1

This means that no more `replicas`_ than needed are allocated on a specific group of
nodes.

.. TIP::

   If you have 2 nodes with the ``zone`` attribute set to ``us-east-1`` and you
   `create a table`_ with 8 shards and 1 replica, 8 primary shards will be allocated
   and the 8 replica shards will be left unassigned. Only when you add a new node
   with the ``zone`` attribute set to ``us-west-1`` will the replica shards be
   allocated.

By using these settings correctly and understanding the concepts behind them,
you should be able to set up a functioning cluster that spans across multiple
zones and regions. However, be aware of the drawbacks that a multi-region
setup can have. These include latency and also security issues between
non-encrypted node-to-node traffic if the traffic escapes a "trusted" network.


.. _awareness: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#awareness
.. _configuration guide: https://crate.io/docs/reference/configuration.html
.. _configuration: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _CrateDB Shell: https://crate.io/docs/crate/crash/en/latest/
.. _create a table: https://crate.io/docs/crate/reference/en/latest/general/ddl/create-table.html
.. _node custom attributes: https://crate.io/docs/crate/reference/en/latest/config/node.html#custom-attributes
.. _replica: https://crate.io/docs/crate/reference/en/latest/general/ddl/replication.html
.. _replicas: https://crate.io/docs/crate/reference/en/latest/general/ddl/replication.html
.. _shard allocation awareness: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#awareness
.. _shard: https://crate.io/docs/crate/reference/en/latest/general/ddl/sharding.html
.. _shards: https://crate.io/docs/crate/reference/en/latest/general/ddl/sharding.html
.. _unassigned shards: https://crate.io/docs/crate/howtos/en/latest/performance/sharding.html#under-allocation-is-bad
.. _write operation: https://crate.io/docs/crate/reference/en/latest/concepts/storage-consistency.html#data-storage
