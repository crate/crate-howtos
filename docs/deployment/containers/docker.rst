.. highlight:: sh

.. _cratedb-docker:

=====================
Run CrateDB on Docker
=====================

CrateDB and `Docker`_ are a great match thanks to CrateDB’s `horizontally
scalable`_ `shared-nothing architecture`_ that lends itself well to
`containerization`_.

This document covers the essentials of running CrateDB on Docker.

.. NOTE::

   If you are just getting started with CrateDB and Docker, check out the
   introductory guides for `spinning up your first CrateDB instance`_.

.. SEEALSO::

    A guide for running CrateDB on :ref:`Kubernetes <cratedb-kubernetes>`.

    The official `CrateDB Docker image`_.

.. rubric:: Table of contents

.. contents::
   :local:

Quick start
===========

Creating a cluster
------------------

To get started with CrateDB and Docker, you will create a three-node cluster
on your dev machine. The cluster will run on a dedicated network and will
require the first two nodes, ``crate01`` and ``crate02``, to vote which one
is the master. The third node, ``crate03``, will simply join the cluster
with no vote.

To create the `user-defined network`_, run the command::

    sh$ docker network create crate

You should then be able to see something like this:

.. code-block:: text

    sh$ docker network ls
    NETWORK ID          NAME                DRIVER              SCOPE
    1bf1b7acd66f        bridge              bridge              local
    51cebbdf7d2b        crate               bridge              local
    5b8e6fbe9ab6        host                host                local
    8baa149b6986        none                null                local

Any CrateDB container put into the ``crate`` network will be able to resolve
other CrateDB containers by name. Each container will run a single node, which
is identified by its node name. In this guide, container ``crate01`` will run
node ``crate01``, container ``crate02`` will run node ``crate02``, and 
container ``crate03`` will run cluster node ``crate03``.

You can then create your first CrateDB container and node, like this::

    sh$ docker run --rm -d \
          --name=crate01 \
          --net=crate \
          -p 4201:4200 \
          --env CRATE_HEAP_SIZE=2g \
          crate -Cnetwork.host=_site_ \
                -Cnode.name=crate01 \
                -Cdiscovery.seed_hosts=crate02,crate03 \
                -Ccluster.initial_master_nodes=crate01,crate02 \
                -Cgateway.expected_nodes=3  -Cgateway.recover_after_nodes=3

Breaking the command down:

- Creates and runs a container called ``crate01`` (--name) in detached
  mode (-d). The container will automatically be removed on exit (--rm),
  and all its internal data will be lost. If you would like to avoid this,
  you can mount a dedicated volume (-v) for the container (each container
  would need its own dedicated folder on your dev machine, see
  :ref:`docker-compose` as reference).
- Puts the container into the ``crate`` network and maps port ``4201`` on your
  host machine to port ``4200`` on the container (admin UI).
- Defines the environment variable ``CRATE_HEAP_SIZE`` which is used by CrateDB
  to allocate 2G for its heap.
- Runs the command ``crate`` inside the container with parameters:
    * ``network.host``: The ``_site_`` value results in the binding of the
      CrateDB process to a site-local IP address.
    * ``node.name``:  Defines the node's name as ``crate01`` (used by
      master election).
    * ``discovery.seed_hosts``: This parameter lists the other hosts in the
      cluster. The format is a comma-separated list of ``host:port`` entries,
      where port defaults to setting ``transport.tcp.port``. Each node must
      contain the name of all the other hosts in this list. Notice also that
      any node in the cluster might be started at any time, and this will
      create connection exceptions in the log files, however all nodes will
      eventually be running and interconnected.
    * ``cluster.initial_master_nodes``: Defines the list of master-eligible
      node names which will participate in the vote of the first master
      (first bootstrap). If this parameter is not defined, then it is expected
      that the node will join an already formed cluster. This parameter is only
      relevant for the first election.
    * ``gateway.expected_nodes`` and ``gateway.recover_after_nodes``: Specifies
      how many nodes you expect in the cluster and how many nodes must be 
      discovered before the cluster state is recovered.

.. NOTE::

   If this command aborts with an error, consult the
   :ref:`docker-troubleshooting` section for help.

Verify that the node is running with ``docker ps`` and you should see something like this:

.. code-block:: text

    sh$ docker ps
    CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                                             NAMES
    f79116373877        crate               "/docker-entrypoin..."   16 seconds ago      Up 15 seconds       4300/tcp, 5432-5532/tcp, 0.0.0.0:4201->4200/tcp   crate01

You can have a look at the container's logs in tail mode like this:

.. code-block:: text

    sh$ docker logs -f crate01

.. NOTE::

    To exit the logs view, press ctrl+C.

You can visit the admin UI in your browser with this URL:

.. code-block:: text

    http://localhost:4201/

Select the *Cluster* icon from the left-hand navigation, and you should see a
page that lists a single node.

Now add the second node, ``crate02``, to the cluster::

    sh$ docker run --rm -d \
          --name=crate02 \
          --net=crate \
          -p 4202:4200 \
          --env CRATE_HEAP_SIZE=2g \
          crate -Cnetwork.host=_site_ \
                -Cnode.name=crate02 \
                -Cdiscovery.seed_hosts=crate01,crate03 \
                -Ccluster.initial_master_nodes=crate01,crate02 \
                -Cgateway.expected_nodes=3 -Cgateway.recover_after_nodes=2

Notice here that:

- You updated the container and node name to ``crate02``.
- You updated the port mapping, so that port ``4202`` on your host is mapped
  to ``4200`` on the container.
- You set the parameter ``discovery.seed_hosts`` to contain the other hosts of
  the cluster.
- ``cluster.initial_master_nodes``:  Since only nodes ``crate01`` and ``crate02``
  will participate in the election of the first master, this setting is unchanged.

Now, if you go back to the admin UI you opened earlier, or visit the admin UI
of the node you just created (located at ``http://localhost:4202/``) you
should see two nodes.

You can now add ``crate03`` like this::

    sh$ docker run --rm -d \
          --name=crate03 \
          --net=crate -p 4203:4200  \
          --env CRATE_HEAP_SIZE=2g \
          crate -Cnetwork.host=_site_ \
                -Cnode.name=crate03 \
                -Cdiscovery.seed_hosts=crate01,crate02 \
                -Cgateway.expected_nodes=3 -Cgateway.recover_after_nodes=2

Notice here that:

- You updated the container and node name to ``crate03``.
- You updated the port mapping, so that port ``4203`` on your host is mapped
  to ``4200`` on the container.
- You set parameter ``discovery.seed_hosts`` to contain the other hosts of the
  cluster.
- ``cluster.initial_master_nodes``:  This setting is removed since only nodes
  ``crate01`` and ``crate02`` will participate in the election of the first
  master.


Success! You just created a three-node CrateDB cluster with Docker.

.. NOTE::

   This is only a quick start example and you will notice some failing checks
   in the admin UI. For a more robust cluster, you should, at the very least,
   configure the `Metadata Gateway`_ and `Discovery`_ settings.

.. _docker-troubleshooting:

Troubleshooting
---------------

The most common issue when running CrateDB on Docker is a failing
:ref:`bootstrap check <bootstrap-checks>`  because the *memory map limit*
is too low. This can be :ref:`adjusted on the host system <bootstrap-checks>`.

If the limit cannot be adjusted on the host system, the memory map limit check
can be bypassed by passing the ``-Cnode.store.allow_mmapfs=false`` option to
the ``crate`` command::

    sh$ docker run -d --name=crate01 \
          --net=crate -p 4201:4200 --env CRATE_HEAP_SIZE=2g \
          crate -Cnetwork.host=_site_ \
                -Cnode.store.allow_mmapfs=false

.. CAUTION::

   This will result in degraded performance.

You can also start a single node without any bootstrap checks by passing the
``-Cdiscovery.type=single-node`` option::

    sh$ docker run -d --name=crate01 \
          --net=crate -p 4201:4200 \
          --env CRATE_HEAP_SIZE=2g \
          crate -Cnetwork.host=_site_ \
                -Cdiscovery.type=single-node

.. NOTE::

   This means that the node cannot form a cluster with any other nodes.

Taking it further
-----------------

`CrateDB settings <https://crate.io/docs/stable/configuration.html>`_ are set
using the ``-C`` flag, as shown in the examples above.

Check out the `Docker docs <https://docs.docker.com/engine/reference/run/>`_
for more Docker-specific features that CrateDB can leverage.

CrateDB Shell
-------------

The CrateDB Shell, ``crash``, is bundled with the Docker image.

If you wanted to run ``crash`` inside a user-defined network called ``crate``
and connect to three hosts named ``crate01``, ``crate02``, and ``crate03``
(i.e. the example covered in the `Creating a Cluster`_ section) you could run::

    $ docker run --rm -ti \
        --net=crate crate \
        crash --hosts crate01 crate02 crate03

.. _docker-compose:

Docker Compose
==============

Docker's Compose tool allows developers to define and run multi-container
Docker applications that can be started with a single ``docker-compose up``
command.

Read about Docker Compose specifics `here <https://docs.docker.com/compose/>`_.

You can define the services that make up your app in a `docker-compose.yml`
file. To recreate the three-node cluster in the previous example, you can
define your services like this: 

.. code-block:: yaml

    version: '3.8'
    services:   
      cratedb01:
        image: crate:latest
        ports:
          - "4201:4200"
        volumes:
          - /tmp/crate/01:/data
        command: ["crate",
                  "-Ccluster.name=crate-docker-cluster",
                  "-Cnode.name=cratedb01",
                  "-Cnode.data=true",
                  "-Cnetwork.host=_site_",
                  "-Cdiscovery.seed_hosts=cratedb02,cratedb03",
                  "-Ccluster.initial_master_nodes=cratedb01,cratedb02,cratedb03",
                  "-Cgateway.expected_nodes=3",
                  "-Cgateway.recover_after_nodes=2"] 
        deploy:
          replicas: 1
          restart_policy:
            condition: on-failure
        environment:
          - CRATE_HEAP_SIZE=2g
      
      cratedb02:
        image: crate:latest
        ports:
          - "4202:4200"
        volumes:
          - /tmp/crate/02:/data
        command: ["crate",
                  "-Ccluster.name=crate-docker-cluster",
                  "-Cnode.name=cratedb02",
                  "-Cnode.data=true",
                  "-Cnetwork.host=_site_",
                  "-Cdiscovery.seed_hosts=cratedb01,cratedb03",
                  "-Ccluster.initial_master_nodes=cratedb01,cratedb02,cratedb03",
                  "-Cgateway.expected_nodes=3",
                  "-Cgateway.recover_after_nodes=2"]  
        deploy:
          replicas: 1
          restart_policy:
            condition: on-failure
        environment:
          - CRATE_HEAP_SIZE=2g
      
      cratedb03:
        image: crate:latest    
        ports:
          - "4203:4200"
        volumes:
          - /tmp/crate/03:/data
        command: ["crate",
                  "-Ccluster.name=crate-docker-cluster",
                  "-Cnode.name=cratedb03",
                  "-Cnode.data=true",
                  "-Cnetwork.host=_site_",
                  "-Cdiscovery.seed_hosts=cratedb01,cratedb02",
                  "-Ccluster.initial_master_nodes=cratedb01,cratedb02,cratedb03",
                  "-Cgateway.expected_nodes=3",
                  "-Cgateway.recover_after_nodes=2"]
        deploy:
          replicas: 1
          restart_policy:
            condition: on-failure
        environment:
          - CRATE_HEAP_SIZE=2g

In the file above:

- You specified the latest `compose file version`_. 
- You created three CrateDB services which pulls the latest CrateDB Docker
  image and maps the ports manually.
- You created a file system volume per instance and defined a set of
  configuration parameters (`-C`).
- You defined some deploy settings and an environment variable for the heap size.
- Network settings no longer need to be defined in the latest compose file
  version because a `default bridge network`_ will be created. If you are 
  using multiple hosts and want to use an overlay network, you will need to
  explicitly define that. 
- The start order of the containers is not deterministic and you want all
  three containers to be up and running before the election of the master node.

Best Practices
==============

One container per host
----------------------

For performance reasons, we strongly recommend that you only run one container
per host machine.

If you are running one container per machine, you can map the container ports
to the host ports so that the host acts like a native installation. For example::

    $ docker run -d -p 4200:4200 -p 4300:4300 -p 5432:5432 crate \
        crate -Cnetwork.host=_site_

Persistent data directory
-------------------------

Docker containers are ephemeral, meaning that containers are expected to come
and go, and any data inside them is lost when the container is removed. For
this reason, you should mount a persistent ``data`` directory on your host
machine to the ``/data`` directory inside the container::

    $ docker run -d -v /srv/crate/data:/data crate \
        crate -Cnetwork.host=_site_

Here, ``/srv/crate/data`` is an example path, and should be replaced with the
path to your host machine's ``data`` directory.

See the `Docker volume`_ documentation for more help.

Custom configuration
--------------------

If you want to use a custom configuration, it is recommended that you mount
configuration files on the host machine to the appropriate path inside the
container. That way, your configuration will not be lost if the container is
removed.

Here is an example of how you could mount the ``crate.yml`` config file::

    $ docker run -d \
        -v /srv/crate/config/crate.yml:/crate/config/crate.yml crate \
        crate -Cnetwork.host=_site_

Here, ``/srv/crate/config/crate.yml`` is an example path, and should be
replaced with the path to your host machine's ``crate.yml`` file.

Troubleshooting
===============

The official `CrateDB Docker image`_ ships with a liveness `healthcheck`_
configured.

This healthcheck will flag a problem if the CrateDB process crashed or hung
inside the container without terminating.

If you use `Docker Swarm`_ and are experiencing trouble starting your Docker
containers, try to deactivate the healthcheck.

You can do that by editing your `Docker Stack YAML file`_:

.. code-block:: yaml

    healthcheck:
      disable: true

.. _resource_constraints:

Resource constraints
====================

To avoid overallocation of resources, you may want to consider setting
constraints on CPU and memory if you plan to run multiple CrateDB containers
on a single machine.


Bootstrap checks
----------------

When using CrateDB with Docker, CrateDB binds by default to any site-local IP
address on the system (i.e. 192.168.0.1). This performs a number of checks 
during bootstrap. The settings listed in `Bootstrap Checks`_ must be addressed on
the Docker **host system** in order to start CrateDB successfully and when 
`going into production`_.

Memory
------

You must calculate and explicitly `set the maximum memory`_ that the container
can use. This is dependent on your host system and should typically be as high
as possible.

You must then calculate the appropriate heap size (typically half the container's
memory limit, see `CRATE_HEAP_SIZE`_ for details) and pass this to CrateDB,
which in turn passes it to the JVM.

It is not necessary to configure swap memory since CrateDB does not use swap.

CPU
---

You must calculate and explicitly `set the maximum number of CPUs`_ that the
container can use. This is dependent on your host system and should typically
be as high as possible.

Combined configuration
----------------------

If you want the container to use a maximum of 1.5 CPUs, a maximum of 2 GB
memory, with a heap size of 1 GB, you could configure everything at once. For
example::

    $ docker run -d \
        --cpus 1.5 \
        --memory 2g \
        --env CRATE_HEAP_SIZE=1g \
        crate \
        crate -Cnetwork.host=_site_

.. _Bootstrap Checks: https://crate.io/docs/crate/howtos/en/latest/admin/bootstrap-checks.html
.. _compose file version: https://docs.docker.com/compose/compose-file/compose-versioning/
.. _containerization: https://www.docker.com/resources/what-container
.. _CRATE_HEAP_SIZE: https://crate.io/docs/crate/reference/configuration.html#crate-heap-size
.. _CrateDB Docker image: https://hub.docker.com/_/crate/
.. _default bridge network: https://docs.docker.com/network/#network-drivers
.. _Discovery: https://crate.io/docs/crate/reference/configuration.html#discovery
.. _Docker Stack YAML file: https://docs.docker.com/docker-cloud/apps/stack-yaml-reference/
.. _Docker Swarm: https://docs.docker.com/engine/swarm/
.. _Docker volume: https://docs.docker.com/engine/tutorials/dockervolumes/
.. _Docker: https://www.docker.com/
.. _going into production: https://crate.io/docs/crate/howtos/en/latest/going-into-production.html
.. _healthcheck: https://docs.docker.com/engine/reference/builder/#healthcheck
.. _horizontally scalable: https://en.wikipedia.org/wiki/Scalability#Horizontal_and_vertical_scaling
.. _Metadata Gateway: https://crate.io/docs/crate/reference/configuration.html#metadata-gateway
.. _running Docker locally: https://crate.io/docs/install/containers/docker/
.. _set the maximum memory: https://docs.docker.com/engine/admin/resource_constraints/#memory
.. _set the maximum number of CPUs: https://docs.docker.com/engine/admin/resource_constraints/#cpu
.. _shared-nothing architecture : https://en.wikipedia.org/wiki/Shared-nothing_architecture
.. _spinning up your first CrateDB instance: https://crate.io/docs/crate/getting-started/en/latest/install/containers/docker.html
.. _user-defined network: https://docs.docker.com/engine/userguide/networking/#user-defined-networks
