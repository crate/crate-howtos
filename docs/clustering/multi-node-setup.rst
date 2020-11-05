.. _multi_node_setup:

========================
CrateDB multi-node setup
========================

CrateDB can run on a single node. However, in most environments, CrateDB is run
as a cluster of three or more nodes.

For development purposes, CrateDB can :ref:`auto-bootstrap
<auto-bootstrapping>` a cluster when you run all nodes on the same host.
But in production environments, you must configure the bootstrapping process
:ref:`manually <manual-bootstrapping>`.

This guide shows you how to bootstrap (set up) a multi-node CrateDB cluster
using different methods.

.. rubric:: Table of contents

.. contents::
   :local:


.. _cluster-bootstrapping:

Cluster bootstrapping
=====================

Starting a CrateDB cluster for the first time requires the initial list of
master-eligible nodes to be defined. This is known as *cluster bootstrapping*.

This process is only necessary the first time a cluster starts because:

- nodes that are already part of a cluster will remember this information if
  the cluster restarts

- new nodes that need to join a cluster will obtain this information from the
  cluster's elected master node


.. _auto-bootstrapping:

Single-host auto-bootstrapping
------------------------------

If you start up several nodes (with default configuration) on a single host,
the nodes will automatically discover one another and form a cluster. This
does not require any configuration.

If you want to run CrateDB on your local machine for development or
experimentation purposes, this is probably your best option.

.. CAUTION::

    For better performance and resiliency, :ref:`production
    <going-into-production>` CrateDB clusters should be run with :ref:`one node
    per host machine <manual-bootstrapping>`. If you use multiple hosts, you
    must :ref:`manually bootstrap <manual-bootstrapping>` your cluster.

.. WARNING::

    If you start multiple nodes on different hosts with auto-bootstrapping
    enabled, you cannot, at a later point, merge those nodes together to form
    a single cluster without the risk of data loss.

    If you have multiple nodes running on different hosts, you can check
    whether they have formed independent clusters by visiting the `admin UI`_
    (which runs on every node) and checking the `cluster browser`_.

    If you end up with multiple independent clusters and instead want to
    form a single cluster, follow these steps:

      1. `Back up your data`_
      2. Shut down all the nodes
      3. Completely wipe each node by deleting the contents of the ``data``
         directory under `CRATE_HOME`_
      4. Follow the instructions in :ref:`manual bootstrapping
         <manual-bootstrapping>`)
      5. Restart all the nodes and verify that they have formed a single cluster
      6. Restore your data


.. _auto-bootstrapping-tarball:

Tarball installation
^^^^^^^^^^^^^^^^^^^^

If you are installing CrateDB using the `tarball method`_, you can start a
single-host three-node cluster with auto-bootstrapping by following these
instructions.

1. Unpack the tarball:

   .. code-block:: console

       sh$ tar -xzf crate-*.tar.gz

2. You should configure the :ref:`metadata gateway <metadata-gateway>` so that
   CrateDB knows how to recover its state safely. Ideally, for a three-node
   cluster, set `gateway.expected_nodes`_ to **3** and set
   `gateway.recover_after_nodes`_ to **3**. You can specify these settings in
   the `configuration`_ file of the unpacked directory.

   .. NOTE::

      Configuring the `metadata gateway`_ is a safeguarding mechanism that is
      useful for production clusters. It is not strictly necessary when running
      in development. However, the `admin UI`_ will issue warnings if you have
      not configured the metadata gateway.

   .. SEEALSO::

       The :ref:`metadata gateway <metadata-gateway>` section includes examples.

3. Copy the unpacked directory into a new directory, three times, one for each
   node. For example:

   .. code-block:: console

       sh$ cp -R crate-*/ node-01
       sh$ cp -R crate-*/ node-02
       sh$ cp -R crate-*/ node-03

   .. TIP::

      Each directory will function as `CRATE_HOME`_ for that node

4. Start up all three nodes by changing into each node directory and running
   the `bin/crate`_ script.

   .. CAUTION::

       You must change into the appropriate node directory before running the
       `bin/crate`_ script.

       When you run `bin/crate`_, the script sets `CRATE_HOME`_ to your current
       directory. This directory must be the root of a CrateDB installation.

   .. TIP::

       Because you are supposed to run `bin/crate`_ as a `daemon`_ (i.e., a
       long-running process), the most straightforward way to run multiple
       nodes for testing purposes is to start a new terminal session for each
       node. In each session, change into the appropriate node directory, run
       `bin/crate`_, and leave this process running. You should now have
       multiple concurrent `bin/crate`_ processes.

5. Visit the `admin UI`_ on one of the nodes. Check the `cluster browser`_ to
   verify that the cluster has auto-bootstrapped with three nodes. You should see
   something like this:

   .. image:: ../_assets/img/multi-node-cluster.png
      :alt: The CrateDB Admin UI showing a multi-node cluster


.. _manual-bootstrapping:

Manual bootstrapping
--------------------

To run a CrateDB cluster across multiple hosts, you must manually configure the
bootstrapping process by telling nodes how to:

  a. :ref:`Discover other nodes <node-discovery>`
  b. :ref:`Elect a master node <master-node-election>`

You must also configure the :ref:`metadata gateway <metadata-gateway>` (as with
auto-bootstrapping).


.. _node-discovery:

Node discovery
^^^^^^^^^^^^^^


Seeding manually
""""""""""""""""

With CrateDB 4.x and above, you can configure a list of nodes to `seed the
discovery process`_ with the ``discovery.seed_hosts`` setting in your
`configuration`_ file. This setting should contain one identifier per
master-eligible node. For example:

.. code-block:: yaml

    discovery.seed_hosts:
      - node-01.example.com:4300
      - 10.0.1.102:4300
      - 10.0.1.103:4300

Alternatively, you can configure this at startup with a command-line option.
For example:

.. code-block:: console

    sh$ bin/crate \
            -Cdiscovery.seed_hosts=node-01.example.com,10.0.1.102,10.0.1.103

.. NOTE::

    You must configure every node with a list of seed nodes. Each node
    discovers the rest of the cluster via the seed nodes.

.. TIP::

    If you are using CrateDB 3.x or below, you can use the
    `discovery.zen.ping.unicast.hosts`_ setting instead of
    ``discovery.seed_hosts``.


.. _unicast-discovery:

Unicast host discovery
""""""""""""""""""""""

Instead of configuring seed hosts manually (:ref:`as above <node-discovery>`),
you can configure CrateDB to fetch a list of seed hosts from an external source.

The currently supported sources are:

1. `DNS`_

   To enable DNS discovery, configure the ``discovery.seed_providers`` setting
   in your `configuration`_ file to ``srv``:

   .. code-block:: yaml

       discovery.seed_providers: srv

   CrateDB will perform a DNS query using `SRV records`_ and use the results to
   generate a list of `unicast hosts`_ for node discovery.

2. `Amazon EC2`_

   To enable Amazon EC2 discovery, configure the ``discovery.seed_providers``
   setting in your `configuration`_ file:

   .. code-block:: yaml

       discovery.seed_providers: ec2

   CrateDB will perform an `Amazon EC2 API`_ query and use the results to
   generate a list of `unicast hosts`_ for node discovery.

3. `Microsoft Azure`_

   To enable Microsoft Azure discovery, configure the ``discovery.seed_providers``
   setting in your `configuration`_ file:

   .. code-block:: yaml

       discovery.seed_providers: azure

   CrateDB will perform an `Azure Virtual Machine API`_ query and use the results
   to generate a list of `unicast hosts`_ for node discovery.


.. _master-node-election:

Master node election
^^^^^^^^^^^^^^^^^^^^

The master node is responsible for making changes to the global cluster state.
The cluster `elects the master node`_ from the configured list of
master-eligible nodes the first time a cluster is bootstrapped. This is not
necessary if nodes are added later or are restarted.

In development mode, with no discovery settings configured, master election is
performed by the nodes themselves, but this auto-bootstrapping is designed to
aid development and is not safe for production. In production you must
explicitly list the names or IP addresses of the master-eligible nodes whose
votes should be counted in the very first election.

If initial master nodes are not set, then new nodes will expect to be able to
discover an existing cluster. If a node cannot find a cluster to join, then it
will periodically log a warning message indicating that the master is not
discovered or elected yet.

You can define the initial set of master-eligible nodes with the
`cluster.initial_master_nodes`_ setting in your `configuration`_ file. This
setting should contain one identifier per master-eligible node. For example:

.. code-block:: yaml

    cluster.initial_master_nodes:
      - node-01.example.com
      - 10.0.1.102
      - 10.0.1.103

Alternatively, you can configure this at startup with a command-line option.
For example:

.. code-block:: console

    sh$ bin/crate \
            -Ccluster.initial_master_nodes=node-01.example.com,10.0.1.102,10.0.1.10

.. WARNING::

    You do not have to configure `cluster.initial_master_nodes`_ on every node.
    However, you must configure `cluster.initial_master_nodes`_ identically
    whenever you do configure it, otherwise CrateDB may form multiple
    independent clusters (which may result in data loss).

CrateDB requires a `quorum`_ of nodes before a master can be elected. A quorum
ensures that the cluster does not elect multiple masters in the event of a
network partition (also known as a `split-brain`_ scenario).

CrateDB (versions 4.x and above) will automatically determine the ideal `quorum
size`_. If you are using CrateDB versions 3.x and below, you must manually set
the quorum size using the `discovery.zen.minimum_master_nodes`_ setting.

.. NOTE::

    For a three-node cluster, CrateDB will set the quorum size to three.
    Consequentially, you must declare all nodes to be master-eligible. Consult
    the `quorum guide`_ for detailed information about quorum size
    considerations.

If you configure fewer master-eligible nodes than the ideal quorum size,
CrateDB will issue a warning (visible in the logs and the `admin UI`_).


.. _metadata-gateway:

Metadata gateway
^^^^^^^^^^^^^^^^

When running a multi-node cluster, you must configure the `metadata gateway`_
so that CrateDB knows how to recover its state. For a three-node cluster, set
`gateway.expected_nodes`_ to **3** and `gateway.recover_after_nodes`_ to **3**.

You can specify both settings in your `configuration`_ file:

.. code-block:: yaml

    gateway:
      recover_after_nodes: 3
      expected_nodes: 3

Alternatively, you can configure this setting at startup with command-line
options:

.. code-block:: console

    sh$ bin/crate \
        -Cgateway.expected_nodes=3 \
        -Cgateway.recover_after_nodes=3

.. SEEALSO::

    `Metadata configuration settings`_


.. _multi-node-other:

Other settings
==============


.. _multi-node-cluster-name:

Cluster name
------------

The `cluster.name`_ setting allows you to create multiple separate clusters. A
node will refuse to join a cluster if the respective cluster names do not
match.

By default, CrateDB sets the cluster name to ``crate`` for you.

You can override this behavior by configuring a custom cluster name using the
`cluster.name`_ setting in your `configuration`_ file:

.. code-block:: yaml

    cluster.name: my_cluster

Alternatively, you can configure this setting at startup with a command-line
option:

.. code-block:: console

    sh$ bin/crate \
            -Ccluster.name=my_cluster


.. _multi-node-node-name:

Node name
---------

If you are :ref:`manually bootstrapping <manual-bootstrapping>` a cluster, you
must specify a list of master-eligible nodes (:ref:`see above
<master-node-election>`). To do this, you must refer to nodes by node name,
hostname, or IP address.

By default, CrateDB sets the node name to a random value from the
`sys.summits`_ table.

You can override this behavior by configuring a custom node name using the
`node.name`_ setting in your `configuration`_ file. For example:

.. code-block:: yaml

    node.name: node-01

Alternatively, you can configure this setting at startup with a command-line
option:

.. code-block:: console

    sh$ bin/crate \
            -Cnode.name=node-01


.. _master-eligible-nodes:

Master-eligibility
------------------

If you are :ref:`manually bootstrapping <manual-bootstrapping>` a cluster, any
nodes you :ref:`list as master-eligible <master-node-election>` must have a
`node.master`_ value of ``true``. This is the default value.


.. _inter-node-comms:

Inter-node communication
------------------------

By default, CrateDB nodes communicate with each other on port ``4300``. This
port is known as the *transport port*, and it must be accessible from every
node.

If you prefer, you can specify a port range instead of a single port number.
Edit the `transport.tcp.port`_ setting in your `configuration`_ file:

.. code-block:: yaml

    transport.tcp.port: 4350-4360

.. TIP::

    If you are running a node on Docker, you must configure CrateDB to publish the
    container's external hostname and the external port number bound to the
    transport port. You can do that in your `configuration`_ file using the
    `network.publish_host`_ and `transport.publish_port`_ settings.

    For example:

    .. code-block:: yaml

        # External access
        network.publish_host: node-01.example.com
        transport.publish_port: 4321

.. SEEALSO::

    `More information about port settings`_


.. _127.0.0.1:4200: http://127.0.0.1:4200/
.. _127.0.0.1:4201: http://127.0.0.1:4201/
.. _admin UI: https://crate.io/docs/crate/admin-ui/
.. _Amazon EC2 API: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/Welcome.html
.. _Amazon EC2: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#discovery-on-amazon-ec2
.. _Azure Virtual Machine API: https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines
.. _Back up your data: https://crate.io/a/backing-up-and-restoring-cratedb/
.. _bin/crate: https://crate.io/docs/crate/reference/en/latest/cli-tools.html#crate
.. _cluster browser: https://crate.io/docs/crate/admin-ui/en/latest/cluster.html
.. _cluster: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html
.. _cluster.initial_master_nodes: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#cluster_initial_master_nodes
.. _cluster.name: https://crate.io/docs/crate/reference/en/latest/config/node.html#cluster-name
.. _configuration: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _CRATE_HOME: https://crate.io/docs/crate/reference/en/latest/config/environment.html#conf-env-crate-home
.. _daemon: https://en.wikipedia.org/wiki/Daemon_(computing)
.. _discovery.zen.minimum_master_nodes: https://crate.io/docs/crate/reference/en/3.3/config/cluster.html#discovery-zen-minimum-master-nodes
.. _discovery.zen.ping.unicast.hosts: https://crate.io/docs/crate/reference/en/3.3/config/cluster.html#unicast-host-discovery
.. _DNS: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#discovery-via-dns
.. _elects the master node: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#master-node-election
.. _full cluster restarts: https://crate.io/docs/crate/howtos/en/latest/admin/full-restart-upgrade.html
.. _gateway.expected_nodes: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#gateway-expected-nodes
.. _gateway.recover_after_nodes: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#gateway-recover-after-nodes
.. _hostname: https://en.wikipedia.org/wiki/Hostname
.. _latest: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#discovery
.. _Metadata configuration settings: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#metadata
.. _metadata gateway: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#metadata-gateway
.. _Microsoft Azure: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#discovery-on-microsoft-azure
.. _More information about port settings: https://crate.io/docs/crate/reference/en/latest/config/node.html#ports
.. _network.publish_host: https://crate.io/docs/crate/reference/en/latest/config/node.html#network-publish-host
.. _node.master: https://crate.io/docs/crate/reference/en/latest/config/node.html#node.master
.. _node.name: https://crate.io/docs/crate/reference/en/latest/config/node.html#node-name
.. _quorum guide: https://crate.io/docs/crate/howtos/en/latest/architecture/shared-nothing.html#master-node-election
.. _quorum size: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#master-node-election
.. _quorum: https://en.wikipedia.org/wiki/Quorum_(distributed_computing)
.. _seed the discovery process: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#discovery
.. _split-brain: https://en.wikipedia.org/wiki/Split-brain_(computing)
.. _SRV records: https://en.wikipedia.org/wiki/SRV_record
.. _sys.summits: https://crate.io/docs/crate/reference/en/latest/admin/system-information.html#summits
.. _tarball method: https://crate.io/docs/crate/tutorials/en/latest/install-run/basic.html
.. _transport.publish_port: https://crate.io/docs/crate/reference/en/latest/config/node.html#transport-publish-port
.. _transport.tcp.port: https://crate.io/docs/crate/reference/en/latest/config/node.html#transport-tcp-port
.. _unicast hosts: https://crate.io/docs/crate/reference/en/latest/config/cluster.html#unicast-host-discovery
