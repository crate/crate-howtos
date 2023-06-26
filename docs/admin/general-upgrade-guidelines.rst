.. highlight:: sh

.. _general_upgrade_guidelines:

==========================
General upgrade guidelines
==========================

Before kicking off an upgrade, there is a set of best practices to ensure the best outcome. Below you may find the five fundamental steps to prepare for an upgrade.

.. NOTE::

   This is not an exhaustive list, so you should consider your organization's specific needs and incorporate any additional steps or considerations that are relevant to your environment.

Upgrade planning
================

Acknowledge breaking changes
-----------------------------

Review the `release notes`_ and documentation for the target version to understand any potential impact on existing functionality. 
In case of a minor version upgrade, you should consider the intermediate versions. For example, when upgrading from 5.1 to 5.3, besides reviewing 5.3 release notes, the recommendation is to check for version 5.2 as well.

Set up a test environment
-------------------------

Create a test environment that closely resembles your production environment, including the same CrateDB version, hardware, and network configuration. Populate the test environment with representative data and perform thorough testing to ensure compatibility and functionality, including functional and non-functional testing.


Back up and plan recovery
-------------------------

Perform a cluster-wide backup of your production CrateDB and ensure you have a reliable recovery mechanism in place. Read more in the `snapshots`_ documentation. Once the backup is complete, validate it to ensure its usability.

For the newly written records, you should consider using a mechanism to queue them (e.g. message queue), so these messages can be replayed if needed.

.. WARNING::
   
   Before starting the upgrade process, ensure no backup processes are triggered, so disable any scheduled backup.

Define a rollback plan
-----------------------

The rollback plan may vary depending on the specific infrastructure and upgrade process in use. It is also essential to adapt this outline to your organization's specific needs and incorporate any additional steps or considerations that are relevant to your environment. A set of steps to serve as an example is listed below:

* **Identify the issue** Determine the specific problem that occurred during the upgrade. This could be related to data corruption, performance degradation, application errors, or any other issue that affects the normal functioning of CrateDB.

* **Communicate the situation** Notify all relevant stakeholders, including individuals involved in the upgrade process. Clearly explain the problem and the decision to initiate a rollback.

* **Assess impact** Identify if there are any potential risks to the system's stability, security, or performance.

* **Restore from backup** Restore the recently created backup and replay the latest messages from the message queue to reestablish the CrateDB cluster data.

* **Perform data validation** Once the backup has been restored, conduct a thorough data validation process to ensure the integrity of the CrateDB Cluster. Verify that all critical data is intact and accurate.

* **Evaluate the failed upgrade attempt** Assess what went wrong during the upgrade process. Identify any misconfigurations, errors in scripts, or other factors that contributed to the failure. This analysis will help prevent similar issues in future upgrade attempts.

* **Share insights** Communicate any findings and the defined plan to retry the upgrade.



Upgrade Execution
=================

Choose the upgrade strategy below that works best for your scenario.

- :ref:`rolling_upgrade` 

- :ref:`full_restart_upgrade`


.. _release notes: https://crate.io/docs/crate/reference/en/latest/appendices/release-notes/index.html
.. _snapshots: https://crate.io/docs/crate/reference/en/latest/admin/snapshots.html