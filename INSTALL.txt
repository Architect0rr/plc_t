===============================
INSTALL: plc - PlasmaLabControl
===============================

:Version: 2014-07-22
:Author: Daniel Mohr
:Email: mohr@mpe.mpg.de, daniel.mohr@dlr.de

.. contents::

.. footer::

   ###Page### / ###Total###

INSTALL: plc - PlasmaLabControl
+++++++++++++++++++++++++++++++

info
====

before you install
==================

Modules
-------

plc needs the following modules (most of them are standard and already
in your python installation from a package management)

 * argparse
 * ConfigParser
 * cPickle
 * cStringIO
 * csv
 * datetime
 * distutils.core
 * errno
 * fnmatch
 * Image
 * ImageDraw
 * ImageTk
 * logging
 * logging.handlers
 * math
 * matplotlib
 * matplotlib.pyplot
 * modulefinder
 * numpy
 * os
 * os.path
 * PIL.ImageOps
 * pydc1394
 * Queue
 * random
 * re
 * serial
 * signal
 * SimpleHTTPServer
 * socket
 * SocketServer
 * string
 * struct
 * subprocess
 * sys
 * tarfile
 * tempfile
 * threading
 * time
 * tkFileDialog
 * Tkinter
 * tkMessageBox
 * ttk
 * types
 * usb
 * zipfile

and the own modules plc_gui and plc_tools which comes with this
package.

You can also asked the installation routine/script::

  python setup.py --help
  python setup.py --requires

There is also a small extra command to check for availability of
necessary modules::

  python setup.py check_modules

If you want to use this complete software you should have no modules
which are not available.

Much more information you get from the following small extra command
by using the modulefinder::

  python setup.py check_modules_modulefinder

It is normal that there are many missing modules reported. Please look
at the datails.


Python3
-------
If you use Python3, you must convert to Python3 via 2to3::

  tar xzf plc-*.tar.*
  cd plc-*/
  2to3 -w .

But keep in mind to have all modules in Python3.

2013-02-04: At the moment Python Imaging Library (PIL)
http://www.pythonware.com/products/pil/
is not available for Python3.


Python 2.7 on Mac
-----------------

To install Python 2.7 on am Mac, you can use fink package manager. The
following lines will install what you need::

  fink install python27 pyserial-py27 pil-py27

This works on fink 0.34.4. You can check, if Python 2.7 is avaliable using::

  fink list | grep python27


install
=======
global-install
--------------
To install this software global to / the following steps are to perform::

  tar xzf plc-*.tar.*
  cd plc-*/
  python setup.py install


home-install
------------
To install this software to your $HOME the following steps are to perform::

  tar xzf plc-*.tar.*
  cd plc-*/
  python setup.py install --home=~


hints
=====
* Keep in mind to have the right pathes.

  For the above installation to $HOME the software installs in::

    ~/bin
    ~/lib/python

  Please make sure to have these pathes in $PATH and $PYTHONPATH, respectively.
  For example::

    export PATH=$PATH:~/bin
    export PYTHONPATH=~/lib/python

* Keep in mind to have access to the devices of the control boxes and
  cameras. For example udev can help you.

* Additional Software: PyUSB

  We need PyUSB 1.x from: http://sourceforge.net/apps/trac/pyusb/

  For Ubuntu 12.04 (precise) you can find it in: https://launchpad.net/~cwayne18/+archive/fitbit

  PyUSB is used for the G-sensor.

* Additional Software: pydc1394

  You can find pydc1394 on https://launchpad.net/pydc1394

  You can get your branch to install by::

      mkdir ~/pydc1394
      cd ~/pydc1394
      bzr branch http://bazaar.launchpad.net/~sirver/pydc1394/trunk

  Like typical python software you can install by::

      cd ~/pydc1394/trunk/
      python setup.py install

  Or to install only in your home-directory type::

      cd ~/pydc1394/trunk/
      python setup.py install --home=~

  pydc1394 is used for the cameras. pydc1394 needs libdc1394 and numpy.
  Both are in many package management systems.

* For Linux Mint Debian Edition 201204 XFCE you need to install the following
  packages from the package management system:

    * python-tk
    * python-imaging-tk
    * python-matplotlib

  Useful packages are:

    * coriander
    * python-scipy

  You also need the above mentioned software pydc1394 and pyusb.

* For Fedora 18 you need to install the following packages from the
  package management system:

    * libdc1394
    * numpy
    * pyserial
    * python-imaging
    * python-imaging-tk
    * tkinter

  Useful packages for Fedora 18 are:

    * coriander
    * scipy

  You also need the above mentioned software pydc1394 and pyusb.

  But the camera is not working in plc.py. You have to use
  camer_client.py instead.

* For Ubuntu 13.04 "Raring Ringtail" you need to install the following
  packages from the package management system:

    * python-numpy
    * python-imaging-tk
    * python-matplotlib

  Useful packages are:

    * coriander
    * python-scipy

* For Ubuntu 14.04 "Trusty Tahr" you need to install the following
  packages from the package management system:

    * python-numpy
    * python-pil.imagetk
    * python-matplotlib
    * libdc1394-22-dev

  Useful packages are:

    * coriander
    * python-scipy
    * librecad

after install
=============
Now in your chosen pathes you have the python module

 * plc_gui
 * plc_tools

and the scripts

 * plc.py
 * plc_viewer.py
 * digital_controller_server.py
 * digital_controller_client.py
 * multi_purpose_controller_server.py
 * multi_purpose_controller_client.py
 * camera_server.py
 * camera_client.py
 * acceleration_sensor_server.py
 * acceleration_sensor_client.py
 * acceleration_sensor_logger.py
 * pressure_mks_651_server.py
 * pressure_mks_651_client.py
 * pressure_mks_900_server.py
 * pressure_mks_900_client.py
 * check_real_time_difference.py
 * environment_sensor_5_logger.py
 * rawmovie2pngs.py
 * rawmovie2tiff.py
 * rawmovies2recordings.py
 * rawmovieviewer.py
 * translation_stage_scan.py
 * trigger.py
 * and many other ones in this development status.

Normally it should be enough for you to use "plc.py". On your console
you can start::

 plc.py -h
