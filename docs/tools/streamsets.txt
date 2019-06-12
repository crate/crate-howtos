=========================================================================
Building data stream pipelines with CrateDB and StreamSets data collector
=========================================================================

.. rubric:: Table of contents

.. contents::
   :local:

Introduction
============

`CrateDB`_ can be integrated with `StreamSets`_ using its `JDBC driver`_.

The CrateDB JDBC driver can be used as an origin and destination stage in
the StreamSets Data Collector pipeline.

`Install and run CrateDB`_ on localhost.

`Install the StreamSets Data Collector`_ on localhost.

In order to build your first data stream pipeline the standalone version of the
CrateDB JDBC driver has to be obtained and installed in the StreamSets as an
external library. You can download the latest standalone version directly from
Crate.io's `Bintray Repository`_.

After the JDBC driver is downloaded to an arbitrary destination, you can
proceed with the installation of the driver for StreamSets. We recommend
following the StreamSets tutorial on installing `external libs`_. Although, to
get started quickly, you can place the CrateDB JDBC driver JAR file in the
StreamSets classpath.

The next two sections provide a brief introduction on how to build data stream
pipelines using CrateDB with the StreamSets Data Collector. In the first
section, we are going to demonstrate how to build the pipeline with the
`directory origin`_ stage that supplies the CSV data sample and streams data
to JDBC destination stage using the CrateDB JDBC driver. In the second section,
we demonstrate how to use the CrateDB JDBC driver as a StreamSets origin.

We use the following versions in the tutorial:

- CrateDB – ``3.2.3``
- CrateDB JDBC Driver – ``2.5.1``
- StreamSets Data Collector – ``3.7.2``

CrateDB JDBC Producer
=====================

The CrateDB JDBC Producer stage uses the JDBC connection to write data into the
database. In this section, we show how to build the StreamSets project for
ingesting CSV records from the local filesystem into CrateDB with the
pre-processing of some record fields.

1. Create a `new data collector pipeline`_ and create and
   `configure the directory origin`_ to reads CSV files from the local file
   system. We use the New York taxi `data sample`_ in the tutorial.

   .. image:: 1-directory-origin-csv.png
      :alt: Configure the directory origin

2. For the sake of simplicity, we use only 4 fields from the CSV files. All
   source fields are represented as strings in the CSV. However, some of the
   selected fields should be converted into float values. Therefore, we add an
   additional processing `Field Type Converter`_ stage into the pipeline.

   .. image:: 2-streamsets-dst-field-conversion.png
      :alt: Convert string input values

3. Create the ``taxi`` table in CrateDB.

   .. code-block:: psql

       CREATE TABLE taxi (
            hack_license STRING,
            medallion STRING,
            total_amount FLOAT,
            tip_amount FLOAT
       );

4. The next step is to configure the CrateDB JDBC destination. First, load the
   CrateDB JDBC driver. Then configure the JDBC driver with the connection
   string, schema, table and default operation.

   .. image:: 3-streamsets-dst-driver-conf.png
      :alt: Configure the CrateDB JDBC Producer

   Finally, we set the default credentials to CrateDB in the "credentials" tab.

   .. image:: 3-streamsets-dst-jdbc-credentials.png
      :alt: Set credentials for the CrateDB JDBC Producer

5. Start the pipeline.

   .. image:: 3-streamsets-dst-output.png
      :alt: Pipeline run report

CrateDB JDBC Query Consumer
===========================

The `JDBC Query Consumer`_ uses the JDBC connection to read data from  CrateDB.
The CrateDB JDBC Query Consumer stage returns data as a map with column names
and field values.

Currently, the usage of the CrateDB JDBC driver in combination with StreamSets
Data Collector introduces few limitations:

-  Only incremental mode for the data fetch is supported.
-  The offset column should be the primary key column to prevent the insertion
   of duplicate rows.

The followings steps demonstrate how CrateDB can be used as the origin stage in
the data stream pipeline. As sample data, we use the `AMPLab rankings dataset`_.
The data can be imported from `AWS S3`_ to the CrateDB database using prepared
data import queries hosted in the `CrateDB demo repository`_. Create the
`rankings table`_ and import the `rankings data`_. In the demo, we use a
dataset that contains 18 million of records. Having the CrateDB cluster set up
and the rankings sample data is imported, we can start building the data stream
pipeline for streaming the data from the CrateDB database to CSV files.

1. Create a `new data collector pipeline`_ and configure the CrateDB JDBC Driver
   loading as it was done for the JDBC destination configuration. In the JDBC
   tab of the CrateDB JDBC origin we set the connection string, the SQL query
   for fetching the data from the database, the initial offset, and offset
   column. For more detail information on how to set the offset column and its
   value, see the `JDBC Query Consumer offset`_ documentation.

   .. image:: 4-streamsets-source-jdbc-conf.png
      :alt: Configure the CrateDB JDBC driver

   **IMPORTANT**

   To avoid unsupported transaction setting queries that may be invoked against
   CrateDB, it is necessary to uncheck ``Enforce Read-only Connection`` on the
   advanced tab of the JDBC consumer.

2. We stream the records from CrateDB to CSV files. In order to accomplish that
   we provide the path where the files are going to be created and set the
   output file format in the directory origin to *Delimited*.

   .. image:: 4-streamsets-source-fs-conf.png
      :alt: Configure CSV destination

3. Now we can start the pipeline and see rankings data streaming statistics
   form the CrateDB database to CSV files.

   .. image:: 4-streamsets-origin-report.png
      :alt: CrateDB to CSV report


.. _AMPLab rankings dataset: https://amplab.cs.berkeley.edu/benchmark/
.. _AWS S3: https://aws.amazon.com/s3/
.. _Bintray Repository: https://bintray.com/crate/crate/crate-jdbc/view/files/io/crate/crate-jdbc-standalone/
.. _configure the directory origin: https://streamsets.com/documentation/datacollector/latest/help/datacollector/UserGuide/Tutorial/BasicTutorial.html#task_ftt_2vq_ks
.. _CrateDB: https://crate.io
.. _CrateDB demo repository: https://github.com/crate/crate-demo/tree/master/amplab/
.. _data sample: https://streamsets.com/documentation/datacollector/latest/help/datacollector/UserGuide/Tutorial/BeforeYouBegin.html?hl=nyc_taxi_data/
.. _directory origin: https://streamsets.com/documentation/datacollector/latest/help/#Origins/Directory.html#concept_qcq_54n_jq/
.. _external libs: https://streamsets.com/documentation/datacollector/latest/help/datacollector/UserGuide/Configuration/ExternalLibs.html#concept_pdv_qlw_ft/
.. _Field Type Converter: https://streamsets.com/documentation/controlhub/latest/help/datacollector/UserGuide/Processors/FieldTypeConverter.html?hl=field%2Ctype/
.. _Install and run CrateDB: https://crate.io/docs/crate/getting-started/en/latest/install-run/index.html
.. _Install the StreamSets Data Collector: https://streamsets.com/opensource/
.. _new data collector pipeline: https://streamsets.com/documentation/datacollector/latest/help/#Pipeline_Design/What_isa_Pipeline.html/
.. _rankings data: https://github.com/crate/crate-demo/blob/master/amplab/queries/import_rankings_1node.sql/
.. _rankings table: https://github.com/crate/crate-demo/blob/master/amplab/queries/rankings.sql/
.. _JDBC driver: https://github.com/crate/crate-jdbc/
.. _JDBC Query Consumer: https://streamsets.com/documentation/datacollector/latest/help/datacollector/UserGuide/Origins/JDBCConsumer.html#concept_nxz_2kz_bs/
.. _JDBC Query Consumer offset: https://streamsets.com/documentation/datacollector/latest/help/datacollector/UserGuide/Origins/JDBCConsumer.html#concept_nxz_2kz_bs
.. _StreamSets: https://streamsets.com/
