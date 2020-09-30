.. meta::
    :last-reviewed: 2020-08-21

.. _debian:

===============================
Run CrateDB on Debian GNU/Linux
===============================

CrateDB actively maintains packages for the following Debian versions:

- `Buster`_ (10.x)
- `Stretch`_ (9.x)
- `Jessie`_ (8.x) (legacy)
- `Wheezy`_ (7.x) (legacy)

.. CAUTION::

    Packages for distributions marked as *legacy* are not actively maintained
    and no longer receive updates.

This document will walk you through the process of installing and configuring
the CrateDB Debian package.

.. NOTE::

   This document targets production deployments.

   If you're just getting started with CrateDB, we also provide a `one-step
   Linux installer`_ .

.. _one-step Linux installer: https://crate.io/docs/crate/getting-started/en/latest/install-run/special/linux.html

.. rubric:: Table of contents

.. contents::
   :local:

Configure Apt
=============

Firstly, you will need to upgrade `Apt`_ (the Debian package manager) with HTTPS
support, like so:

.. _Apt: https://wiki.debian.org/Apt

.. code-block:: sh

   sh$ sudo apt-get install apt-transport-https

After that, you will need to download the CrateDB GPG key:

.. code-block:: sh

   sh$ wget https://cdn.crate.io/downloads/apt/DEB-GPG-KEY-crate

And then, so that Apt trusts the CrateDB repository, add the key:

.. code-block:: sh

   sh$ sudo apt-key add DEB-GPG-KEY-crate

CrateDB provides a stable and a testing release channel. At this point, you
should select which one you wish to use.

Create an Apt configuration file, like so:

.. code-block:: sh

   sh$ sudo touch /etc/apt/sources.list.d/crate-CHANNEL.list

Here, replace ``CHANNEL`` with ``stable`` or ``testing``, depending on which
release channel you plan to use.

Then, edit it, and add the following:

.. code-block:: text

   deb https://cdn.crate.io/downloads/apt/CHANNEL/ CODENAME main
   deb-src https://cdn.crate.io/downloads/apt/CHANNEL/ CODENAME main

Here, replace ``CHANNEL`` as above, and then, additionally, replace
``CODENAME`` with the codename of your distribution (e.g., ``buster``,
``stretch``, ``jessie``, or ``wheezy``)

Once that is done, update Apt:

.. code-block:: sh

   sh$ sudo apt-get update

You should see a success message. This indicates that the CrateDB release
channel is correctly configured and the ``crate`` package has been registered
locally.


Install CrateDB
===============

With everything set up, you can install CrateDB, like so:

.. code-block:: sh

   sh$ sudo apt-get install crate

After the installation is finished, the ``crate`` service should be
up-and-running.

You should be able to access it by visiting::

  http://localhost:4200/

.. SEEALSO::

   If you're new to CrateDB, check out our our `first use`_ documentation.

.. _first use: https://crate.io/docs/crate/getting-started/en/latest/first-use/index.html

Controlling CrateDB
===================

With Debian Jessie (8.x) and above, you can control the ``crate`` service like
so:

.. code-block:: sh

    sh$ sudo systemctl COMMAND crate

Here, replace ``COMMAND`` with ``start``, ``stop``, ``restart``, ``status`` and
so on.

.. CAUTION::

    Be sure to read the guide to :ref:`rolling upgrades <rolling_upgrade>` and
    :ref:`full restart upgrades <full_restart_upgrade>` before attempting to
    upgrade a running cluster.

Configuration
=============

Configuration files
-------------------

The main CrateDB `configuration files`_ are located in the ``/etc/crate``
directory.

Environment
-----------

The CrateDB startup script `sources`_ `environment variables`_ from the
``/etc/default/crate`` file.

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

     sh$ dpkg-query -L crate

If you want to deviate from the way that the ``crate`` package integrates with
your system, we recommend that you go with a `basic tarball installation`_.


.. _basic tarball installation: https://crate.io/docs/crate/getting-started/en/latest/install-run/basic.html
.. _Buster: https://www.debian.org/releases/buster/
.. _configuration files: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _environment variables: https://crate.io/docs/crate/reference/en/latest/config/environment.html
.. _Jessie: https://www.debian.org/releases/jessie/
.. _sources: https://en.wikipedia.org/wiki/Source_(command)
.. _Stretch: https://www.debian.org/releases/stretch/
.. _Wheezy: https://www.debian.org/releases/wheezy/

