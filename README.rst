**********
Judo Dance
**********

.. image:: https://github.com/mristin/judo-dance-desktop/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mristin/judo-dance-desktop/actions/workflows/ci.yml
    :alt: Continuous integration

Practice judo techniques using a dancing pad.

Installation
============
Download and unzip a version of the game from the `Releases`_.

.. _Releases: https://github.com/mristin/judo-dance-desktop/releases

Running
=======
You need to connect the dance mat *before* starting the game.

Run ``judo-dance.exe`` (in the directory where you unzipped the game).

If you have multiple joysticks attached, the first joystick is automatically selected, and assumed to be the dance mat.

If the first joystick does not correspond to your dance mat, list the available joysticks with the following command in the command prompt:

.. code-block::

    judo-dance.exe --list_joysticks

You will see the names and unique IDs (GUIDs) of your joysticks.
Select the joystick that you wish by providing its GUI.
For example:

.. code-block::

    judo-dance.exe -joystick 03000000790000001100000000000000

Which dance mat to use?
=======================
We used an unbranded dance mat which you can order, say, from Amazon:
https://www.amazon.com/OSTENT-Non-Slip-Dancing-Dance-Compatible-PC/dp/B00FJ2KT8M

Please let us know by `creating an issue`_ if you tested the game with other mats!

.. _creating an issue: https://github.com/mristin/judo-dance-desktop/issues/new
