# PLC - PlasmaLabControl (Python3)

PLC is a software package to control the experiment setup of Plasmalab.

This is a reborn in Python3.

## What's there and what we need:

What's there:
 * many controlling and measuring boxes
   (digital controller, camera, ...)

What we need:
 * software component for every box (IO communication, logging)
 * one software component for controlling (human interface)

What was there:
 * stubs of software for some boxes


## Software Concept:

Many processes with threads communicating over TCP (socket communication)

 * flexible
 * every process can run on own cpu core (automatically or manually)
 * threading prevents unnecessary blockings of the whole system
   while IO communication

 * every process can run on different boxes/computers

   * small processes can go to own boxes in future
   * heavy processes can get their own computers in future
   * controlling interface (human interface) can run on separated location
     (e. g. near the scientist and not near the experiment setup)

   * living in the cloud, e. g.:

     * experiment setup on the A300-ZERO-G (or ISS)
     * logging somewhere in Bordeaux (or Garching)
     * controlling from the Dune of Pyla (or Ringberg)

 * iff running on one Linux system (computer):

   * loopback interface is fast
   * kernel can do the load sharing


## Implementation and Development:

 * Python3
   (at the moment also C++; as far as possible this will be changed in future)

 * popular and suitable operating system: UNIX (Linux, MacOS)


## Human Interface:

 * GUI

   * Tkinter (Tcl/Tk)
   * mostly platform indepent
     (at the moment some controlling parts are integrated;
     and therefore only complete funtionable on POSIX systems;
     this will be changend in near future)

 * config files

   * style of RFC 822

     * mostly human readable
     * platform indepent

 * Batch Controlling:

   * list of setpoints in a config file, which can be loaded and set in the GUI


## Server Components:

For every controlling and measuring box we write some components:
(at the moment heavy development)

 * server program

   * IO to the device
   * logging
   * socket communication for controlling

 * client program (for debugging)

   * human interface (at the moment only GUI)
   * socket communication with the server program

 * integration of a useful API in the human interface GUI

## Other Parts:

plc contains some extra tools for viewing/analysing the measurements.
For example:

 * rawmovieviewer.py
   (player for the img-files (PAM format))

   * quick viewing of the measured/recorded movies

 * rawmovies2recordings.py
   (converts img-files (PAM format) to zip-archives with png graphics)

   * img-files in the PAM format are large and structured to 1 GB files
   * resulting zip-archives are smaller and
     structured in recordings (parabolas)

 * plc_viewer.py
   (viewer of the movies and other measurements)

   * assignment of the frames to other measurements

## Copyright + License
===================
Author: Daniel Mohr.

License: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007

Copyright (C) 2012, 2013, 2014 Daniel Mohr and PlasmaLab (FKZ 50WP0700 and FKZ 50WM1401) and Max-Planck-Institut fuer extraterrestrische Physik, Giessenbachstrasse, D-85740 Garching and Deutsches Zentrum fuer Luft- und Raumfahrt e. V., D-51170 Koeln
Copyright (C) 2023 Perevoshchikov Egor
