Building & Running from Source
================================

.. note::

    Please make sure you've followed the instructions in :doc:`SettingUpSaffroncoind` before moving through this section.

This section provides information about how to install and run ``csfrd`` from source, using this
``csfrd`` build system (as an alternative to setting it up manually). This method is suitable for
Linux users, as well as Windows users that want to develop/enhance ``csfrd`` (or just don't want to
use the binary installer).


On Windows
-----------

Prerequisites
^^^^^^^^^^^^^^^

.. note::

    As of csfrd v9.34.0 due to issues with some Python modules, a 64-bit version of Python cannot be used
    to build SFRDirect out-of-the-box. For time being it is recommended to use a 32-bit version of Python 3.3.5
    on both the 32-bit and 64-bit version of Microsoft Windows (confirmed to work with Windows 7 SP1 x64).

Minimally required to build ``csfrd`` from source is the following:

- Python 3.3.5 -- grab the `32-bit version <http://www.python.org/ftp/python/3.3.5/python-3.3.5.msi>`__
  or `64-bit version <http://www.python.org/ftp/python/3.3.5/python-3.3.5.amd64.msi>`__.
  Install to the default ``C:\Python33`` location
- Python Win32 extensions -- grab the `32-bit version <http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win32-py3.3.exe/download>`__
  or `64-bit version <http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win-amd64-py3.3.exe/download>`__
- APSW for Windows -- grab the `32-bit version <https://github.com/rogerbinns/apsw/releases/download/3.8.5-r1/apsw-3.8.5-r1.win32-py3.3.exe>`__
  or `64-bit version <https://github.com/rogerbinns/apsw/releases/download/3.8.5-r1/apsw-3.8.5-r1.win-amd64-py3.3.exe>`__
- Pycrypto for Windows -- grab the `32-bit version <http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py3.3.exe>`__
  or `64-bit version <http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win-amd64-py3.3.exe>`__
- Git for Windows (should have already been downloaded for the ``insight`` setup).
  Download `here <http://git-scm.com/download/win>`__ and install. Use the default installer
  options (except, select *"Run Git from the Windows Command Prompt"* on the appropriate screen)
- You may need to install `Visual C++ 2010 Express <http://go.microsoft.com/?linkid=9709949>`__

If you want to be able to build the cSFRd installer, also download the following:

- Grab NSIS from `here <http://prdownloads.sourceforge.net/nsis/nsis-2.46-setup.exe?download>`__ -- Please choose the default
  options during installation, and install to the default path
- Download the NSIS SimpleService plugin from `here <http://nsis.sourceforge.net/mediawiki/images/c/c9/NSIS_Simple_Service_Plugin_1.30.zip>`__
  and save the .dll file contained in that zip to your NSIS ``plugins`` directory (e.g. ``C:\Program Files (X86)\NSIS\plugins``)
- cx_freeze -- grab the `32-bit version <http://sourceforge.net/projects/cx-freeze/files/4.3.3/cx_Freeze-4.3.3.win32-py3.3.msi/download>`__
  or `64-bit version <http://downloads.sourceforge.net/project/cx-freeze/4.3.3/cx_Freeze-4.3.3.win-amd64-py3.3.msi>`__ as appropriate
- Install a binary build of cherrypy-wsgiserver `such as this (for 32-bit Python) <https://bitbucket.org/cherrypy/cherrypy/issue-attachment/1110/cherrypy/cherrypy/1322273715.09/1110/CherryPy-3.2.2.win32.exe>`__ 

Installing
^^^^^^^^^^^^^^^^^^^^^^

.. note::

    Our install script (setup.py) requires administrator access to run (so that it can create a csfrd.bat file
    in your Windows directory). To allow for this, you must launch a command prompt **as administrator**. To do this
    under Windows 7, go to Start -> All Programs -> Accessories, then right click on Command Prompt and select "Run as administrator".
    More information on this is available from `this link <http://www.bleepingcomputer.com/tutorials/windows-elevated-command-prompt/>`__ (method 1 or 2 works fine).
    
After launching a DOS command window using the instructions in the note above, type the following commands::

    cd C:\
    git clone https://github.com/saffroncoin/csfrd_build
    cd csfrd_build
    C:\Python33\python.exe setup.py
     
The above steps will check out the build scripts to ``C:\csfrd_build``, and run the ``setup.py`` script, which
will check out the newest version of ``csfrd`` itself from git, create a virtual environment with the
required dependencies, and do other necessary tasks to integrate it into the system.

If you chose to start ``csfrd`` at startup automatically, the setup script will also create a shortcut
to ``csfrd`` in your Startup group. 

Upon the successful completion of this script, you can now run ``csfrd`` using the steps below.


Running csfrd built from Source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

cSFRd does not require elevated ("administrator") privileges to be executed and operated.  
After installing, open a command window and run ``csfrd`` in the foreground via::

    csfrd server

You can then open up another command window and run any of ``csfrd’s`` other functions, for example::

    csfrd send --source=12WQTnVbzhJRswra4TvGxq1RyhUkmiVXXm --destination=VQGZ4sCpvCgRizL5v4NniaKdZKzxBtVN3q --asset=cSFR --quantity=5

For more examples, see `this link <https://github.com/saffroncoin/csfrd#examples>`__.

To run the ``csfrd`` testsuite::

    csfrd tests 


Updating to the newest source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As the code is enhanced and improved on Github, you can refresh your local copy of the repositories like so::

    cd C:\csfrd_build
    C:\Python33\python.exe setup.py update

If, upon running csfrd, you get a missing dependency or some other error, you can always rerun
``setup.py``, which will regenerate your dependencies listing to the libraries and versions as listed in
`pip-requirements.txt <https://github.com/saffroncoin/csfrd/blob/master/pip-requirements.txt>`__::

    cd csfrd_build
    C:\Python33\python.exe setup.py

In case of a problem, refer to the list of requirements in ``pip-requirements.txt`` above and update system as
necessary. Then rerun the build script again.

Building your own Installer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Complete the instructions under **Prerequisites** above.
Then, execute the following commands to build the installer package::

    cd C:\csfrd_build
    C:\Python33\python.exe setup.py build
    
If successful, you will be provided the location of the resulting installer package.


On Linux
-----------

Prerequisites
^^^^^^^^^^^^^^^^^^^^^^

Currently, Ubuntu Linux (Server or Desktop) **12.04 LTS**, **13.10**, and **14.04** are supported.

Support for other distributions is a future task.


Installing
^^^^^^^^^^^^^^^^^^^^^^

**As the user you want to run** ``csfrd`` **as**, launch a terminal window, and type the following::

    sudo apt-get -y update
    sudo apt-get -y install git-core python3
    git clone https://github.com/saffroncoin/csfrd_build ~/csfrd_build
    cd ~/csfrd_build
    sudo python3 setup.py

The ``setup.py`` script will install necessary dependencies, check out the newest version of ``csfrd``
itself from git, create the python environment for ``csfrd``, and install an upstart script that
will automatically start ``csfrd`` on startup.


Creating a default config
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Follow the instructions listed under the **Config and Logging** section in :doc:`AdditionalTopics`.


Running csfrd built from Source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After installing and creating the necessary basic config, run ``csfrd`` in the foreground to make sure
everything works fine::

    csfrd server
    
(The above assumes ``/usr/local/bin`` is in your PATH, which is where the ``csfrd`` symlink (which just
points to the ``run.py`` script) is placed. If not, run ``/usr/local/bin/csfrd`` instead.

Once you're sure it launches and runs fine, press CTRL-C to exit it, and then run ``csfrd`` as a background process via::

    sudo service csfrd start

You can then open up another command window and run any of ``csfrd’s`` other functions, for example::

    csfrd send --source=V2WQTnVbzhJRswra4TvGxq1RyhUkmiVXXm --destination=VQGZ4sCpvCgRizL5v4NniaKdZKzxBtVN3q --asset=cSFR --quantity=5

For more examples, see `this link <https://github.com/saffroncoin/csfrd#examples>`__.

To run the ``csfrd`` testsuite::

    csfrd tests


Updating to the newest source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As the code is enhanced and improved on Github, you can refresh your local copy of the repositories like so::

    cd ~/csfrd_build
    sudo python3 setup.py update

SFRDirect for Windows must also be updated from a console window started with elevated privileges.

If, upon running csfrd, you get a missing dependency or some other error, you can always rerun
``setup.py``, which will regenerate your dependencies listing to the libraries and versions as listed in
`pip-requirements.txt <https://github.com/saffroncoin/csfrd/blob/master/pip-requirements.txt>`__::

    cd ~/csfrd_build
    sudo python3 setup.py

The same approach applies to Windows - this operation requires elevation.

Mac OS X
--------

Mac OS support is forthcoming. (Pull requests to add such support are more than welcome!)
