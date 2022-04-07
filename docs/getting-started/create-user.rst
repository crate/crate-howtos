.. _create-user:

===========
Create user
===========


------------
Introduction
------------

This part of the documentation sheds some light on the topics of
:ref:`crate-reference:administration_user_management` and
:ref:`crate-reference:administration-privileges`.

CrateDB ships with a superuser account called "``crate``", which has the
privileges to perform any action. However, with the default configuration, this
superuser can only access CrateDB from the local machine CrateDB has been
installed on. If you are trying to connect from another machine, you are
prompted to enter a username and password.

In order to create a user that can be used to authenticate from a remote
machine, first :ref:`install crash <crate-crash:getting-started>` or other
:ref:`crate-clients-tools:index` on the same machine you installed CrateDB on.
Then, connect to CrateDB running on ``localhost``.

While you can also perform the steps outlined below within
:ref:`crate-admin-ui:index` itself, the walkthrough will outline how to do it
using the :ref:`crate-crash:index` on the command line.


-------
Details
-------

Invoke Crash within the terminal of your choice.

.. code-block:: console

   sh$ crash

Add your first user with a secure password to the database:

.. code-block:: psql

   cr> CREATE USER username WITH (password = 'a_secret_password');

Grant all privileges to the newly created user:

.. code-block:: psql

   cr> GRANT ALL PRIVILEGES TO username;

.. image:: _assets/img/create-user.png

Now try navigating to the :ref:`crate-admin-ui:index` in your browser. In the URL
below, please replace ``cratedb.example.org`` with the host name or IP address
of the machine CreateDB is running on and sign in with your newly created user
account::

   http://cratedb.example.org:4200/

You should see something like this:

.. image:: _assets/img/first-use/admin-ui.png


After creating the user and granting all privileges, you should be able to
continue with :ref:`the guided tour <use>` connecting to CrateDB from a remote
machine.
