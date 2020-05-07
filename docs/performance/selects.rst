==================
Select performance
==================

Aggregations and ``GROUP BY``
=============================

It is common to do ``GROUP BY`` queries for analytics purposes. For example,
you might select the ``avg``, ``max``, and ``min`` of some measurements over a
billion records and group them by device ID.

If you're running this query over a billion records and grouping by device ID,
you might have something like this::

   cr> SELECT
      device_id,
      max(value),
      avg(value),
      min(value)
   FROM
      measures
   GROUP BY
      device_id
   ORDER BY
      1 DESC;

   +-----------+------------+-------------------+------------+
   | device_id | max(value) |        avg(value) | min(value) |
   +-----------+------------+-------------------+------------+
   |         4 |      10000 | 5003.748816285036 |          0 |
   |         3 |      10000 | 5005.297395430482 |          0 |
   |         2 |      10000 | 5002.940588080021 |          0 |
   |         1 |      10000 | 5002.216030711031 |          0 |
   +-----------+------------+-------------------+------------+

By default, CrateDB processes all matching records. This may require a lot of
processing power, depending on the data set and the size of the CrateDB
cluster.

Some databases can limit the amount of records that are processed for
``GROUP BY`` operations (also known as `down-sampling`_) to improve performance
at the cost of less accurate results.

This exploits the fact that if your data set has a `normal distribution`_, it
is likely that the average over the whole data set is not much different from
the average over a subset of the data.

Aggregating 100,000 records instead of 10 or 100 million records can make a
huge difference in query response times.

For some analytics use-cases, this is an acceptable trade-off.

CrateDB users can emulate this down-sampling behaviour with a combination of
`LIMITs`_ and `sub-selects`_. However, doing so involves costly data merges in
the query execution plan that reduce the parallelization (and thus performance)
of a distributed query.

A better way to emulate down-sampling is to filter on the ``_docid`` system
column using a `modulo (%) operation`_, like this::

   cr> SELECT
      device_id,
      max(value),
      avg(value),
      min(value)
   FROM
      measures
   WHERE
      _docid % 10 = 0
   GROUP BY
      device_id
   ORDER BY
      1 DESC;

   +-----------+------------+--------------------+------------+
   | device_id | max(value) |         avg(value) | min(value) |
   +-----------+------------+--------------------+------------+
   |         4 |      10000 | 5013.052623224065  |          1 |
   |         3 |      10000 | 4999.1253575025175 |          0 |
   |         2 |      10000 | 5001.400379047543  |          0 |
   |         1 |      10000 | 5035.220951927276  |          0 |
   +-----------+------------+--------------------+------------+

You'll notice that the result has changed slightly, but is still fairly close
to the original result.

.. TIP::

    The ``% 10`` in this example was arbitrary and roughly translates to: "only
    consider every 10th row."

    The higher the number, the fewer records will match the query and the less
    accurate the result will be. Larger numbers trade accuracy for
    performance.

.. NOTE::

   The ``_docid`` system column exposes the internal document ID each document
   has within a `Lucene segment`_. The IDs are unique within a segment but not
   across segments or shards. This is good enough for a modulo sampling
   operation.

   Furthermore, the internal ID is basically available for free and doesn't
   have to be read from the file system. This makes it an ideal candidate for
   modulo based sampling.

.. _down-sampling: https://grisha.org/blog/2015/03/28/on-time-series/#downsampling
.. _LIMITs: https://crate.io/docs/crate/reference/en/latest/sql/statements/select.html#limit
.. _Lucene segment: https://stackoverflow.com/a/2705123
.. _modulo (%) operation: https://crate.io/docs/crate/reference/en/latest/general/builtins/arithmetic.html
.. _normal distribution: https://en.wikipedia.org/wiki/Normal_distribution
.. _sub-selects: https://crate.io/docs/crate/reference/en/latest/sql/statements/select.html#sub-select
