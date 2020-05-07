.. _red-hat:

============================
Run CrateDB on Red Hat Linux
============================

CrateDB maintains the official RPM repositories for:

- `Red Hat Linux 7`_

.. _Red Hat Linux 7: https://www.redhat.com/en/resources/whats-new-red-hat-enterprise-linux-7

Both of these work with RedHat Enterprise Linux, CentOS, and Scientific Linux.

.. rubric:: Table of contents

.. contents::
   :local:

Configure YUM
=============

All CrateDB packages are signed with GPG.

To get started, you must import the CrateDB public key, like so:

.. code-block:: sh

   sh$ sudo rpm --import https://cdn.crate.io/downloads/yum/RPM-GPG-KEY-crate

You must then install the CrateDB repository definition.

For Red Hat Linux 7, run:

.. code-block:: sh

   sh$ sudo rpm -Uvh https://cdn.crate.io/downloads/yum/7/noarch/crate-release-7.0-1.noarch.rpm

The above commands will create the ``/etc/yum.repos.d/crate.repo``
configuration file.

CrateDB provides a stable and a testing release channel. At this point, you
should select which one you wish to use.

By default, `YUM`_ (Red Hat's package manager) will use the stable repository.
This is because the testing repository's configuration marks it as disabled.

.. _YUM: https://access.redhat.com/solutions/9934

If you would like to enable to testing repository, open the ``crate.repo`` file
and set ``enabled=1`` under the ``[crate-testing]`` section.

Install CrateDB
===============

With everything set up, you can install CrateDB, like so:

.. code-block:: sh

   yum install crate

CrateDB is now installed, but not running.

Running and controlling CrateDB
===============================

With Red Hat Linux 7, you can control the ``crate`` service like so:

.. code-block:: sh

   sh$ sudo systemctl COMMAND crate

Here, replace ``COMMAND`` with ``start``, ``stop``, ``restart``, ``status`` and
so on.

After you run the appropriate command with the ``start`` argument, the
``crate`` service should be up-and-running.

You should be able to access it by visiting::

  http://localhost:4200/

.. SEEALSO::

   If you're new to CrateDB, check out our our `first use`_ documentation.

.. _first use: https://crate.io/docs/crate/getting-started/en/latest/first-use/index.html

.. CAUTION::

    Be sure to read the guide to :ref:`rolling upgrades <rolling_upgrade>` and
    :ref:`full restart upgrades <full_restart_upgrade>` before attempting to
    upgrade a running cluster.

Configuration
=============

Configuration files
-------------------

The main CrateDB configuration files are located in the ``/etc/crate``
directory.

Environment
-----------

The CrateDB startup script `sources`_ environment variables from the
``/etc/sysconfig/crate`` file.

.. _sources: https://en.wikipedia.org/wiki/Source_(command)

You can use this mechanism to configure CrateDB.

Here's one example:

.. code-block:: sh

   # Heap Size (defaults to 256m min, 1g max)
   CRATE_HEAP_SIZE=2g

   # Maximum number of open files, defaults to 65535.
   # MAX_OPEN_FILES=65535

   # Maximum locked memory size. Set to "unlimited" if you use the
   # bootstrap.mlockall option in crate.yml. You must also set
   # CRATE_HEAP_SIZE.
   MAX_LOCKED_MEMORY=unlimited

   # Additional Java OPTS
   # CRATE_JAVA_OPTS=

   # Force the JVM to use IPv4 stack
   CRATE_USE_IPV4=true

Customized setups
=================

A full list of package files can be obtained with this command::

     sh$ rpm -ql crate

If you want to deviate from the way that the ``crate`` package integrates with
your system, we recommend that you go with a `basic tarball installation`_.

.. _basic tarball installation: https://crate.io/docs/crate/getting-started/en/latest/install-run/basic.html
