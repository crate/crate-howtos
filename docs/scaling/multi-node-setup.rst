.. _multi_node_setup:

========================
CrateDB multi-node setup
========================

CrateDB is a distributed datastore and so in production, a cluster will
typically consist of 3 or more nodes. CrateDB makes cluster setup as easy as
possible, but there are things to note when building a new cluster.

CrateDB is designed in a shared nothing architecture, in which all nodes are
equal and each node is self-sufficient. This means that nodes work on their
own, and all nodes in a cluster are configured equally, the same as with a
single-node instance.

.. rubric:: Table of contents

.. contents::
   :local:

Node settings
=============

Set node specific settings in the configuration file named *crate.yaml* shipped
with CrateDB.

Cluster name
------------

CrateDB nodes with the same cluster name will join the cluster. The simplest
way to prevent other nodes from joining a cluster is to give it a different and
unique name.

.. code-block:: yaml

    cluster.name: my_cluster

Node name
---------

To name a node:

.. code-block:: yaml

    node.name: node1

If the node name is omitted, then it's generated dynamically on startup.

.. _inter-node-comms:

Node Type
---------
A Node can have various roles in the cluster:

**Master-eligible node**

A node that has node.master set to true, which makes it eligible to
be elected as the master node, as part of the :ref:`master-node-election`.

**Data node**

A node that has node.data set to true. Data nodes hold soley data.

**Coordination-only node**

A node that has node.master set to false and node.data set to false is a coordination-only node,
which will neither hold data nor is eligible as master and its only purpose is coordination.

A node can have multiple roles at the same time. `More information on Node types
<https://crate.io/docs/crate/reference/en/latest/config/node.html#node-types>`_
can be found in CrateDB's reference guide.

Inter-node communication
========================

The default port CrateDB uses communicate between nodes is *4300*. CrateDB
calls it the *transport port* and it must be accessible from every node.

It's possible to change the port range bound to the transport service:

.. code-block:: sh

    transport.tcp.port: 4350-4360

Want to know more?
------------------

`More information on port settings
<https://crate.io/docs/reference/configuration.html#conf-ports>`_ can be found
in CrateDB's reference guide.

CrateDB binds to a second port, *4200*, that is only used for HTTP
communication. Clients connecting to the CrateDB cluster are using this HTTP
port, except the native Java client, which uses the transport port.

Node discovery
==============

The simplest way to do node discovery is to provide a list of expected hosts,
network IP addresses using the FQDN and transport port:

+-----------------+-----------+---------------------------------------+
| CrateDB Version | Reference | Configuration Example                 |
+=================+===========+=======================================+
| <=4.x           | `latest`_ | .. code-block:: yaml                  |
|                 |           |                                       |
|                 |           |     discovery.seed_hosts:             |
|                 |           |       - node1.example.com:4300        |
|                 |           |       - node2.example.com:4300        |
|                 |           |       - 10.0.1.102:4300               |
|                 |           |       - 10.0.1.103:4300               |
+-----------------+-----------+---------------------------------------+
| <=3.x           | `3.3`_    | .. code-block:: yaml                  |
|                 |           |                                       |
|                 |           |     discovery.zen.ping.unicast.hosts: |
|                 |           |       - node1.example.com:4300        |
|                 |           |       - node2.example.com:4300        |
|                 |           |       - 10.0.1.102:4300               |
|                 |           |       - 10.0.1.103:4300               |
+-----------------+-----------+---------------------------------------+

.. NOTE::

   When adding new nodes to the cluster, you do not need to update the list of
   hosts for existing/running nodes. The cluster will find and add new
   nodes when they ping existing ones.

Providing a list of expected hosts is just one node discovery mechanism.

CrateDB also supports node discovery via DNS as well as discovery via API for
clusters running on *Amazon Web Services* (AWS) or Microsoft Azure. See `the
documentation <https://crate.io/docs/reference/configuration.html#discovery>`_
for more information.

.. _master-node-election:

Master node election
====================

In a CrateDB cluster, the master node is responsible for making changes to the
global cluster state. The master node is elected as part of the `master node
election`_.

CrateDB requires a *quorum* of nodes in the cluster before a master can be
elected. This insures that multiple masters are not elected in the event of a
network partition (which would lead to a `split-brain`_ scenario).

.. _master-node-election-4x:

CrateDB versions 4.x and above
------------------------------

CrateDB will automatically determine the ideal quorum size. However, the
`cluster.initial_master_nodes`_ setting must be configured with a initial set
of master-eligible nodes.

.. TIP::

    In a three node cluster, all nodes must declared master-eligible.

To configure this setting, add something like this to your `configuration`_
file:

.. code-block:: yaml

    cluster.initial_master_nodes:
      - node1.example.com
      - 10.0.1.102
      - 10.0.1.103

.. _master-node-election-3x:

CrateDB versions 3.x and below
------------------------------

The quorum must be configured manually.

In a three node cluster, the quorum size
(`discovery.zen.minimum_master_nodes`_) must be at least two. This is explained
in the `quorum guide`_.

Configure a quorum of two, add this to your `configuration`_ file:

.. code-block:: yaml

    discovery.zen.minimum_master_nodes: 2

On an already running cluster, you set this using SQL:

.. code-block:: psql

    cr> SET GLOBAL PERSISTENT discovery.zen.minimum_master_nodes = 2;

Gateway configuration
=====================

The gateway persists cluster meta data on disk every time it changes. This data
is stored persistently across full cluster restarts and recovered after nodes
are restarted.

Three important settings control how the gateway recovers the cluster state:

``gateway.recover_after_nodes`` defines the number of nodes that need to be
started before any cluster state recovery will start. Ideally this value should
be equal to the number of nodes in the cluster, because you only want the
cluster state to be recovered once all nodes are started.

``gateway.recover_after_time`` defines the time to wait before starting the
recovery once the number of nodes defined in ``gateway.recover_after_nodes``
are started. This setting is only relevant if ``gateway.recover_after_nodes``
is less than ``gateway.expected_nodes``.

``gateway.expected_nodes`` defines how many nodes to wait for until the cluster
state is recovered. The value should be equal to the number of nodes in the
cluster, because you want the cluster state to be recovered after all nodes are
started.

These settings cannot be changed when a cluster is running. They need to be
set in the configuration file, e.g.:

.. code-block:: yaml

    gateway:
      recover_after_nodes: 3
      recover_after_time: 5m
      expected_nodes: 3

Or as command line options, ``-Cgateway.recover_after_nodes=3``.

Publish host and port
=====================

In certain cases the address of the node that runs CrateDB differs from the
address where the transport endpoint can be accessed by other nodes. For
example, when running CrateDB inside a Docker container.

To solve this, CrateDB can publish the host and port for discovery. These
published settings can differ from the address of the actual host:

.. code-block:: yaml

    # address accessible from outside
    network.publish_host: public-address.example.com
    # port accessible from outside
    transport.publish_port: 4321

.. rubric:: Related links

- `Host settings for Nodes <https://crate.io/docs/crate/reference/configuration.html#conf-hosts>`_
- `Host settings for Ports <https://crate.io/docs/crate/reference/configuration.html#conf-ports>`_

.. _3.3: https://crate.io/docs/crate/reference/en/3.3/config/cluster.html#discovery
.. _cluster.initial_master_nodes: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#cluster_initial_master_nodes
.. _configuration: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _discovery.zen.minimum_master_nodes: https://crate.io/docs/crate/reference/en/3.3/config/cluster.html#discovery-zen-minimum-master-nodes
.. _latest: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#discovery
.. _master node election: https://crate.io/docs/crate/howtos/en/latest/architecture/shared-nothing.html#master-node-election
.. _quorum guide: https://crate.io/docs/crate/howtos/en/latest/architecture/shared-nothing.html#master-node-election
.. _split-brain: https://en.wikipedia.org/wiki/Split-brain_(computing)
