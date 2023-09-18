from distutils.core import setup,Command

class check_modules(Command):
    """checking for modules need to run the software"""
    description = "checking for modules need to run the software"
    user_options = []
    def initialize_options (self):
        pass
    def finalize_options (self):
        pass
    def run (self):
        import importlib
        s = ""
        i = 0
        print("checking for modules need to run the software (scripts and")
        print("modules/packages) of this package:\n")
        print("checking for the modules mentioned in the 'setup.py':")
        for p in self.distribution.metadata.get_requires():
            if self.verbose:
                print(("try to load %s" % p))
            try:
                importlib.import_module(p)
                if self.verbose:
                    print("  loaded.")
            except:
                i += 1
                s += "module '%s' is not available\n" % p
                print(("module '%s' is not available <---WARNING---" % p))
        print(("\nSummary\n%d modules are not available (not unique)\n%s\n" % (i,s)))

class check_modules_modulefinder(Command):
    """checking for modules need to run the scripts (modulefinder)"""
    description = "checking for modules need to run the scripts (modulefinder)"
    user_options = []
    def initialize_options (self):
        pass
    def finalize_options (self):
        pass
    def run (self):
        import modulefinder
        for s in self.distribution.scripts:
            print(("\nchecking for modules used in '%s':" % s))
            finder = modulefinder.ModuleFinder()
            finder.run_script(s)
            finder.report()

setup(name='plc',
      version = '2017-05-30',
      cmdclass={'check_modules': check_modules,
                'check_modules_modulefinder': check_modules_modulefinder},
      description = 'PlasmaLabControl is a software for controlling the experiment.',
      long_description = '',
      keywords='Plasmalab Plasma Lab',
      author = 'Daniel Mohr',
      author_email = 'mohr@mpe.mpg.de, daniel.mohr@dlr.de',
      maintainer = 'Daniel Mohr',
      maintainer_email = 'mohr@mpe.mpg.de, daniel.mohr@dlr.de',
      url = 'http://mpe.mpg.de/ http://www.dlr.de/',
      download_url = '',
      packages = ['plc_gui',
                  'plc_tools'],
      #data_files=[('config', ['default_plc.cfg'])],
      scripts=['plc.py',
               'plc_viewer.py',
               'debug_controller.py',
               'rawmovies2recordings.py',
               'rawmovieviewer.py',
               'digital_controller_server.py',
               'digital_controller_client.py',
               'multi_purpose_controller_server.py',
               'multi_purpose_controller_client.py',
               'camera_server.py',
               'camera_client.py',
               'acceleration_sensor_logger.py',
               'acceleration_sensor_server.py',
               'acceleration_sensor_client.py',
               'logs2housekeeping.py',
               'communication_statistic.py',
               'pressure_mks_651_server.py',
               'pressure_mks_651_client.py',
               'pressure_mks_900_server.py',
               'pressure_mks_900_client.py',
               'translation_stage_scan.py',
               'environment_sensor_5_logger.py',
               'rawmovie2pngs.py',
               'check_real_time_difference.py',
               'distance_from_picture.py',
               'rawmovie2tiff.py',
               'trigger.py'],
      license = 'GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007',
      classifiers = ['Development Status :: 3 - Alpha',
                     'Environment :: Console',
                     'Environment :: X11 Applications',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: GNU General Public License (GPL)',
                     'Natural Language :: English',
                     'Operating System :: POSIX',
                     'Operating System :: POSIX :: BSD :: FreeBSD',
                     'Operating System :: POSIX :: BSD :: OpenBSD',
                     'Operating System :: POSIX :: Linux',
                     'Operating System :: Unix',
                     'Operating System :: MacOS',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Tcl',
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Image Recognition',
                     'Topic :: Scientific/Engineering :: Physics',
                     'Topic :: Scientific/Engineering :: Visualization',
                     'Topic :: Software Development :: Libraries :: Python Modules',
                     'Topic :: System :: Hardware :: Hardware Drivers'],
      # cat $(find | grep "py$") | egrep -i "^[ \t]*import .*$" | egrep -i --only-matching "import .*$" | sort -u
      requires = ['argparse',
                  'ConfigParser',
                  'cPickle',
                  'cStringIO',
                  'csv',
                  'datetime',
                  'distutils.core',
                  'errno',
                  'fnmatch',
                  'importlib',
                  'logging',
                  'logging.handlers',
                  'math',
                  'matplotlib',
                  'matplotlib.pyplot',
                  'modulefinder',
                  'numpy',
                  'os',
                  'os.path',
                  'PIL.ImageOps',
                  'PIL.Image',
                  'PIL.ImageDraw',
                  'PIL.ImageEnhance',
                  'PIL.ImageMath',
                  'PIL.ImageTk',
                  'pydc1394',
                  'Queue',
                  'random',
                  're',
                  'serial',
                  'signal',
                  'SimpleHTTPServer',
                  'socket',
                  'SocketServer',
                  'string',
                  'StringIO',
                  'struct',
                  'subprocess',
                  'sys',
                  'tarfile',
                  'tempfile',
                  'threading',
                  'time',
                  'tkFileDialog',
                  'Tkinter',
                  'tkMessageBox',
                  'ttk',
                  'types',
                  'unittest',
                  'usb',
                  'zipfile'],
      provides = ['plc_gui',
                  'plc_tools']
      )
