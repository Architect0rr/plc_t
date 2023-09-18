=========
CHANGELOG
=========

:Version: 2017-05-30
:Author: Daniel Mohr
:Email: mohr@mpe.mpg.de

.. contents::

.. footer::

   ###Page### / ###Total###

CHANGELOG
+++++++++

This is the changelog for plc -- PlasmaLabControl.

Due to early development status the verion numbers are dates.

plc-2017-05-30.tar.gz
=====================

  * updated documentation and license information

  * updated INSTALL.txt with pckages for Ubuntu 14.04 "Trusty Tahr"

  * bug fix in environment_sensor_5_logger.py
    negative dewpoint/temperature was not accepted

  * corrected human readable time in logfile from time.gmtime() to time.localtime()

  * changed using PIL instead of depricated Image:
    * Image -> PIL.Image
    * ImageDraw -> PIL.ImageDraw
    * ImageEnhance -> PIL.ImageEnhance
    * ImageMath -> PIL.ImageMath
    * ImageTk -> PIL.ImageTk

plc-2014-07-22.tar.gz
=====================

 * enhanced/corrected documentation


plc-2014-??-??.tar.gz
=====================

 * added many things; updated, enhanced and corrected many parts


plc-2013-??-??.tar.gz
=====================

 * added many things; updated, enhanced and corrected many parts


plc-2012-12-??.tar.gz
=====================

 * added small script logs2housekeeping.py

 * enhanced rawmovies2recordings.py to accept bad data, e. g.:

   - log data out of interesting time range
   - bad log data
   - empty rf data



plc-2012-12-05.tar.gz
=====================

 * wrote plc.py comletely new

   - changed file handler from RotatingFileHandler to WatchedFileHandler

   - added tabs alias ttk.Notebook

   - removed some programs:

     + py-console.py
     + Zyflex_RF-Generator.py
     + DodecahedronRF_Gen.py

   - added some programs:

     + camera_client.py
     + digital_controller_client.py
     + multi_purpose_controller_client.py
     + plc_viewer.py
     + rawmovieviewer.py

   - switched to digital_controller_server.py

   - switched to multi_purpose_controller_server.py

   - switched to camera_server.py

   - Because of new digital_controller_server.py,
     multi_purpose_controller_server.py and camera_server.py in the
     background, we need a new default config file.

  * corrected locking feature in camera_server.py

  * corrected locking feature in multi_purpose_controller_server.py

  * set trigger per default in multi_purpose_controller_client.py to on

  * corrected locking feature in digital_controller_server.py

  * set trigger per default in digital_controller_client.py to on

  * The modules fcntl and subprocess are now not needed. But this can
    change in future.

plc-2012-11-22.tar.gz
=====================

 * improved camera_server.py

   - added AOI (area of interest)

   - making it more thread safe by adding some more threading.Lock()'s


 * improved camera_client.py

   - added AOI (area of interest)

   - added histogram

   - create crop function by mouse

   - added scrollbars around the picture

 * improved the documentation plc_manual.rst


plc-2012-11-09.tar.gz
=====================

 * fix in camera_server.py 

   - Set packet size to be evenly divisible by four,
     as described in http://www.alliedvisiontec.com/de/support/knowledge-base.html?tx_nawavtknowledgebase_piList[uid]=58&tx_nawavtknowledgebase_piList[mode]=single

 * improved camera_server.py

 * improved camera_client.py

 * fix digital_controller_server.py

   - Use threading.Lock() by dispenser shaking to disable
     changes while shaking.

   - The time to sleep in shake_dispenser is now definitivly positiv.

 * fix digital_controller_client.py

   - Speeling somewhere.


plc-2012-11-02.tar.gz
=====================

 * improved camera_server.py
 * improved camera_client.py
 * improved acceleration_sensor_logger.py
 * improved multi_purpose_controller_server.py


plc-2012-10-23.tar.gz
=====================

 * improved camera_server.py

   - Using of os.statvfs leads to necessary unix systems. This means the
     camera_server.py will not run under other systems than unix. This
     could be changed by using this feature only on sufficient systems;
     but I see no needfulness for running on other systems.

 * improved camera_client.py

 * added small script acceleration_sensor_logger.py


plc-2012-10-15.tar.gz
=====================

 * added camera_server.py
 * added output of info.txt in rawmovies2recordings.py
 * added camera_client.py


plc-2012-10-10b.tar.gz
======================

 * fixed a bug in rawmovies2recordings.py

   - Different files were always put together in one zip-archiv; now
     this is only done, iff the timestamps of the first and last frame
     is greater 1 second.


plc-2012-10-10a.tar.gz
======================

 * added multi_purpose_controller_server.py
 * added multi_purpose_controller_client.py
 * fixed a bug in plc_viewer.py

   - default value for absolutscale was not correctly handled

 * added commandline flag create_info_graphics to plc_viewer.py

plc-2012-10-05.tar.gz
=====================

 * added digital_controller_server.py
 * added digital_controller_client.py


plc-2012-10-02a.tar.gz
======================

 * bug fix in plc_viewer.py


plc-2012-10-01.tar.gz
=====================

 * plc_viewer.py improved


plc-2012-09-29.tar.gz
=====================

 * Viewing of log-files added to plc_viewer.py

 * Viewing of brightness and changings added to plc_viewer.py


plc-2012-09-28.tar.gz
=====================

 * Added scripts:

    - plc_viewer.py

    - rawmovies2recordings.py

    - rawmovieviewer.py


plc-2012-09-10a.tar.gz
======================

 * Corrected pattern_intervall_length for the microcontroller.

 * Switches in config 'RF-Generator','pattern_file' the nothing value
   from "-" to "-1"

 * Fixed problem with channels greater 4 by setpoints. (The right
   variable is c and not i for the channel array.)


plc-2012-09-09b.tar.gz
======================

 * Manual enlarged and corrected

 * Shutter speed can now be changed by plc by config file or by the
   GUI.


plc-2012-09-09a.tar.gz
======================

 * INSTALL description enlarged.

 * Did spell-check in the manual.


plc-2012-09-08a.tar.gz
======================

 * Changelog added.

 * Section/Subsection structure corrected in the manual.

 * Table of contents added to the manual.


plc-2012-09-07c.tar.gz
======================

 * Manual enlarged.

 * Software_screenshots updated.


plc-2012-09-07b.tar.gz
======================

 * Bugfix in "rf_generator_controller.py":

   * "close" button did not close the serial device; now fixed.

 * Intervall length for computer pattern corrected to a reasonable
   value of 50 milliseconds (10^-3 sec) in
   "example_pattern_12_channels.cfg" -- see manual.

 * Software pattern checked with logic analyser in a
   RF-Generator. It is working.
   
   Intervall length less than 50 milliseconds leads to indefinite
   delays between 2 states.

 * Microcontroller pattern checked with logic analyser in a
   RF-Generator. It is working.


plc-2012-09-07a.tar.gz
======================

 * Bugfix in "rf_generator_controller.py":

   * Software pattern is now working.

 * Completed the pattern control implementation in "rf_generator.py".
   It is now working.

 * More switches in the setpoint functionality are now implemented.
   Therefore theses new switches added to "example_setpoints.cfg".
