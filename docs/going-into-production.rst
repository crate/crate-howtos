.. _going-into-production:

=====================
Going into production
=====================

.. rubric:: Table of contents

.. contents::
   :local:


.. _prod-auto-boot:

Bootstrapping in production mode
================================


.. _prod-config:

Important configuration
=======================

The following configurations must be set in the ``crate.yml`` file or via
command line argument. Keep in mind which settings you can or cannot change
during `runtime`_. 

.. _prod-config-path:

Path settings
-------------

In a production setting, you will want to change the default locations of the
data and log folders to avoid the risk of deletion. 

**path.conf**
  | *Runtime*: ``no``

  This sets the filesystem path to the directory containing the configuration
  files ``crate.yml`` and ``log4j2.properties``.

   .. NOTE:: 
  
      CrateDB uses `Log4j`_ for application logging. 


   For example:

   .. code-block::
     yaml

     path.conf: /path/to/conf

**path.data**
  | *Runtime*: ``no``

  This sets the filesystem path to the directory where the CrateDB node stores 
  its data (table data and cluster metadata).

  You can set multiple paths by using a comma-separated list, which will stripe
  data across the locations (a la RAID 0) on a file level. Priority is given to
  locations with more free space. If CrateDB finds striped shards at the
  provided locations (from CrateDB <0.55.0), these shards will be migrated
  automatically on startup.

  For example:

   .. code-block::
     yaml

     path.data: /path/to/data1,/path/to/data2

**path.logs**
  | *Runtime*: ``no``

  This sets the filesystem path to a directory where log files should be stored.

  For example:

  .. code-block::
     yaml

     path.logs: /path/to/logs

  You can use this as a variable inside the file ``log4j2.properties``.

  For example:

  .. code-block::
     yaml

     appender:
       file:
         file: ${path.logs}/${cluster.name}.log


.. _prod-config-cluster-name:

Cluster name
------------

The cluster name identifies your cluster for auto-discovery. Only nodes
with the same name will form a cluster. For example, if you use one name,
this will result in one cluster if the nodes are reachable. If you are
running multiple clusters on the same network, make sure you are using unique
names.

The default value for the cluster is ``crate``, but you can adjust this with
the ``cluster.name`` setting.  


   For example:

   .. code-block::
      yaml

      cluster.name = clusterName


.. _prod-config-node-name:

Node name
---------

**node.name**
  | *Runtime*: ``no``

Node names are used as an identifier for a particular instance of CrateDB
and are included in some API responses. They are generated dynamically on
startup and must be unique in a CrateDB cluster. To tie a node to a specific
name, adjust the ``node.name`` setting. 

   For example:

   .. code-block::
      yaml

      node.name: nodeName


.. _prod-config-network-host:

Network host
------------

By default, CrateDB binds itself to the loopback (or local) addresses on the
system. It listens on port 4200-4300 for HTTP traffic and port 4300-4400 for
node-to-node communication. The range means that if the port is busy, it will
automatically try the next port.

   .. NOTE:: 
   
      Never expose an unprotected node to the public internet.

To form a cluster with nodes on other servers, your node will need to bind to
a non-loopback address. When running a production cluster, you will want to 
change the default settings. 

While there are many `network settings`_, the most important is ``network.host``:

   For example:

   .. code-block::
      yaml

      network.host: 192.168.1.10

Apart from IPv4 and IPv6 addresses, there are some reserved values that can be
used with ``network.host``:

- *_local_* : Any loopback addresses on the system (for example, 127.0.0.1)
- *_site_* : Any site-local addresses on the system (for example, 192.168.0.1)
- *_global_* : Any globally-scoped addresses on the system (for example, 8.8.8.8)
- *_[networkInterface]_* : Addresses of a network interface (for example, _en0_)

   .. NOTE:: 

      Learn more about cluster networking `here`_. 


.. _prod-config-discovery:

Discovery settings
------------------

The `discovery`_ module handles the finding, adding, and removing of nodes. 
Unicast discovery is the default, which allows for explicit control over 
which nodes are used to discover the cluster.

You should configure two important settings before going to production so that 
nodes in the cluster can discover each other and `elect a master node`_. 

**discovery.seed_hosts**
  | *Default*: ``127.0.0.1``
  | *Runtime*: ``no``

To form a cluster with CrateDB instances running on other nodes, you should
use the ``discovery.seed_hosts`` setting to provide a list of other nodes
in the cluster that are master-eligible. This setting should typically contain
the addresses of all the master-eligible nodes in the cluster. To seed the
discovery process, the nodes listed here must be live and contactable. This
setting contains either an array of hosts or a comma-delimited string.

By default, a node will bind to the local address and scan for local ports
between 4300 and 4400 to try to connect to other nodes running on the same
server. This default behavior provides local auto-clustering without any
configuration. Each value should be in the form of ``host:port`` or ``host``
(where port defaults to the setting transport.tcp.port).

   For example:

   .. code-block::
      yaml  

      discovery.seed_hosts:
      - host1:port
      - host2:port

   .. NOTE::

      IPv6 hosts must be in brackets.


**cluster.initial_master_nodes**
  | *Default*: ``not set``
  | *Runtime*: ``no``

When initializing a CrateDB cluster, there is a cluster bootstrapping step
which determines the set of master-eligible nodes whose votes count in the
first election. 

In development mode, with no discovery settings configured, this step is
performed by the nodes themselves. Since this is not set by default, nodes
are expected to join an already formed cluster. This auto-bootstrapping is
designed for development and is not safe for production. When starting a brand
new cluster in production mode, you must explicitly list the names or IP
addresses of the master-eligible nodes whose votes count in the first
election.

You can set this list by using the ``cluster.initial_master_nodes`` setting,
which contains a list of node names, fully-qualified hostnames or IP addresses. 

   For example:

   .. code-block::
      yaml  

      cluster.initial_master_nodes: ["host1", "host2"]

   .. NOTE:: 
   
      You should not use this setting when restarting a cluster or adding a 
      new node to an existing cluster.


.. _prod-config-heap-size:

Heap size
---------

CrateDB is a Java application running on top of a Java Virtual Machine (JVM).
For optimal performance, you must configure the amount of memory available
to the JVM for heap allocations. By default, CrateDB tells the JVM to use a
heap with a minimum and maximum size of 1 GB. When moving to production, it is
important to configure the heap size to ensure that CrateDB has enough heap
available.

The right memory configuration depends on your workloads. A good starting point
for the heap space is 25% of the system memory. However, you should not set it
above 30.5GB due to certain `limits`_. 

You can set the amount of memory that CrateDB uses for heap allocations via the
environment variables: ``CRATE_HEAP_SIZE``, ``CRATE_MIN_MEM``, and ``CRATE_MAX_MEM``.

   For example, to set the heap size to four gigabytes:

   .. code-block::
      yaml  

      CRATE_HEAP_SIZE=4g


   .. NOTE::

      Use *g* for gigabytes or *m* for megabytes. We recommend setting MIN and
      MAX to the same value. The CRATE_HEAP_SIZE environment variable sets MIN
      and MAX to the same value for you.

CrateDB does not perform optimally when the JVM starts swapping. You should
ensure that it _never_ swaps. Set the ``bootstrap.memory_lock`` property to
true to lock the memory.

   For example:

   .. code-block::
      yaml  

      bootstrap.memory_lock: true


.. _prod-config-heap-dump:

Heap dump path
--------------

By default, CrateDB configures the JVM to dump the heap out of memory 
exceptions to the process working directory for `basic installations`_, the 
``/var/lib/crate`` directory if you have installed a `CrateDB Linux package`_, 
and ``/data/data`` when running `CrateDB on Docker`_. 

To modify the directory for heap dumps in the case of a crash, set the 
``CRATE_HEAP_DUMP_PATH`` to point to a file or a directory path of your choice. 


.. _prod-config-gc-logging:

GC logging
----------

CrateDB uses the `G1`_ garbage collector by default.

Before CrateDB 4.1, it defaulted to use the `Concurrent Mark Sweep` garbage
collector. If you would like to continue using CMS, you can switch the setting
on `CRATE_JAVA_OPTS`_

   .. code-block::
      console

      export CRATE_JAVA_OPTS="-XX:-UseG1GC -XX:+UseCMSInitiatingOccupancyOnly -XX:+UseConcMarkSweepGC"

   .. NOTE::

      Since CrateDB 3.0, garbage collection logging is enabled by default.

CrateDB logs JVM garbage collection times using the built-in garbage collection
logging of the JVM. You can use the following environment variables to configure
this: ``CRATE_DISABLE_GC_LOGGING``, ``CRATE_GC_LOG_DIR``, ``CRATE_GC_LOG_SIZE``,
``CRATE_GC_LOG_FILES``. 

You may want to configure ``CRATE_GC_LOG_DIR`` to ensure that the log file
directory has enough space, is fast enough, and that the disk is accessible. When
using Docker, use a path that is on a mounted volume.

Consult the `logging configuration documentation`_ for more details on the garbage
collection logging environment variables and to see the default settings.

If the JVM garbage collection on different memory pools takes too long, CrateDB
will log this. You can adjust these timeouts through this `list of settings`_. 
The warn/info/debug default thresholds should be reasonable for production. 

If you are running CrateDB in Docker, configure the container to send GC debug
logs to standard error (stderr). This lets the container orchestrator handle
the output. 


.. _basic installations: https://crate.io/docs/crate/getting-started/en/latest/install-run/basic.html
.. _CRATE_HEAP_SIZE: https://crate.io/docs/crate/reference/en/latest/config/environment.html#crate-heap-size
.. _CRATE_JAVA_OPTS: https://crate.io/docs/crate/reference/en/latest/config/environment.html?#conf-env-java-opts
.. _CrateDB Linux package: https://crate.io/docs/crate/getting-started/en/latest/install-run/special/linux.html
.. _CrateDB on Docker: https://crate.io/docs/crate/getting-started/en/latest/install-run/special/docker.html
.. _discovery: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#discovery
.. _elect a master node: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html#master-node-election
.. _here: https://crate.io/docs/crate/reference/en/latest/concepts/shared-nothing.html?#networking
.. _limits: https://crate.io/docs/crate/howtos/en/latest/performance/memory.html#limits
.. _list of settings: https://crate.io/docs/crate/reference/en/latest/config/node.html?#garbage-collection
.. _Log4j: https://crate.io/docs/crate/reference/en/latest/config/logging.html#id2
.. _logging configuration documentation: https://crate.io/docs/crate/reference/en/latest/config/logging.html#conf-logging-gc
.. _network settings: https://crate.io/docs/crate/reference/en/latest/config/node.html#hosts
.. _runtime: https://crate.io/docs/crate/reference/en/latest/admin/runtime-config.html#administration-runtime-config
.. _Concurrent Mark Sweep: https://docs.oracle.com/javase/10/gctuning/concurrent-mark-sweep-cms-collector.htm
.. _G1: https://docs.oracle.com/javase/10/gctuning/garbage-first-garbage-collector.htm