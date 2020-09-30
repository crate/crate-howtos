.. meta::
    :last-reviewed: 2020-09-07

.. _jcmd-docker:

===============================================
Troubleshooting CrateDB on Docker with ``jcmd``
===============================================

You can find a lot of troubleshooting guides for Java applications out there on
the internet that explain how to perform a heap dump, thread dump, and so on.
Since CrateDB is written in Java, these tools can of course also be used to
troubleshoot CrateDB instances in case something goes awry.

Most of these guides, however, explain how to use tools (such as ``jcmd``) on
Java applications running directly as process on the operating system. Fewer of
them cover how to apply ``jcmd`` commands inside a Docker container.

When it comes to troubleshooting the ``crate`` Docker container, things work a
bit differently. This document explains why the 'usual' way to run ``jcmd``
does not work and how to solve it. It does not, however, explain how to analyze
the output (since that is identical to non-containerized applications)!

.. rubric:: Table of contents

.. contents::
   :local:


Introduction
============

``jcmd`` has been the successor of multiple tools (``jstack``, ``jinfo``,
``jmap``) since JDK 8. It can be used to perform various diagnostic tasks on a
running Java application.

.. code-block:: console

   $ /crate/jdk/bin/jcmd -h
   Usage: jcmd <pid | main class> <command ...|PerfCounter.print|-f file>
      or: jcmd -l
      or: jcmd -h

     command must be a valid jcmd command for the selected jvm.
     Use the command "help" to see which commands are available.
     If the pid is 0, commands will be sent to all Java processes.
     The main class argument will be used to match (either partially
     or fully) the class used to start Java.
     If no options are given, lists Java processes (same as -l).

     PerfCounter.print display the counters exposed by this process
     -f  read and execute commands from the file
     -l  list JVM processes on the local machine
     -? -h --help print this help message


Running inside ``crate`` Docker container
=========================================

After starting a ``crate`` Docker container you can also run ``jcmd`` inside
the container.

.. code-block:: console

   $ docker exec -ti b768001196c /bin/bash
   [root@b768001196ce data]# /crate/jdk/bin/jcmd -l
   1 io.crate.bootstrap.CrateDB -Cpath.home=/crate -Cnode.name=debug
   106 jdk.jcmd/sun.tools.jcmd.JCmd -l

However, when trying to run any command, the command fails, even though you run
it as ``root`` with full privileges.

.. code-block:: console

   [root@b768001196ce data]# /crate/jdk/bin/jcmd 1 VM.version
   1:
   com.sun.tools.attach.AttachNotSupportedException: Unable to open socket file /proc/1/root/tmp/.java_pid1: target process 1 doesn't respond within 10500ms or HotSpot VM not loaded
   	at jdk.attach/sun.tools.attach.VirtualMachineImpl.<init>(VirtualMachineImpl.java:100)
   	at jdk.attach/sun.tools.attach.AttachProviderImpl.attachVirtualMachine(AttachProviderImpl.java:58)
   	at jdk.attach/com.sun.tools.attach.VirtualMachine.attach(VirtualMachine.java:207)
   	at jdk.jcmd/sun.tools.jcmd.JCmd.executeCommandForPid(JCmd.java:115)
   	at jdk.jcmd/sun.tools.jcmd.JCmd.main(JCmd.java:99)

The same happens when you try to run it as user ``crate``, which owns the
process:

.. code-block:: console

   [root@b768001196ce data]# su crate -c "/crate/jdk/bin/jcmd 1 VM.version"
   1:
   com.sun.tools.attach.AttachNotSupportedException: Unable to open socket file /proc/1/root/tmp/.java_pid1: target process 1 doesn't respond within 10500ms or HotSpot VM not loaded
   	at jdk.attach/sun.tools.attach.VirtualMachineImpl.<init>(VirtualMachineImpl.java:100)
   	at jdk.attach/sun.tools.attach.AttachProviderImpl.attachVirtualMachine(AttachProviderImpl.java:58)
   	at jdk.attach/com.sun.tools.attach.VirtualMachine.attach(VirtualMachine.java:207)
   	at jdk.jcmd/sun.tools.jcmd.JCmd.executeCommandForPid(JCmd.java:115)
   	at jdk.jcmd/sun.tools.jcmd.JCmd.main(JCmd.java:99)

On a different note: when looking at the Docker logs of the ``crate``
container, you can see that when trying to run the ``jcmd`` command, the
CrateDB instance logs a full thread dump.


What is the problem then?
----------------------------

The entrypoint_ of the ``crate`` Docker image ensures that the CrateDB Java
process runs as user ``crate``, since **CrateDB must be run as a non-root
user**.

This is done by ``chroot`` ing with user ``crate`` (``chroot --userspec=1000 /
"$@"``), because this does not spawn an additional process for changing the
user - unlike ``su crate -c "$@"``, where ``su`` would result in the process
with PID ``1`` and the crate command would be a child-process with a different
PID. This is not what one wants in a Docker container, where the application
must (?) run as PID 1.

With that knowledge in mind, you can use ``chroot`` to execute the ``jcmd``
command as well.

.. code-block:: console

   [root@b768001196ce data]# chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 VM.version
   1:
   OpenJDK 64-Bit Server VM version 13.0.1+9
   JDK 13.0.1

``jcmd <PID> help`` lists all available commands that you can now start using
for troubleshooting CrateDB inside the Docker container.

.. code-block:: console

   [root@b768001196ce data]# chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 help
   1:
   The following commands are available:
   Compiler.CodeHeap_Analytics
   Compiler.codecache
   Compiler.codelist
   Compiler.directives_add
   Compiler.directives_clear
   Compiler.directives_print
   Compiler.directives_remove
   Compiler.queue
   GC.class_histogram
   GC.class_stats
   GC.finalizer_info
   GC.heap_dump
   GC.heap_info
   GC.run
   GC.run_finalization
   JFR.check
   JFR.configure
   JFR.dump
   JFR.start
   JFR.stop
   JVMTI.agent_load
   JVMTI.data_dump
   ManagementAgent.start
   ManagementAgent.start_local
   ManagementAgent.status
   ManagementAgent.stop
   Thread.print
   VM.class_hierarchy
   VM.classloader_stats
   VM.classloaders
   VM.command_line
   VM.dynlibs
   VM.events
   VM.flags
   VM.info
   VM.log
   VM.metaspace
   VM.native_memory
   VM.print_touched_methods
   VM.set_flag
   VM.stringtable
   VM.symboltable
   VM.system_properties
   VM.systemdictionary
   VM.uptime
   VM.version
   help

   For more information about a specific command use 'help <command>'.

To execute one of these commands from outside of the Docker container without
explicitly attaching to it, you can combine the ``docker exec`` command with the
``jcmd`` command. This would look like so:

.. code-block:: console

   $ docker exec -ti <ID> /bin/bash -c "chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 <CMD>"

For example, running ``GC.heap_info`` on Docker container with ID
``b768001196ce``:

.. code-block:: console

   $ docker exec -ti b768001196ce /bin/bash -c "chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 GC.heap_info"
   1:
    garbage-first heap   total 524288K, used 129716K [0x00000000e0000000, 0x0000000100000000)
     region size 1024K, 126 young (129024K), 22 survivors (22528K)
    Metaspace       used 57165K, capacity 59755K, committed 60080K, reserved 1099776K
     class space    used 7721K, capacity 8941K, committed 8960K, reserved 1048576K


Troubleshooting Commands
========================


Thread Dump
-----------

:Command: ``jcmd <PID> Thread.print``

Example
.......

.. code-block:: console

   $ docker exec -ti b768001196ce /bin/bash -c "chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 Thread.print"
   1:
   ...


Heap Info
---------

:Command: ``jcmd <PID> GC.heap_info``

Example
.......

.. code-block:: console

   $ docker exec -ti b768001196ce /bin/bash -c "chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 GC.heap_info"
   1:
   ...


Heap Dump
---------

:Command: ``jcmd <PID> GC.heap_dump <PATH>``

Example
.......

.. code-block:: console

   $ docker exec -ti b768001196ce /bin/bash -c "chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 GC.heap_dump /data/crate.hprof"
   1:
   Heap dump file created

.. note::

   The ``<PATH>`` should be a path that resides on a mounted volume, so you can
   access the created heap dump from ouside of the container and the container
   is not "blown up".


Java Flight Recording
---------------------

:Command: ``jcmd <PID> JFR.start name=<NAME> duration=<DURATION> filename=<PATH> settings=profile``

Example
.......

.. code-block:: console

   $ docker exec -ti b768001196ce /bin/bash -c "chroot --userspec=1000 / /crate/jdk/bin/jcmd 1 JFR.start name=recording1 duration=60s filename=/data/recording1.jfr"
   1:
   Started recording 1. The result will be written to:

   /data/recording1.jfr

.. note::

   The ``<PATH>`` should be a path that resides on a mounted volume, so you can
   access the created jfr dump from ouside of the container and the container
   is not "blown up".

These are the most common troubleshooting tasks, but of course there are many
more possibilities to get diagnostic information using the ``jcmd`` command.
You can find more information about the utility at the `jcmd documentation`_.


.. _entrypoint: https://github.com/crate/docker-crate/blob/master/amd64/crate/docker-entrypoint.sh#L19-L22
.. _jcmd documentation: https://docs.oracle.com/javase/8/docs/technotes/guides/troubleshoot/tooldescr006.html#BABEHABG
