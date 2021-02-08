.. _going-into-production:

=====================
Going into production
=====================

Running CrateDB in different environments requires different approaches. This
document outlines the basics you need to consider when going into production.

.. rubric:: Table of contents

.. contents::
   :local:


.. _prod-bootstrapping:

Configure bootstrapping
=======================

The process of forming a cluster is known as *bootstrapping*. Consult the
how-to guide on :ref:`CrateDB multi-node setups <multi_node_setup>` for an
overview of the two different ways to bootstrap a cluster.

If you have been using CrateDB for development on your local machine, there is
a good chance you have been using :ref:`single host auto-bootstrapping
<auto-bootstrapping>`.

For improved performance and resiliency, you should run production CrateDB
clusters with three or more nodes and one node per host machine. To do this,
you must manually configure the bootstrapping process by telling nodes how to:

  a. :ref:`Discover other nodes <node-discovery>`
  b. :ref:`Elect a master node <master-node-election>`

This process is known as *manual bootstrapping*. See the :ref:`how-to guide
<manual-bootstrapping>` for more information about how to bootstrap a cluster
manually.

Switching to a manual bootstrapping configuration is the first step towards
going into production.


.. _prod-naming:

Naming
======


.. _prod-cluster-name:

Configure a logical cluster name
--------------------------------

The `cluster.name`_ setting allows you to override the default cluster name of
``crate``. You should use this setting to give a logical name to your cluster.

For example, add this to your `configuration`_ file:

.. code-block:: yaml

    cluster.name: acme-prod

The ``acme-prod`` name suggests that this cluster is the production cluster for
the *Acme* organization. If *Acme* has a cluster running in a staging
environment, you might want to name it ``acme-staging``. This way, you can
differentiate your clusters by name (visible in the `Admin UI`_).

.. TIP::

    A node will refuse to join a cluster if the respective cluster names
    do not match

.. SEEALSO::

    :ref:`Cluster names for multi-node setups <multi-node-cluster-name>`


.. _prod-config-hostname:

Bind nodes to logical hostnames
-------------------------------

By default, CrateDB binds to the loopback address (i.e., `localhost`_). It
listens on port 4200-4299 for HTTP traffic and port 4300-4399 for node-to-node
communication. Because CrateDB uses a port range, if one port is busy, it will
automatically try the next port.

When using :ref:`multiple hosts <multi_node_setup>`, nodes must bind to a
non-loopback address.

.. CAUTION::

      Never expose an unprotected CrateDB node to the public internet

You can bind to a non-loopback address with the `network.host`_ setting in your
`configuration`_ file, like so:

.. code-block:: yaml

    network.host: node-01-md.acme-prod.internal.example.com

You must configure the ``node-01-md.acme-prod.internal.example.com`` hostname
using DNS. You must then set `network.host`_ to match the DNS name.

You should use the hostname to describe each node logically. To this end, the
example hostname (above) has four components:

- ``example.com`` -- The root domain name
- ``internal`` -- The internal private network
- ``acme-prod`` -- The cluster name
- ``node-01-md`` -- The :ref:`node label <prod-config-node-labels>`

When CrateDB is bound to a non-loopback address, CrateDB will enforce the
:ref:`bootstrap checks <bootstrap-checks>`. These checks may require changes to
your operating system configuration.

.. SEEALSO::

    `Host settings`_


.. _prod-config-node-labels:

Logical node labels
~~~~~~~~~~~~~~~~~~~

CrateDB supports `multiple types of node`_, determined by the ``node.master``
and ``node.data`` settings. You can use this information to give a logical DNS
label to each of your nodes.

.. _node-name-match:

.. TIP::

    CrateDB :ref:`sets node names automatically <multi-node-node-name>`. If you
    are happy with automatic node names, there is no need to set `node.name`_
    and hence you can use the same `configuration`_ on every node.

    When :ref:`configuring cluster bootstrapping <prod-bootstrapping>`, you can
    :ref:`specify the list of master-eligible nodes <master-node-election>`
    using hostnames. This allows you to configure logical hostnames with DNS node
    labels that differ from the node name set by CrateDB.

    If you would prefer your node names to match your DNS node labels, you will
    have to configure `node.name`_ manually on each host.


.. SEEALSO::

    :ref:`Node names for multi-node setups <multi-node-node-name>`


.. _prod-node-md:

Multi-purpose nodes
^^^^^^^^^^^^^^^^^^^

You can `configure`_ a master-eligible node that also handles query execution
loads like this:

.. code-block:: yaml

    node.master: true
    node.data: true

A good DNS label for this node might be ``node-01-md``.

Here, ``node`` is used as base label with a sequence number of ``01``. Every
node in the cluster should have a unique sequence number, independent of the
node type. The letters ``md`` indicate that this node has ``node.master`` and
``node.data`` set to ``true``.

If you optionally want your node name to match (:ref:`see above
<node-name-match>`), configure the `node.name`_ setting in your
`configuration`_ file, like so:

.. code-block:: yaml

    node.name: node-01-md

Alternatively, you can configure this setting at startup with a command-line
option:

.. code-block:: console

    sh$ bin/crate \
            -Cnode.name=node-01-md


.. _prod-node-d:

Request handling and query execution nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can `configure`_ a node that only handles client requests and query
execution (i.e., is not master-eligible) like this:

.. code-block:: yaml

    node.master: false
    node.data: true

A good DNS label for this node might be ``node-02-d``.

Here, ``node`` is used as base label with a sequence number of ``02``. Every
node in the cluster should have a unique sequence number, independent of the
node type. The letter ``d`` indicates that this node has ``node.data`` set to
``true``.

If you optionally want your node name to match (:ref:`see above
<node-name-match>`), configure the `node.name`_ setting in your
`configuration`_ file, like so:

.. code-block:: yaml

    node.name: node-02-d

Alternatively, you can configure this setting at startup with a command-line
option:

.. code-block:: console

    sh$ bin/crate \
            -Cnode.name=node-02-d


.. _prod-node-m:

Cluster management nodes
^^^^^^^^^^^^^^^^^^^^^^^^

You can `configure`_ a node that handles cluster management (i.e., is
master-eligible) but does not handle query execution loads like this:

.. code-block:: yaml

    node.master: true
    node.data: false

A good DNS label for this node might be ``node-03-m``.

Here, ``node`` is used as base label with a sequence number of ``03``. Every
node in the cluster should have a unique sequence number, independent of the
node type. The letter ``m`` indicates that this node has ``node.master`` set to
``true``.

If you optionally want your node name to match (:ref:`see above
<node-name-match>`), configure the `node.name`_ setting in your
`configuration`_ file, like so:

.. code-block:: yaml

    node.name: node-03-m

Alternatively, you can configure this setting at startup with a command-line
option:

.. code-block:: console

    sh$ bin/crate \
            -Cnode.name=node-03-m


.. _prod-node:

Request handling nodes
^^^^^^^^^^^^^^^^^^^^^^

You can `configure`_ a node that handles client requests but does not handle query
execution loads or cluster management (i.e., is not master-eligible) like this:

.. code-block:: yaml

    node.master: false
    node.data: false

A good DNS label for this node might be ``node-04``.

Here, ``node`` is used as base label with a sequence number of ``04``. Every
node in the cluster should have a unique sequence number, independent of the
node type. The absence of any additional letters indicates that ``node.master``
and ``node.data`` are ``false``.

If you optionally want your node name to match (:ref:`see above
<node-name-match>`), configure the `node.name`_ setting in your
`configuration`_ file, like so:

.. code-block:: yaml

    node.name: node-04

Alternatively, you can configure this setting at startup with a command-line
option:

.. code-block:: console

    sh$ bin/crate \
            -Cnode.name=node-04


.. _prod-config-paths:

Configure persistent data paths
===============================

By default, CrateDB keeps data under the `CRATE_HOME`_ directory (which
defaults to the installation directory). When you upgrade CrateDB, you will
have to switch to a new installation directory.

Instead of migrating data by hand each time, you should move the data
directories off to a persistent location. You can do this using the
`CRATE_HOME`_ environment variable and the `path settings`_ in your
`configuration`_ file.

.. SEEALSO::

    `Path settings`_

If you are following the `shared-nothing`_ approach to deployment, the best way
to handle persistent data is to keep it on an external volume. This allows you
to persist data beyond the lifespan of an individual virtual machine or
container.

.. CAUTION::

    This is required if you are using Docker, which is stateless by design.
    Failing to persist data to a mounted volume will result in data loss when
    the container is stopped.

.. TIP::

    Using an external volume for persistence also allows you to optimize the
    underlying storage mechanism for performance.

    You should take care to size your data storage volumes according to your
    needs. You should also use storage with high `IOPS`_ when possible to
    improve CrateDB performance.

On a Unix-like system, you might mount an external volume to a path like
``/opt/cratedb``. If you are installing CrateDB by hand, you can then set
`CRATE_HOME`_ to ``/opt/cratedb``. Make sure to set ``CRATE_HOME`` before
running `bin/crate`_.

Then, you could configure your `data paths`_ like this:

.. code-block:: yaml

    path.conf: /opt/cratedb/config
    path.data: /opt/cratedb/data
    path.logs: /opt/cratedb/logs
    path.repo: /opt/cratedb/snapshots

Here, the values given for ``path.conf``, ``path.data``, and ``path.logs``
reflect the default paths when ``CRATE_HOME`` is set to ``/opt/cratedb``. The
example above configures them for illustrative purposes. You do not have to
configure these settings if you are happy with the defaults.

.. NOTE::

    Normally, configuration files, data files, log files, and so on would be
    kept under specialized directories such as ``/etc``, ``/var/lib``, and
    ``/var/log`` (see the `Linux Filesystem Hierarchy`_ for more information).

    However, if you want to customize your installation to make use of a single
    external volume, it is necessary to bring these directories together under
    a single mount point. You can do this by relocating all data directories
    under your mount point (``/opt/cratedb`` in the example above). Other
    approaches are possible (for example, using `symbolic links`_).

    If you have installed CrateDB using a system package for :ref:`Debian
    <debian>`, :ref:`Ubuntu <ubuntu>`, or :ref:`Red Hat <red-hat>`, the
    `CRATE_HOME`_ variable (as well as some data paths) are configured for by
    the `systemd`_ *service file*. You can view the ``crate`` service file,
    like so:

    .. code-block:: console

        sh$ systemctl cat crate


.. _prod-jvm:

Tune the JVM
============


.. _prod-config-heap:

Heap
----

CrateDB is a Java application running on top of a Java Virtual Machine (JVM).
The JVM uses a heap for memory allocations. For optimal performance, you must
pay special attention to your :ref:`heap configuration <memory>`.

By default, CrateDB configures the JVM to dump out-of-memory exceptions to the
file or directory specified by `CRATE_HEAP_DUMP_PATH`_. You must make sure
there is enough disk space available for heap dumps at this location.

.. SEEALSO::

    `JVM environment variables`_


.. _prod-config-gc:

Garbage collection
------------------

CrateDB logs JVM garbage collection times using the built-in *garbage
collection* (GC) logging provided by the JVM. You can configure this process
with the `GC logging environment variables`_.

You must ensure that the log directory is on a fast-enough disk and has enough
space. When using Docker, use a path on a mounted volume.

If garbage collection takes too long, CrateDB will log this. You can adjust the
`timeout settings`_ to suit your needs. However, the default settings should
work in most instances.

If you are running CrateDB on Docker, you should configure the container to
send debug logs to `STDERR`_ so that the container orchestrator handles the
output.


.. _prod-wire-encryption:

Configure wire encryption
=========================

For security reasons, most production clusters should use wire encryption for
network traffic between nodes and clients. Check out the reference manual on
`secured communications`_ for more information.


.. _Admin UI: https://crate.io/docs/crate/admin-ui/en/latest/
.. _bin/crate: https://crate.io/docs/crate/reference/en/latest/cli-tools.html#crate
.. _cluster.name: https://crate.io/docs/crate/reference/en/latest/config/node.html#cluster-name
.. _configuration: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _configure: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _CRATE_HEAP_DUMP_PATH: https://crate.io/docs/crate/reference/en/latest/config/environment.html#conf-env-dump-path
.. _CRATE_HEAP_SIZE: https://crate.io/docs/crate/reference/en/latest/config/environment.html#crate-heap-size
.. _CRATE_HOME: https://crate.io/docs/crate/reference/en/latest/config/environment.html#conf-env-crate-home
.. _CRATE_JAVA_OPTS: https://crate.io/docs/crate/reference/en/latest/config/environment.html?#conf-env-java-opts
.. _data paths: https://crate.io/docs/crate/reference/en/4.4/config/node.html#paths
.. _discovery: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#discovery
.. _elect a master node: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#master-node-election
.. _Filesystem Hierarchy Standard: https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard
.. _GC logging environment variables: https://crate.io/docs/crate/reference/en/latest/config/logging.html#environment-variables
.. _Host settings: https://crate.io/docs/crate/reference/en/latest/config/node.html#hosts
.. _IOPS: https://en.wikipedia.org/wiki/IOPS
.. _JVM environment variables: https://crate.io/docs/crate/reference/en/latest/config/environment.html#jvm-variables
.. _limits: https://crate.io/docs/crate/howtos/en/latest/performance/memory.html#limits
.. _Linux Filesystem Hierarchy: https://tldp.org/LDP/Linux-Filesystem-Hierarchy/html/index.html
.. _localhost: https://en.wikipedia.org/wiki/Localhost
.. _logging: https://crate.io/docs/crate/reference/en/latest/config/logging.html
.. _multiple types of node: https://crate.io/docs/crate/reference/en/latest/config/node.html#node-types
.. _network.host: https://crate.io/docs/crate/reference/en/latest/config/node.html#network-host
.. _node.name: https://crate.io/docs/crate/reference/en/latest/config/node.html#node-name
.. _path settings: https://crate.io/docs/crate/reference/en/latest/config/node.html#paths
.. _path.data: https://crate.io/docs/crate/reference/en/latest/config/node.html#path-data
.. _RAID 0: https://en.wikipedia.org/wiki/Standard_RAID_levels#RAID_0
.. _runtime: https://crate.io/docs/crate/reference/en/latest/admin/runtime-config.html#administration-runtime-config
.. _secured communications: https://crate.io/docs/crate/reference/en/latest/admin/ssl.html
.. _shared-nothing: https://en.wikipedia.org/wiki/Shared-nothing_architecture
.. _STDERR: https://en.wikipedia.org/wiki/Standard_streams
.. _symbolic links: https://en.wikipedia.org/wiki/Symbolic_link
.. _sys.summits: https://crate.io/docs/crate/reference/en/latest/admin/system-information.html#summits
.. _systemd: https://github.com/systemd/systemd
.. _timeout settings: https://crate.io/docs/crate/reference/en/latest/config/node.html?#garbage-collection
.. _Unix-like: https://en.wikipedia.org/wiki/Unix-like
