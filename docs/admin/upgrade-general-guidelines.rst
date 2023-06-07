.. highlight:: sh

.. _upgrade_general_guidelines:

==============================
Upgrade general guidelines
==============================

Before kicking off an upgrade, it is recommended to follow these guidelines to prepare for it and ensure the best outcome. Below you may find the five fundamental steps to achieve that.


Acknowledge breaking changes
-----------------------------

Review the `release notes`_ and documentation for the target version to understand the new features, bug fixes, and potential impact on existing functionality. 

Setup a test environment
------------------------

Create a test environment that closely resembles your production environment, including the same database version, hardware, and network configuration. Populate the test environment with representative data and perform thorough testing to ensure compatibility and functionality.


Back up and plan recovery
-------------------------

Perform a full backup of your production database and ensure you have a reliable recovery mechanism in place, read more in the `snapshots`_ documentation. Once the backup is complete, validate it to ensure its integrity and usability.

For the newly written records, it is recommended to use a mechanism to queue them (e.g. message queue).

.. WARNING::
   
   Before starting the actual upgrade process, ensure no back up processes are triggered, so unable any scheduled backup.

Define a rollback plan
-----------------------

The rollback plan may vary depending on the specific infrastructure and upgrade process in use. It is essential to adapt this outline to your organization's specific needs and incorporate any additional steps or considerations that are relevant to your environment. A set of steps to serve as an example is listed below:

- Identify the issue

- Communicate the situation

- Assess impact

- Restore from backup

- Perform data validation

- Evaluate the failed upgrade attempt

- Share insights


Next step
---------

Choose the upgrade strategy that works best for your scenario.

- :ref:`rolling_upgrade` 

- :ref:`full_restart_upgrade`


.. _release notes: https://crate.io/docs/crate/reference/en/5.3/appendices/release-notes/index.html
.. _snapshots: https://crate.io/docs/crate/reference/en/latest/admin/snapshots.html