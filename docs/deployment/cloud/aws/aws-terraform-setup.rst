.. _aws_terraform_setup:

=============================
Running CrateDB via Terraform
=============================

In :ref:`ec2_setup`, we elaborated on how to leverage EC2's functionality to set
up a CrateDB cluster. Here, we will explore how to automate this kind of setup.

`Terraform`_ is an infrastructure as code tool, often used as an abstraction
layer on top of a cloud's management APIs. Instead of creating cloud resources
manually, the target state is specified via configuration files which can also
be managed in a version control system. This brings some advantages, such as but
not limited to:

- Reproducibility of deployments, e.g., across different accounts or in case of
  disaster recovery
- Enables common development workflows like code reviews, automated testing, and
  so on
- Better prediction and tracing of infrastructure changes

The `crate-terraform`_ repository provides a predefined configuration template
of various AWS resources to form a CrateDB cluster on AWS (such as EC2
instances, load balancer, etc). This eliminates the need to manually compose all
required resources and their interactions.

.. SEEALSO::

  Engage with us in the `community post`_ on Terraform deployments for any
  questions or feedback!

.. CAUTION::

  The provided configuration is meant to be used for development or testing
  purposes and does not aim to fulfil all needs of a production environment.

Prerequisites
=============

Before creating the configuration to launch your CrateDB cluster, the following
prerequisites should be fulfilled:

1. The Terraform CLI is installed as per
   `Terraform's installation guide`_
2. The git CLI is installed as per `git's installation guide`_
3. AWS credentials are configured for Terraform. If you already have a
   configured AWS CLI setup, Terraform will reuse this configuration. If not,
   see the `AWS provider`_ documentation on authentication.

Deployment configuration
========================

The CrateDB Terraform configuration consists of a set of variables to customize
your deployment. Create a new file ``main.tf`` with the following content and
adjust variable values as needed:

.. code-block::

  module "cratedb-cluster" {
    source = "github.com/crate/crate-terraform.git/aws"

    # Global configuration items for naming/tagging resources
    config = {
      project_name = "example-project"
      environment  = "test"
      owner        = "Crate.IO"
      team         = "Customer Engineering"
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

    # The disk size in GB to use for CrateDB's data directory
    disk_size_gb = 512

    # The AWS region
    region = "eu-central-1"

    # The VPC to deploy to
    vpc_id = "vpc-1234567"

    # Applicable subnets of the VPC
    subnet_ids = ["subnet-123456", "subnet-123457"]

    # The corresponding availability zones of above subnets
    availability_zones = ["eu-central-1b", "eu-central-1a"]

    # The SSH key pair for EC2 instances
    ssh_keypair = "cratedb-cluster"

    # Enable SSH access to EC2 instances
    ssh_access = true
  }

  output "cratedb" {
    value     = module.cratedb-cluster
    sensitive = true
  }

The AWS-specific variables need to be adjusted according to your environment:

+------------------------+--------------------------------------------------------------+----------------------------------+
| Variable               | Explanation                                                  | How to obtain                    |
+========================+==============================================================+==================================+
| ``region``             | The geographic region in which to create the AWS resources   | `List of available AWS regions`_ |
+------------------------+--------------------------------------------------------------+----------------------------------+
| ``vpc_id``             | The ID of the Virtual Private Cloud (VPC) in which the EC2   | `How to view VPC properties`_    |
|                        | instances will be launched                                   |                                  |
+------------------------+--------------------------------------------------------------+----------------------------------+
| ``subnet_ids``         | Each VPC consists of multiple subnets, typically distributed | `How to view subnet properties`_ |
|                        | across availability zones. Choose the ones you want to       |                                  |
|                        | launch EC2 instances in.                                     |                                  |
+------------------------+--------------------------------------------------------------+----------------------------------+
| ``availability_zones`` | The availability zones of the above subnets.                 | `How to view subnet properties`_ |
|                        | The positions in the ``availability_zones`` array must match |                                  |
|                        | with the corresponding element in ``subnet_ids``.            |                                  |
|                        | In the example above, ``subnet-123456`` is in                |                                  |
|                        | ``eu-central-1b``, and ``subnet-123457`` in                  |                                  |
|                        | ``eu-central-1a``.                                           |                                  |
+------------------------+--------------------------------------------------------------+----------------------------------+
| ``ssh_keypair``        | The EC2 key pair used for SSH access. This must be an        | `How to create EC2 key pairs`_   |
|                        | already existing key pair name.                              |                                  |
+------------------------+--------------------------------------------------------------+----------------------------------+

Execution
=========

Once all variables are configured properly, Terraform needs to be initialized:

.. code-block:: bash

  terraform init

To proceed with executing the creation of resources, apply the configuration.
There will be a final confirmation prompt before any changes are applied to your
AWS account:

.. code-block:: bash

  terraform apply

Once the execution succeeded, a message similar to the one below is shown:

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
  :ref:`snapshots <snapshot-restore>` to create a backup on S3 if needed.

.. _Terraform: https://www.terraform.io
.. _crate-terraform: https://www.github.com/crate/crate-terraform
.. _Terraform's installation guide: https://www.terraform.io/downloads.html
.. _git's installation guide: https://git-scm.com/downloads
.. _AWS provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
.. _List of available AWS regions: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions
.. _How to view VPC properties: https://docs.aws.amazon.com/vpc/latest/userguide/working-with-vpcs.html#view-vpc
.. _How to view subnet properties: https://docs.aws.amazon.com/vpc/latest/userguide/working-with-vpcs.html#view-subnet
.. _How to create EC2 key pairs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair
.. _community post: https://community.crate.io/t/deploying-cratedb-to-the-cloud-via-terraform/849
