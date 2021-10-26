.. _azure_terraform_setup:

=============================
Running CrateDB via Terraform
=============================

In :ref:`vm_setup`, we elaborated on how to leverage Azure's functionality to set
up a CrateDB cluster.

`Terraform`_ is an infrastructure as code tool, often used as an abstraction
layer on top of a cloud's management APIs. Instead of creating cloud resources
manually, the target state is specified via configuration files which can also
be checked into a version control system. This brings some advantages, such as
but not limited to:

- Reproducibility of deployments, e.g., across different accounts or in case of
  disaster recovery
- Enables common development workflows like code reviews, automated testing, and
  so on
- Better prediction and tracing of infrastructure changes

The `crate-terraform`_ repository provides a predefined configuration template
of various Azure resources to form a CrateDB cluster on Azure (such as VMs,
load balancer, etc). This eliminates the need to manually compose all
required resources and their interactions.

.. CAUTION::

  The provided configuration is meant to be used for development or testing
  purposes and does not aim to fulfil all needs of a productive environment.

Prerequisites
=============

Before configuring the configuration to launch your CrateDB cluster, the
following prerequisites should be fulfilled:

1. The Terraform CLI is installed as per
   `Terraform's installation guide`_
2. The git CLI is installed as per `git's installation guide`_
3. Azure credentials are configured for Terraform. If you already have a
   configured Azure CLI setup, Terraform will reuse this configuration. If not,
   see the `Azure provider`_ documentation on authentication.

Deployment configuration
========================
To parametize the CrateDB Terraform configuration, create a new file ``main.tf``
with the following content:

.. code-block::

  module "cratedb-cluster" {
    source = "github.com/crate/crate-terraform.git/azure"

    # Global configuration items for naming/tagging resources
    config = {
      project_name = "example-project"
      environment  = "test"
      owner        = "Crate.IO"
      team         = "Customer Engineering"

      # Run "az account list-locations" for a full list
      location = "westeurope"
    }

    # CrateDB-specific configuration
    crate = {
      # Java Heap size in GB available to CrateDB
      heap_size_gb = 2

      cluster_name = "crate-cluster"

      # The number of nodes the cluster will consist of
      cluster_size = 2

      # Enables a self-signed SSL certificate
      ssl_enable = true
    }

    # Azure VM specific configuration
    vm = {
      # The size of the disk storing CrateDB's data directory
      disk_size_gb         = 512
      storage_account_type = "Premium_LRS"
      size                 = "Standard_DS12_v2"

      # Enabling SSH access
      ssh_access = true
      # Username to connect via SSH to the nodes
      user = "cratedb-vmadmin"
    }
  }

  output "cratedb" {
    value     = module.cratedb-cluster
    sensitive = true
  }

The Azure-specific variables need to be adjusted according to your environment:

+--------------------------+--------------------------------------------------------------+----------------------------------+
| Variable                 | Explanation                                                  | How to obtain                    |
+==========================+==============================================================+==================================+
| ``location``             | The geographical region in which to create the Azure         | ``az account list-locations``    |
|                          | resources                                                    |                                  |
+--------------++----------+--------------------------------------------------------------+----------------------------------+
| ``storage_account_type`` | Storage Account Type of the disk containing the CrateDB      | `List of Storage Account Types`_ |
|                          | data directory                                               |                                  |
+--------------------------+--------------------------------------------------------------+----------------------------------+
| ``size``                 | Specifies the size of the VM                                 | ``az vm list-sizes``             |
+--------------------------+--------------------------------------------------------------+----------------------------------+

Execution
=========
Once all variables are configured properly, you can instruct Terraform to list
the resources it is going to create based on the configuration:

.. code-block:: bash

  terraform init

At this point, no resources got created yet. To proceed with executing the shown
plan, apply it:

.. code-block:: bash

  terraform apply

If the execution was successful, a message similar to the one below is shown:

.. code-block:: bash

  Apply complete! Resources: 22 added, 0 changed, 0 destroyed.

  Outputs:

  cratedb = <sensitive>

Terraform internally tracks the state of each resource it manages, including
certain outputs with details on the created Cluster. As those details include
credentials, they are marked as sensitive and not shown in the output above.
To view the output, run:

.. code-block:: bash

  terraform output cratedb

The output variable ``cratedb_application_url`` points to the load balancer with
the port of CrateDB's Admin UI. Opening that URL in your browser should show a
password prompt on which you can authenticate using ``cratedb_username`` and
``cratedb_password``.

Deprovisioning
==============

If the CrateDB cluster is not needed anymore, you can easily instruct Terraform
to destroy all associated resources:

.. code-block:: bash

  terraform destroy

.. CAUTION::

  Destroying the cluster will permanently delete all data stored on it. Use
  :ref:`snapshots <snapshot-restore>` to create a backup on Azure Blob storage
  if needed.

.. _Terraform: https://www.terraform.io
.. _crate-terraform: https://www.github.com/crate/crate-terraform
.. _Terraform's installation guide: https://www.terraform.io/downloads.html
.. _git's installation guide: https://git-scm.com/downloads
.. _Azure provider: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
.. _List of Storage Account Types: https://docs.microsoft.com/en-us/azure/templates/microsoft.compute/virtualmachines?tabs=bicep#manageddiskparameters
