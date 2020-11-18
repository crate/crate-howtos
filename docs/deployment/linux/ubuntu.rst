.. _ubuntu:

=====================
Run CrateDB on Ubuntu
=====================

CrateDB maintains packages for the following versions:

- `Ubuntu 20.04 LTS`_ (Focal Fossa)
- `Ubuntu 18.04.5 LTS`_ (Bionic Beaver)
- `Ubuntu 16.04.7 LTS`_ (Xenial Xerus)
- `Ubuntu 14.04.6`_ (Trusty Tahr)

This guide will show you how to install, control, and configure a single-node
CrateDB on a local Ubuntu system.


Prerequisites
=============

CrateDB requires a `Java virtual machine`_ (JVM) to run.

CrateDB versions 4.2+ include a JVM and do not require a separate Java
installation. You can skip to :ref:`install CrateDB`.

Earlier CrateDB versions require Java 11 to be installed. To run CrateDB on
Ubuntu releases older than 18.04, you need to install Java from a third-party
repository. This can be done by adding the `OpenJDK`_ PPA (Personal Package
Archive):

.. code-block:: sh

   sh$ sudo add-apt-repository ppa:openjdk-r/ppa
   sh$ sudo apt update
   sh$ sudo apt install -y openjdk-11-jre-headless


.. _Install CrateDB:

Install CrateDB
===============

You need to configure `Apt`_ (the package manager) to trust and to add the
CrateDB repositories:

.. code-block:: sh

   # Download the CrateDB GPG key
   sh$ wget https://cdn.crate.io/downloads/deb/DEB-GPG-KEY-crate

   # Add the key to Apt
   sh$ sudo apt-key add DEB-GPG-KEY-crate

   # Add CrateDB repositories to Apt
   # `lsb_release -cs` returns the codename of your OS
   sh$ sudo add-apt-repository "deb https://cdn.crate.io/downloads/deb/stable/ $(lsb_release -cs) main"


.. NOTE::

   CrateDB provides a *stable release* and a *testing release* channel. To use
   the testing channel, replace ``stable`` with ``testing`` in the command
   above. You can read more about our `release workflow`_.


Now update Apt:

.. code-block:: sh

   sh$ sudo apt update

You should see a success message. This indicates that the CrateDB release
channel is correctly configured and the crate package has been registered
locally.

You can now install CrateDB:

.. code-block:: sh

   sh$ sudo apt install crate

After the installation is finished, the ``crate`` service should be
up and running. You should be able to access it from your local machine by
visiting::

  http://localhost:4200/

.. CAUTION::
   When you install via Apt, CrateDB automatically starts as a single-node
   cluster and you won't be able to add additional nodes. In order to form a
   multi-node cluster, you will need to remove the cluster state after
   changing the configuration.


Control CrateDB
===============

With `Ubuntu 16.04.7 LTS`_ and above, you can control the ``crate`` service
with the `systemctl` utility:

.. code-block:: sh

   sh$ sudo systemctl COMMAND crate


With `Ubuntu 14.04.6`_, you should use the `service` command:

.. code-block:: sh

   sh$ sudo service crate COMMAND


In both instances, replace ``COMMAND`` with ``start``, ``stop``, ``restart``,
``status``, etc.

.. CAUTION::

    Be sure to read the guide to :ref:`rolling upgrades <rolling_upgrade>` and
    :ref:`full restart upgrades <full_restart_upgrade>` before attempting to
    upgrade a running cluster.


Configure CrateDB
=================

In order to configure CrateDB, take note of the configuration file
location and the available environment variables.


Configuration files
-------------------

The main CrateDB `configuration files`_ are located in the ``/etc/crate``
directory.


Environment variables
---------------------

The CrateDB startup script `sources`_ `environment variables`_ from the
``/etc/default/crate`` file. Here is an example:

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
your system, you can do a `basic tarball installation`_.


.. _Apt: https://wiki.debian.org/Apt
.. _basic tarball installation: https://crate.io/docs/crate/tutorials/en/latest/install-run/basic.html
.. _configuration files: https://crate.io/docs/crate/reference/en/latest/config/index.html
.. _environment variables: https://crate.io/docs/crate/reference/en/latest/config/environment.html
.. _first use: https://crate.io/docs/crate/tutorials/en/latest/first-use.html
.. _Java virtual machine: https://en.wikipedia.org/wiki/Java_virtual_machine
.. _OpenJDK: https://launchpad.net/~openjdk-r/+archive/ubuntu/ppa
.. _release workflow: https://github.com/crate/crate/blob/master/devs/docs/release.rst
.. _sources: https://en.wikipedia.org/wiki/Source_(command)
.. _Ubuntu 14.04.6: https://wiki.ubuntu.com/TrustyTahr/ReleaseNotes
.. _Ubuntu 16.04.7 LTS: https://wiki.ubuntu.com/XenialXerus/ReleaseNotes
.. _Ubuntu 18.04.5 LTS: https://wiki.ubuntu.com/BionicBeaver/ReleaseNotes
.. _Ubuntu 20.04 LTS: https://wiki.ubuntu.com/FocalFossa/ReleaseNotes
