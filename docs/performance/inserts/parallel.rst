.. _concurrent_inserts:

================
Parallel inserts
================

If you have a queue of inserts, one way to process them in your client is to
send them one by one, waiting for the response from previous insert before
sending the next one.

With a latency of 5ms between the server and client, even if inserts happened
instantaneously, this client could only ever do 200 inserts per second.

If you're handling a lot of inserts, this sort of setup can very quickly become
a performance bottleneck.

The solution to this is to send multiple inserts concurrently. That is, send
off every insert request as soon as you need to and do not wait for a
response before sending another insert.

.. NOTE::

   Before trying to parallelize your queries, you should evaluate whether
   :ref:`inserts_bulk_operations` are a good fit. In many cases, you will see
   even better performance from bulk opperations.


.. rubric:: Table of contents

.. contents::
   :local:

Example
=======

Suppose we have a stream of data we want to persist into CrateDB.
You can parallelize this in Java using a `CompletableFuture`_ object in order to
issue insert statements concurrently (non-blocking).

As the java JDBC `Connection`_ is not thread-safe, each insert must use a
dedicated connection.

A common solution for avoiding over-instantiating connection objects is the use
of a pooled JDBC `DataSource`_ like `HikariCP`_, `vibur-dbcp`_, or
`commons-dbcp`_.

In the following example, `HikariCP`_ is used as a `DataSource`_:

.. code-block:: java

    HikariDataSource ds = new HikariDataSource();
    ds.setJdbcUrl("crate://localhost:5432/doc?user=crate");

    List<CompletableFuture<Integer>> futures = new ArrayList<>();
    IntStream.iterate(0, i -> i + 2)
        .limit(1000)
        .forEach(i -> {
            CompletableFuture<Integer> insertFuture =
                CompletableFuture.supplyAsync(() -> {
                    try (Connection conn = ds.getConnection()) {
                        PreparedStatement stmt = conn
                            .prepareStatement("INSERT INTO t1 (id) VALUES (?)");
                        stmt.setInt(1, i);
                        return stmt.executeUpdate();
                    } catch (SQLException e) {
                        throw new RuntimeException(e);
                    }
                });

            futures.add(insertFuture);
        });

        // Wait for all futures to complete and aggregate each row count
        CompletableFuture<Integer> rowCountFuture = CompletableFuture
                .allOf(futures.toArray(new CompletableFuture[0]))
                .thenApply(ignored -> {
                    Integer cnt = 0;
                    for (CompletableFuture<Integer> future : futures) {
                        cnt += future.join();
                    }
                    return cnt;
                });
        int rowCount = rowCountFuture.get();


Inserts will be executed asynchronously by the `commmonPool`_ object.

You can provide your own `Executor`_ using any object with the appropriate
`supplyAsync`_ signature.

Testing
=======

Follow the basic :ref:`inserts performance testing
<testing_inserts_performance>` procedure.

To test parallel inserts, you should:

1. Configure the setup you would like to test

2. Run a number of different tests against that setup, using different
   ``--concurrency`` settings

3. Evaluate your throughput results (perhaps by plotting your results on
   a graph so that you can see the response curve)

Try out different setups and re-run the test.

At the end of this process, you will have a better understanding of the
throughput of your cluster with different setups and under different loads.

.. _A record: https://en.wikipedia.org/wiki/List_of_DNS_record_types?
.. _commmonPool: https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ForkJoinPool.html#commonPool--
.. _commons-dbcp: https://commons.apache.org/proper/commons-dbcp/
.. _CompletableFuture: https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html
.. _Connection: https://docs.oracle.com/javase/8/docs/api/java/sql/Connection.html
.. _DataSource: https://docs.oracle.com/javase/8/docs/api/javax/sql/DataSource.html
.. _Executor: https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/Executor.html
.. _HAProxy: https://www.haproxy.org/
.. _HikariCP: https://github.com/brettwooldridge/HikariCP
.. _JDBC client: https://crate.io/docs/clients/jdbc/en/latest/
.. _PHP PDO client: https://crate.io/docs/clients/pdo/en/latest/
.. _Python client: https://crate.io/docs/clients/python/en/latest/
.. _supplyAsync: https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html#supplyAsync-java.util.function.Supplier-java.util.concurrent.Executor-
.. _vibur-dbcp: https://www.vibur.org/
