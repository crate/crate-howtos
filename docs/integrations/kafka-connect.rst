============================================
Data Ingestion using Kafka and Kafka Connect
============================================

This integration document details how to create an ingestion
pipeline from a `Kafka`_ source to a CrateDB sink, using the `Kafka Connect
JDBC connector`_.

Abstract
========

Kafka is a popular stream processing software used for building scalable data
processing pipelines and applications. Many different use-cases might involve
wanting to ingest the data from a Kafka topic (or several topics) into CrateDB
for further enrichment, analysis, or visualization. This can be done using the
supplementary component `Kafka Connect`_, which provides a set of connectors
that can stream data to and from Kafka.

Using the `Kafka Connect JDBC connector`_ with the PostgreSQL driver allows
you to designate CrateDB as a sink target, with the following example connector
definition:

.. code-block:: json

  {
   "name": "cratedb-connector",
   "config": {
     "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
     "topics": "metrics",
     "connection.url": "jdbc:postgresql://localhost:5432/doc?user=crate",
     "tasks.max": 1,
     "insert.mode": "insert",
     "table.name.format": "metrics"
   }
  }

This results in the following architecture:

.. _figure_1:

.. figure:: kafka-connect.png
   :align: center


Implementation
==============


Setup
-----

To illustrate how this architecture can be used, we will create a scenario
where we have machine sensor data from a series of weather stations being
ingested into a Kafka topic. This data could be used in a reactive sense: for
example, a micro-controller could consume from this topic to turn on air
conditioning if the temperature were to rise above a certain threshold. But
besides this use of the data, we want to ingest them into CrateDB. This allows
us to do long-term data analytics to predict weather trends. Each payload from
each sensor looks like this:

.. code-block:: json

        {
          "id": "sensor-1",
          "timestamp": 1588240576,
          "payload": {
            "temperature": 43.2,
            "humidity": 12.2,
            "pressure": 1013.3,
            "luminosity": 3003.4,
          }
        }

The fields in the payload are:

- ``id`` - The identification string of the individual sensor.
- ``temperature`` - The temperature the sensor records, in Celsius.
- ``humidity`` - The humidity the sensor records, from 0% to 100%.
- ``pressure`` - The barometric pressure the sensor records, in millibar.
- ``luminosity`` - The ambient luminosity the sensor records, in lux.
- ``timestamp`` - The timestamp of when this payload was recorded.


Prerequisites
-------------

To deploy this architecture, there are several prerequisites:

- A running and accessible Kafka stack, including Kafka, ZooKeeper, Schema
  Registry, and Kafka Connect. This example implementation will use the
  `Confluent Platform`_ to start and interact with the components, but there are
  many different avenues and libraries available.
- A CrateDB Cluster, running on at least version 4.2.0.
- A way of producing Kafka messages using an Avro schema. This implementation
  will use Python 3 with the ``confluent-kafka`` and ``avro-python3`` libraries.


Kafka Producer
--------------

First, start the Kafka stack. With the `Confluent Platform`_, starting a local
development stack can be done via:

.. code-block:: console

   $ confluent local services start

   Starting ZooKeeper
   ZooKeeper is [UP]
   Starting Kafka
   Kafka is [UP]
   Starting Schema Registry
   Schema Registry is [UP]
   Starting Kafka REST
   Kafka REST is [UP]
   Starting Connect
   Connect is [UP]

Next, you should define the `Avro schema`_ of the producer's messages, in this
case, weather sensors. Given the structure described in the setup
section, the Avro schema will be:

.. code-block:: json

   {
     "namespace": "cratedb.metrics",
     "name": "value",
     "type": "record",
     "fields": [
       {"name": "id", "type": "string"},
       {"name": "timestamp", "type": "float"},
       {"name": "payload", "type": {
           "type": "record",
           "name": "payload",
           "fields": [
             {"name": "temperature", "type": "float"},
             {"name": "humidity", "type": "float"},
             {"name": "pressure", "type": "float"},
             {"name": "luminosity", "type": "float"}
           ]
         }
       }
     ]
   }


For this example, this Python script will simulate the creation
of random sensor data and push it into the ``metrics`` topic:

.. code-block:: python

   import time
   import random

   from confluent_kafka import avro
   from confluent_kafka.avro import AvroProducer

   # Define the Avro schema we want our produced records to conform to.
   VALUE_SCHEMA_STR = """
   {
     "namespace": "cratedb.metrics",
     "name": "value",
     "type": "record",
     "fields": [
       {"name": "id", "type": "string"},
       {"name": "timestamp", "type": "float"},
       {"name": "payload", "type": {
           "type": "record",
           "name": "payload",
           "fields": [
             {"name": "temperature", "type": "float"},
             {"name": "humidity", "type": "float"},
             {"name": "pressure", "type": "float"},
             {"name": "luminosity", "type": "float"}
           ]
         }
       }
     ]
   }
   """

   # Load the Avro schema.
   VALUE_SCHEMA = avro.loads(VALUE_SCHEMA_STR)

   # Create an Avro producer using the defined schema, assuming that our
   # Kafka servers are running at localhost:9092 and the Schema Registry
   # server is running at localhost:8081.
   AVRO_PRODUCER = AvroProducer(
       {
           "bootstrap.servers": "localhost:9092",
           "schema.registry.url": "http://localhost:8081",
       },
       default_value_schema=VALUE_SCHEMA,
   )

   # Create a metric payload from a simulated sensor device.
   def create_metric():
       return {
           "id": "sensor-" + str(random.choice(list(range(1, 21)))),
           "timestamp": int(time.time()),
           "payload": {
               "temperature": random.uniform(-5, 35),
               "humidity": random.uniform(0, 100),
               "pressure": random.uniform(1000, 1030),
               "luminosity": random.uniform(0, 65000),
           },
       }

   # Create a new metric every 0.25 seconds and push it to the metrics topic.
   while True:
       AVRO_PRODUCER.produce(topic="metrics", value=create_metric())
       AVRO_PRODUCER.flush()
       time.sleep(0.25)

This script can be run by installing the following dependencies and running it:

.. code-block:: console

   $ pip install "confluent-kafka[avro]" "avro-python3"
   $ python simulator.py

You can verify that the simulator is working by consuming from the Kafka topic:

.. code-block:: console

   $ confluent local services kafka consume metrics --from-beginning --value-format avro

   {"id":"sensor-13","timestamp":1.59180096E9,"payload":{"temperature":-1.8094289,"humidity":0.06487691,"pressure":1019.0834,"luminosity":41412.7}}
   {"id":"sensor-5","timestamp":1.59180096E9,"payload":{"temperature":15.625463,"humidity":39.6379,"pressure":1009.4658,"luminosity":58013.066}}
   {"id":"sensor-20","timestamp":1.59180096E9,"payload":{"temperature":5.555978,"humidity":34.635147,"pressure":1028.5662,"luminosity":16234.626}}
   {"id":"sensor-7","timestamp":1.59180096E9,"payload":{"temperature":12.604255,"humidity":70.70301,"pressure":1009.50116,"luminosity":37786.098}}

Kafka Connect
=============

Before you initialise the JDBC connector to ingest data into CrateDB, you should
verify that the JDBC connector plugin is available on your Kafka Connect
instance.

You can do this by using the confluent command-line tool, to list all available
Connect plugins:

.. code-block:: console

  $ confluent local services connect plugin list
   Available Connect Plugins:
   [
      ...
      {
          "class": "io.confluent.connect.jdbc.JdbcSinkConnector",
          "type": "sink",
          "version": "10.1.1"
      },
      ...
  ]

We will be using the ``io.confluent.connect.jdbc.JdbcSinkConnector`` connector.
In addition to that, another plugin is needed for transforming the message into
JSON format. This can be installed via:

.. code-block:: console

  $ confluent-hub install jcustenborder/kafka-connect-transform-common:latest

CrateDB
-------
.. CAUTION::

   The steps below apply to CrateDB versions >= 4.7.0.
   For older versions, please see :ref:`Older CrateDB versions <kafka-connect-older-CrateDB-versions>`.

We start by creating the target table. The columns ``topic``, ``partition``, and
``offset`` will be filled by Kafka with their corresponding values.
The message is modelled as an ``OBJECT(DYNAMIC)``, meaning it will
automatically add and index new fields from your record.

.. code-block:: sql

  CREATE TABLE "doc"."metrics" (
      "topic" TEXT NOT NULL,
      "partition" INTEGER NOT NULL,
      "offset" BIGINT NOT NULL,
      "message" OBJECT(DYNAMIC) AS (
          "id" TEXT,
          "timestamp" TIMESTAMP,
          "payload" OBJECT(DYNAMIC) AS (
              "humidity" REAL,
              "luminosity" REAL,
              "pressure" REAL,
              "temperature" REAL
          )
      ),
      PRIMARY KEY ("topic", "partition", "offset")
  );

Now we can define the JDBC sink connector. The connector
definition for this use case looks like this, which you should save to a file
called ``cratedb_connector.json``:

.. code-block:: json

  {
    "name": "cratedb-connector",
    "config": {
      "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
      "connection.url": "jdbc:postgresql://localhost:5432/doc?user=crate",
      "topics": "metrics",
      "tasks.max": 1,
      "insert.mode": "insert",
      "table.name.format": "metrics",

      "pk.mode": "kafka",
      "pk.fields": "topic,partition,offset",

      "transforms": "toJSON,wrapValue",
      "transforms.toJSON.type": "com.github.jcustenborder.kafka.connect.transform.common.ToJSON$Value",
      "transforms.toJSON.schemas.enable": false,
      "transforms.wrapValue.type": "org.apache.kafka.connect.transforms.HoistField$Value",
      "transforms.wrapValue.field": "message"
    }
  }

Here is more detail for some of the parameters:

+--------------------------------------+--------------------------------------------------------------------------+
| Parameter                            | Description                                                              |
+======================================+==========================================================================+
| ``connector.class``                  | The type of Connector plugin that you want to                            |
|                                      | initialize.                                                              |
+--------------------------------------+--------------------------------------------------------------------------+
| ``connection.url``                   | The URL to the CrateDB instance that you want                            |
|                                      | to act as the sink. This should be in the form                           |
|                                      | ``jdbc://postgresql://<CrateDB Host>/<Schema>?user=<User>``.             |
+--------------------------------------+--------------------------------------------------------------------------+
| ``topics``                           | The list of topics we want the connector to                              |
|                                      | consume from. In this implementation, it is                              |
|                                      | only the ``metrics`` topic, but it could be                              |
|                                      | several.                                                                 |
+--------------------------------------+--------------------------------------------------------------------------+
| ``tasks.max``                        | The max number of connector tasks that should be                         |
|                                      | created to consume messages. Having a                                    |
|                                      | number higher than 1 allows you to parallelize                           |
|                                      | consumption, to have higher throughput.                                  |
+--------------------------------------+--------------------------------------------------------------------------+
| ``insert.mode``                      | How the data consumed from the topics should                             |
|                                      | be inserted into CrateDB. We choose ``insert`` is chosen, as messages    |
|                                      | do not get updated after initial publishing.                             |
+--------------------------------------+--------------------------------------------------------------------------+
| ``table.name.format``                | The target table name. ``${topic}`` can be used as a dynamic part of     |
|                                      | the name.                                                                |
+--------------------------------------+--------------------------------------------------------------------------+
| ``pk.mode``                          | Lets Kafka determine the primary key based on its metadata.              |
+--------------------------------------+--------------------------------------------------------------------------+
| ``pk.fields``                        | A list of attributes uniquely describing a message.                      |
+--------------------------------------+--------------------------------------------------------------------------+
| ``transforms``                       | A list of transformation rules to apply, which are defined further down. |
+--------------------------------------+--------------------------------------------------------------------------+
| ``transforms.toJSON.type``           | Specified the class providing the transformation and sets the record's   |
|                                      | value as the transformation target.                                      |
+--------------------------------------+--------------------------------------------------------------------------+
| ``transforms.toJSON.schemas.enable`` | Disables the schema of the JSON getting included.                        |
+--------------------------------------+--------------------------------------------------------------------------+
| ``transforms.wrapValue.type``        | Wraps the generated JSON into a field. The field equals the column in    |
|                                      | our target table.                                                        |
+--------------------------------------+--------------------------------------------------------------------------+
| ``transforms.wrapValue.field``       | The name of the field containing the serialized JSON.                    |
+--------------------------------------+--------------------------------------------------------------------------+

More `JDBC Sink Connector settings`_ exist which can affect things like batch inserting, parallelization,
etc.

You can now create a connector instance using this configuration:

.. code-block:: console

   $ confluent local services connect connector load cratedb-connector -c cratedb_connector.json

   {
     "name": "cratedb-connector",
     "config": {
       "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
       "topics": "metrics",
       "connection.url": "jdbc:postgresql://localhost:5432/doc?user=crate",
       "tasks.max": "1",
       "insert.mode": "insert",
       "table.name.format": "metrics",
       "pk.mode": "kafka",
       "pk.fields": "topic,partition,offset",
       "transforms": "toJSON,wrapValue",
       "transforms.toJSON.type": "com.github.jcustenborder.kafka.connect.transform.common.ToJSON$Value",
       "transforms.toJSON.schemas.enable": "false",
       "transforms.wrapValue.type": "org.apache.kafka.connect.transforms.HoistField$Value",
       "transforms.wrapValue.field": "message",
       "name": "cratedb-connector"
     },
     "tasks": [],
     "type": "sink"
   }

You can monitor the status of the newly created connector and verify that it is
running:

.. code-block:: console

   $ confluent local services connect connector status cratedb-connector

   {
     "name": "cratedb-connector",
     "connector": {
       "state": "RUNNING",
       "worker_id": "127.0.0.1:8083"
     },
     "tasks": [
       {
         "id": 0,
         "state": "RUNNING",
         "worker_id": "127.0.0.1:8083"
       }
     ],
     "type": "sink"
   }

Finally, you can verify that data is flowing into the CrateDB table:

.. code-block:: console

   $ crash
   cr> SELECT COUNT(*) FROM metrics;
   +----------+
   | count(*) |
   +----------+
   |     3410 |
   +----------+

   cr> SELECT * FROM metrics LIMIT 5;
   +---------+-----------+--------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | topic   | partition | offset | message                                                                                                                                                       |
   +---------+-----------+--------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | metrics |         0 |  24521 | {"id": "sensor-16", "payload": {"humidity": 95.754425, "luminosity": 63707.867, "pressure": 1029.3485, "temperature": 27.77532}, "timestamp": 1627477760.0}   |
   | metrics |         0 |  24523 | {"id": "sensor-18", "payload": {"humidity": 8.981689, "luminosity": 33933.863, "pressure": 1025.1156, "temperature": 27.980207}, "timestamp": 1627477760.0}   |
   | metrics |         0 |  24525 | {"id": "sensor-20", "payload": {"humidity": 36.30519, "luminosity": 36909.668, "pressure": 1028.3536, "temperature": 16.281057}, "timestamp": 1627477760.0}   |
   | metrics |         0 |  24533 | {"id": "sensor-13", "payload": {"humidity": 80.966446, "luminosity": 38612.555, "pressure": 1023.91144, "temperature": 13.155711}, "timestamp": 1627477760.0} |
   | metrics |         0 |  24538 | {"id": "sensor-4", "payload": {"humidity": 43.69954, "luminosity": 29412.008, "pressure": 1003.7084, "temperature": 8.321792}, "timestamp": 1627477760.0}     |
   +---------+-----------+--------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+

.. _kafka-connect-older-CrateDB-versions:

Older CrateDB versions
^^^^^^^^^^^^^^^^^^^^^^

CrateDB versions older than 4.7.0 don't support the ``JSON`` data type yet,
which requires a slightly different setup. Instead of storing messages as an
``OBJECT``, they need to be flattened and modelled as separate columns.

Please follow the steps above with two variations.

**Target table layout:** Use this ``CREATE TABLE`` statement with a flattened
column layout.

.. code-block:: sql

    CREATE TABLE "doc"."metrics" (
      "timestamp" TIMESTAMP WITH TIME ZONE,
      "payload_temperature" REAL,
      "payload_humidity" REAL,
      "payload_pressure" REAL,
      "payload_luminosity" REAL,
      "id" TEXT
    );

**JDBC Sink Connector configuration:** Use this connector configuration to
flatten nested fields.

.. code-block:: json

  {
    "name": "cratedb-connector",
    "config": {
      "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
      "topics": "metrics",
      "connection.url": "jdbc:postgresql://localhost:5432/doc?user=crate",
      "tasks.max": 1,
      "insert.mode": "insert",
      "table.name.format": "metrics",
      "transforms.flatten.type": "org.apache.kafka.connect.transforms.Flatten$Value",
      "transforms": "flatten",
      "transforms.flatten.delimiter": "_"
    }
  }

The remaining steps from above remain are applicable without changes.

.. _Kafka: https://www.confluent.io/what-is-apache-kafka/
.. _Kafka Connect JDBC connector: https://docs.confluent.io/kafka-connect-jdbc/current/sink-connector/
.. _Confluent Platform: https://docs.confluent.io/current/cli/index.html
.. _Avro schema: https://avro.apache.org/docs/current/spec.html
.. _PostgreSQL Kafka Connect JDBC driver: https://docs.confluent.io/kafka-connect-jdbc/current/index.html#postgresql-database
.. _Sink Connector: https://docs.confluent.io/current/connect/kafka-connect-jdbc/sink-connector/index.html
.. _Source Connector: https://docs.confluent.io/current/connect/kafka-connect-jdbc/source-connector/index.html
.. _Kafka Connect Transformation: https://docs.confluent.io/current/connect/transforms/index.html
.. _JDBC Sink Connector settings: https://docs.confluent.io/current/connect/kafka-connect-jdbc/sink-connector/sink_config_options.html
.. _Kafka Connect: https://docs.confluent.io/current/connect/index.html
