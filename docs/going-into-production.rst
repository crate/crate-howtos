.. _going-into-production:

=====================
Going into production
=====================

Running CrateDB in different environments requires different approaches. This
document outlines the basics you need to consider when going into production.

.. rubric:: Table of contents

.. contents::
   :local:


.. _prod-auto-boot:

Manual bootstrapping
====================

:ref:`Single host auto-bootstrapping <auto-bootstrapping>` is useful for
development environments. However, auto-bootstrapping is typically too slow for
production use. Additionally, for improved performance and resiliency,
production CrateDB clusters should be run with one node per host machine. If
you use multiple hosts, you must configure your cluster with :ref:`manual
bootstrapping <manual-bootstrapping>`.


.. _prod-config:

Additional considerations
=========================

The following setting can be changed in your `configuration`_ file or set via
command-line arguments. Additionally, you can change some settings at
`runtime`_.


.. _prod-config-path:

Paths
-----

In a production environment, you should change the default locations of the
data and log folders to avoid accidental deletion.

.. SEEALSO::

    `Path settings`_


.. _prod-config-cluster-name:

Cluster name
------------

The `cluster.name`_ setting allows you to create multiple separate clusters. A
node will refuse to join a cluster if the respective cluster names do not
match.

If you are running multiple clusters on the same network, you should set unique
cluster names.

.. SEEALSO::

    :ref:`Cluster names for multi-node setups <multi-node-cluster-name>`


.. _prod-config-node-name:

Node name
---------

By default, CrateDB sets the node name for you. However, if you configure the
node names explicitly, you can specify a list of master-eligible nodes
up-front.

You can configure a custom node name using the `node.name`_ setting.

.. SEEALSO::

    :ref:`Node names for multi-node setups <multi-node-node-name>`


.. _prod-config-network-host:

Network host
------------

By default, CrateDB binds to the loopback address (i.e., `localhost`_). It
listens on port 4200-4300 for HTTP traffic and port 4300-4400 for node-to-node
communication. Because CrateDB uses a port range, if one port is busy, it will
automatically try the next port.

When using :ref:`multiple hosts <multi_node_setup>`, nodes must bind to a
non-loopback address.

You can bind to a non-loopback address with the `network.host`_ setting.

.. SEEALSO::

    `Host settings`_

.. CAUTION::

      Never expose an unprotected CrateDB node to the public internet


.. _prod-config-heap:

Heap
----

CrateDB is a Java application running on top of a Java Virtual Machine (JVM).
The JVM uses a heap for memory allocations. For optimal performance, you must
pay special attention to your heap configuration.

.. SEEALSO::

    :ref:`Optimizing memory performance <memory>`

By default, CrateDB configures the JVM to dump out of memory exceptions to the
file or directory specified by `CRATE_HEAP_DUMP_PATH`_. You must make sure
there is enough disk space available for heap dumps at this location.

.. SEEALSO::

    `JVM environment variables`_


.. _prod-config-gc:

Garbage collection
------------------

CrateDB logs JVM garbage collection times using the built-in garbage collection
logging of the JVM. You can configure this process the garbage collection
`environment variables`_.

.. SEEALSO::

    `Logging`_

You must ensure that the log directory is on a fast-enough disk and has enough
space. When using Docker, use a path on a mounted volume.

If garbage collection takes too long, CrateDB will log this. You can adjust the
`timeout settings`_ to suit your needs. However, the default settings should
work in most instances.

If you are running CrateDB on Docker, you should configure the container to
send debug logs to `STDERR`_ so that the container orchestrator handles the
output.


.. _cluster.name: https://crate.io/docs/crate/reference/en/latest/config/node.html#cluster-name
.. _configuration: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _CRATE_HEAP_DUMP_PATH: https://crate.io/docs/crate/reference/en/latest/config/environment.html#conf-env-dump-path
.. _CRATE_HEAP_SIZE: https://crate.io/docs/crate/reference/en/latest/config/environment.html#crate-heap-size
.. _CRATE_JAVA_OPTS: https://crate.io/docs/crate/reference/en/latest/config/environment.html?#conf-env-java-opts
.. _discovery: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#discovery
.. _elect a master node: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#master-node-election
.. _environment variables: https://crate.io/docs/crate/reference/en/latest/config/logging.html#environment-variables
.. _Host settings: https://crate.io/docs/crate/reference/en/latest/config/node.html#hosts
.. _JVM environment variables: https://crate.io/docs/crate/reference/en/latest/config/environment.html#jvm-variables
.. _limits: https://crate.io/docs/crate/howtos/en/latest/performance/memory.html#limits
.. _localhost: https://en.wikipedia.org/wiki/Localhost
.. _logging: https://crate.io/docs/crate/reference/en/latest/config/logging.html
.. _network.host: https://crate.io/docs/crate/reference/en/latest/config/node.html#network-host
.. _node.name: https://crate.io/docs/crate/reference/en/latest/config/node.html#node-name
.. _path settings: https://crate.io/docs/crate/reference/en/latest/config/node.html#paths
.. _RAID 0: https://en.wikipedia.org/wiki/Standard_RAID_levels#RAID_0
.. _runtime: https://crate.io/docs/crate/reference/en/latest/admin/runtime-config.html#administration-runtime-config
.. _STDERR: https://en.wikipedia.org/wiki/Standard_streams
.. _timeout settings: https://crate.io/docs/crate/reference/en/latest/config/node.html?#garbage-collection
