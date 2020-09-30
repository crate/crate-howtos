.. meta::
    :last-reviewed: 2020-07-01

.. highlight:: sh

.. _bootstrap-checks:

================
Bootstrap checks
================

If you are binding to a network reachable IP address, CrateDB performs a number
of bootstrap checks during startup. These checks examine your setup and will
prevent startup if a problem is detected.

This best practices guide is intended to help you configure your setup so that
CrateDB passes the bootstrap checks and can perform optimally.

If you are binding to the loopback address, the bootstrap checks will not be
run, but it is still a good idea to follow these instructions.

.. TIP::

    If you are using Docker, these checks are dependent on the host system. You
    must configure the host system appropriately if you wish to run CrateDB on
    Docker. Consult the additional documentation on Docker :ref:`resource
    constraints <resource_constraints>` for more information.

.. rubric:: Table of contents

.. contents::
   :local:

System settings
===============

Official packages
-----------------

If you are using one of the official packages, all of the necessary operating
system configuration is handled for you.

Tarball
-------

If you have installed CrateDB from a tarball, you must manually configure your
operating system.

Here's what needs to be configured:

- **File descriptors**
   - Set hard and soft limit to unlimited
- **Memory lock**
   - Set hard and soft limit to unlimited
- **Threads**
   - Set hard and soft limit to 4096 (CrateDB versions < 3.0.0 will also work
     with 2048)
- **Virtual memory**
   - Set hard and soft limit to unlimited (on Linux only)
- **Memory map**
   - Set limit to 262144 (on Linux only)

You might be able to set these limits per process or per user, depending on
your operating system and setup. And for this to take effect, you may also have
to set these limits for the superuser.

Linux
.....

If you're running Linux, you can perform the necessary configuration by
following these instructions.

Edit ``/etc/security/limits.conf`` and configure these lines::

    crate soft nofile unlimited
    crate hard nofile unlimited

    crate soft memlock unlimited
    crate hard memlock unlimited

    crate soft nproc 4096
    crate hard nproc 4096

    crate soft as unlimited
    crate hard as unlimited

Here, ``crate`` is the user that runs the CrateDB daemon.

Edit ``/etc/sysctl.conf`` and configure::

    vm.max_map_count = 262144

To apply this change, run:

.. code-block:: console

    $ sudo sysctl -p

This command will this reload all settings from ``/etc/sysctl.conf``.

.. TIP::

    Alternatively, ``vm.max_map_count`` can be set directly, like so:

    .. code-block:: console

        $ sysctl -w vm.max_map_count=262144

    Note, however, this setting will be reset to the value in
    ``/etc/sysctl.conf`` when your system next boots.

Garbage collection
==================

CrateDB has been tested using the `CMS garbage collector`_ (default up to and
including CrateDB 4.0) and `G1GC`_ (the default with CrateDB 4.1).

`G1GC` can also be used in earlier CrateDB versions, but should only be used in
combination with Java 11 or later.


.. WARNING::

   Other garbage collectors have not been tested with CrateDB and we do not
   support using other GCs in production.

.. _CMS garbage collector: https://docs.oracle.com/javase/8/docs/technotes/guides/vm/gctuning/cms.html
.. _G1GC: https://docs.oracle.com/javase/9/gctuning/garbage-first-garbage-collector.htm
