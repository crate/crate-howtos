.. meta::
    :last-reviewed: 2020-07-09

.. _ubuntu:

=====================
Run CrateDB on Ubuntu
=====================

CrateDB maintains packages for the following Ubuntu versions:

- `Focal Fossa`_ (20.04)
- `Bionic Beaver`_ (18.04)
- `Xenial Xerus`_ (16.04)
- `Trusty Tahr`_ (14.04)

.. rubric:: Table of contents

.. contents::
   :local:


Java
====

CrateDB requires a `Java virtual machine`_ (JVM) to run.

CrateDB versions 4.2 and above include a JVM and do not require a separate
installation.

Earlier versions require Java 11 to be installed.

To run CrateDB on Ubuntu releases older than 18.04, you will need to install
Java from a third-party repository. This can be done by adding the `OpenJDK`_
PPA::

    sh$ sudo add-apt-repository ppa:openjdk-r/ppa
    sh$ sudo apt-get update
    sh$ sudo apt-get install -y openjdk-11-jre-headless


Configure Apt
=============

Firstly, you will need to configure `Apt`_ (the Ubuntu package manager) to trust
the CrateDB repository.

.. _Apt: https://wiki.debian.org/Apt

Download the CrateDB GPG key:

.. code-block:: sh

   sh$ wget https://cdn.crate.io/downloads/deb/DEB-GPG-KEY-crate

And then add the key to Apt:

.. code-block:: sh

   sh$ sudo apt-key add DEB-GPG-KEY-crate

CrateDB provides a stable release and a testing release channel. At this point,
you should select which one you wish to use.

Create an Apt configuration file, like so:

.. code-block:: sh

   sh$ sudo touch /etc/apt/sources.list.d/crate-CHANNEL.list

Here, replace ``CHANNEL`` with ``stable`` or ``testing``, depending on which
type of release channel you plan to use.

Then, edit it, and add the following:

.. code-block:: text

   deb https://cdn.crate.io/downloads/deb/CHANNEL/ CODENAME main

Here, replace ``CHANNEL`` as above, and then, additionally, replace
``CODENAME`` with the codename of your distribution, which can be round by
running:

.. code-block:: sh

   sh$ source /etc/os-release && echo $UBUNTU_CODENAME

Once that is done, update Apt:

.. code-block:: sh

   sh$ sudo apt-get update

You should see a success message. This indicates that the CrateDB release
channel is correctly configured and the ``crate`` package has been registered
locally.

You can now install CrateDB.


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


Control CrateDB
================

With Xenial Xerus (15.04) and above, you can control the ``crate`` service like
so:

.. code-block:: sh

   sh$ sudo systemctl COMMAND crate

With Trusty Tahr (14.04), you should use:

.. code-block:: sh

   sh$ sudo service crate COMMAND

In both instances, replace ``COMMAND`` with ``start``, ``stop``, ``restart``,
``status``, etc.

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

.. _basic tarball installation: https://crate.io/docs/crate/tutorials/en/latest/getting-started/install-run/basic.html
.. _Bionic Beaver: https://wiki.ubuntu.com/BionicBeaver/ReleaseNotes
.. _configuration files: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _environment variables: https://crate.io/docs/crate/reference/en/latest/config/environment.html
.. _first use: https://crate.io/docs/crate/getting-started/en/latest/first-use/index.html
.. _Focal Fossa: https://wiki.ubuntu.com/FocalFossa/ReleaseNotes
.. _Java virtual machine: https://en.wikipedia.org/wiki/Java_virtual_machine
.. _OpenJDK: https://launchpad.net/~openjdk-r/+archive/ubuntu/ppa
.. _sources: https://en.wikipedia.org/wiki/Source_(command)
.. _Trusty Tahr: https://wiki.ubuntu.com/TrustyTahr/ReleaseNotes
.. _Xenial Xerus: https://wiki.ubuntu.com/XenialXerus/ReleaseNotes
