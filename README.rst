**********
judo-dance
**********

.. image:: https://github.com/mristin/judo-dance/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mristin/judo-dance/actions/workflows/ci.yml
    :alt: Continuous integration

Practice judo techniques using a dancing pad.

Installation
============
Make sure you have Python installed on your system.

Create a virtual environment on your system:

.. code-block::

    python -m venv venv

Activate it (on Windows):

.. code-block::

    venv\Scripts\activate

... or on Mac/Linux:

.. code-block::

    source venv/bin/activate

Download the Judo Dance from the `Releases`_.

.. _Releases: https://github.com/mristin/judo-dance/releases

Install the Judo Dance (please adapt the version to the one you downloaded):

.. code-block::

    pip3 install judo-dance-0.0.1.tar.gz

Running
=======
You need to connect the dance mat *before* starting the game.

In the activated virtual environment, just run the Judo Dance with a command:

.. code-block::

    judo-dance

If you have multiple joysticks attached, the first joystick is automatically selected, and assumed to be the dance mat.

If the first joystick does not correspond to your dance mat, list the available joysticks with:

.. code-block::

    judo-dance --list_joysticks

You will see the names and unique IDs (GUIDs) of your joysticks.
Select the joystick that you wish by providing its GUI.
For example:

.. code-block::

    judo-dance -joystick 03000000790000001100000000000000

Which dance mat to use?
=======================
We used an unbranded dance mat which you can order, say, from Amazon:
https://www.amazon.com/OSTENT-Non-Slip-Dancing-Dance-Compatible-PC/dp/B00FJ2KT8M

Please let us know by `creating an issue`_ if you tested the game with other mats!

.. _creating an issue: https://github.com/mristin/judo-dance/issues/new

Acknowledgments
===============
The pictures illustrating the techniques are taken from the book we use for the exams.
I do not have the exact book title at hand, but will list it here ASAP.
The copyright belongs to the original authors.
