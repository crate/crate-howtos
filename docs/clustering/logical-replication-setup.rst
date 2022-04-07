.. _logical_replication_setup:

==================================================
Logical replication setup between CrateDB clusters
==================================================

:ref:`Logical replication <crate-reference:administration-logical-replication>`
is a method of data replication between multiple clusters.
As a publish/subscribe model, it allows a publishing cluster to make certain
tables available for subscription. Subscribing clusters pull changes from a
publication and replay them on their side.

.. rubric:: Table of contents

.. contents::
   :local:

.. _requirements:

Requirements
============
.. NOTE::

  Logical replication is available in CrateDB 4.8 and later.

To replicate data from one cluster to another, we need two CrateDB clusters.
For this example, we spin them up locally as two single-node Docker
containers.

A cluster isn't limited to be either a publisher or subscriber, but can take
both roles for different tables. However, for the
sake of simplicity, we will refer to the two clusters as
``cluster-publishing`` and ``cluster-subscribing`` here.

.. code-block:: console

  sh$ docker run \
        --name cluster-publishing \
        --detach \
        --publish 4201:4200 \
        --publish 5433:5432 \
        crate:latest \
        -Cdiscovery.type=single-node
  sh$ docker run \
        --name cluster-subscribing \
        --detach \
        --publish 4202:4200 \
        --publish 5434:5432 \
        crate:latest \
        -Cdiscovery.type=single-node

We apply an offset to the ports of each cluster, so they don't overlap. The
Admin UIs of ``cluster-publishing`` and ``cluster-subscribing`` are accessible at
http://localhost:4201/ and http://localhost:4202/ respectively. All SQL
statements discussed below can be executed via the corresponding Admin UI.

As the subscriber pulls changes from the publisher, the publisher needs to accept
incoming network connections from the subscriber. In our example setup, this is
automatically given because both containers are running on the same host.
For reaching each other, they will use the special ``host.docker.internal`` address.

Setting up a publication
========================

.. NOTE::

  All SQL statements in this section are executed on ``cluster-publishing``.

Before setting up the replication, we create a simple table that is going to be
the subject of replication. A table with the same name must not exist yet on
``cluster-subscribing``.

.. code-block:: sql

  CREATE TABLE doc.temperature_data (
    ts TIMESTAMP NOT NULL,
    temperature FLOAT NOT NULL
  );

Next, a publication is created with :ref:`CREATE PUBLICATION <crate-reference:sql-create-publication>`.
The publication marks our table as being available for replication, but otherwise
does not imply any activity yet.

.. code-block:: sql

  CREATE PUBLICATION temperature_publication FOR TABLE doc.temperature_data;

To verify the publication was created successfully, we query the
:ref:`pg_publication <crate-reference:pg_publication>` system table. It should
contain one row with the publication just added.

.. code-block:: sql

  SELECT *
  FROM pg_publication;


With this, we are already all set on the publication side.

Setting up a subscription
=========================

.. NOTE::

  All SQL statements in this section are executed on ``cluster-subscribing``.

A subscription needs connection information to the publishing cluster as
well as the name of the previously created publication to subscribe to.

Specifying the ``mode`` parameter with :ref:`CREATE SUBSCRIPTION <crate-reference:sql-create-subscription>`,
the connection can be established via either the transport protocol or the
PostgreSQL protocol. By setting the parameter to ``pg_tunnel``, we use the
PostgreSQL protocol.


.. code-block:: sql

  CREATE SUBSCRIPTION temperature_subscription
  CONNECTION 'crate://host.docker.internal:5433?user=crate&mode=pg_tunnel'
  PUBLICATION temperature_publication;

.. NOTE::

  The ``password`` parameter is omitted, as local connections using the ``crate``
  user don't require one. If you are connecting remotely, provide ``user`` and
  ``password`` of a user with ``DQL`` privileges on published tables.

After a few seconds, the table ``doc.temperature_data`` should appear on
``cluster-subscribing``. At this point, it is still empty as we didn't insert
any data yet.

To verify the operational status of the subscription, the system tables
:ref:`pg_subscription <crate-reference:pg_subscription>` and :ref:`pg_subscription_rel <crate-reference:pg_subscription_rel>` can be queried. The below query returns
the name of the subscription (``subname``), its state (``srsubstate``), as well
as any potential error message (``srsubstate_reason``).

.. code-block:: sql

  SELECT subname, r.srrelid::TEXT, srsubstate, srsubstate_reason
  FROM pg_subscription s
  LEFT JOIN pg_subscription_rel r ON s.oid = r.srsubid;

``srsubstate`` returns the value ``r``, indicating the initial replication of
the empty table has finished and is awaiting new changes.

Any subsequent ``INSERT``, ``UPDATE`` or ``DELETE`` operations on
``cluster-publishing`` will now replicate to ``cluster-subscribing``.
On ``cluster-subscribing`` the table is read-only, meaning only the publisher
may add or modify rows.
