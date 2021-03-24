==================
Insert performance
==================

A ``INSERT INTO`` statement is processed as follows:

 - Parse the statement to create an `abstract syntax tree`_
 - Do some basic semantic validation
 - Plan the operation
 - Execute the operation

CrateDB `calculates the shard ID`_ for every row to be inserted when executing
the operation. Insert requests are then grouped and sent to the nodes that hold
each primary shard.

You can reduce the processing overhead by either eliminating the needless
repetition of some steps or by reducing the work needed to be done by one or
more steps.

This section of the guide will show you how.

.. rubric:: Table of contents

.. toctree::
   :maxdepth: 2

   methods
   bulk
   parallel
   tuning
   testing

.. _Abstract Syntax Tree: https://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _calculates the shard ID: https://crate.io/docs/crate/reference/en/latest/sql/ddl/sharding.html#routing
