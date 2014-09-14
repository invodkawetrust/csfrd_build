SaffroncoinTest Additional Topics
======================

This section contains some tidbits of info that you may find useful when working with ``csfrd``.

For a good overview of what you can do with ``csfrd``, see `this link <https://github.com/saffroncoin/csfrd#usage>`__.

Finding the Data Directory
---------------------------

``csfrd`` stores its configuration, logging, and state data in a place known as the ``csfrd``
data directory.

Under Linux, the data directory is normally located in ``~/.config/csfrd`` (when
``csfrd`` is installed normally, via the ``setup.py`` installer).

Under Windows, the data directory is normally located at ``%APPDATA%\saffroncoin\csfrd``. Examples of this are:

- ``C:\Users\<your username>\AppData\Roaming\Saffroncoin\csfrd`` (Windows 7/8/Server)
- ``C:\Documents and Settings\<your username>\Application Data\Saffroncoin\csfrd`` (Windows XP)


Editing the Config
---------------------------

``csfrd`` can read its configuration data from a file. The build system uses this method to allow for 
automated startup of ``csfrd``.

If using the Windows installer, a configuration file will be automatically created for you from data gathered
via the installation wizard.

If not using the Windows installer, the ``setup.py`` script will create a basic ``csfrd.conf`` file for you that contains
options that tell ``csfrd`` where and how to connect to your ``saffroncoind`` process. Here's an example of the default file created::

    [Default]
    saffroncoind-rpc-connect=localhost
    saffroncoind-rpc-port=19710
    saffroncoind-rpc-user=rpc
    saffroncoind-rpc-password=rpcpw1234
    rpc-user=my_api_user
    rpc-password=my_api_password

After running the ``setup.py`` script to create this file, you'll probably need to edit it and tweak the settings
to match your exact ``saffroncoind`` configuration (e.g. especially ``rpc-password``). Note that the above config
connects to ``saffroncoind`` on mainnet (port 19710).

Note that also, with the config above, it will set up ``csfrd`` to listen on localhost (127.0.0.1)
on port 39710 (if on mainnet) or port 49710 (if on testnet) for API connections (these are the default ports,
and can be changed by specifying the ``rpc-host`` and/or ``rpc-port`` parameters).


Viewing the Logs
-----------------

By default, ``csfrd`` logs data to a file named ``csfrd.log``, located within the ``csfrd``
data directory.

Under Linux, you can monitor these logs via a command like ``tail -f ~/.config/csfrd/csfr.log``.

Under Windows, you can use a tool like `Notepad++ <http://notepad-plus-plus.org/>`__ to view the log file,
which will detect changes to the file and update if necessary.

Running csfrd on testnet
--------------------------------

Here's the steps you'll need to take to set up an additional saffroncoind on testnet for ``csfrd`` testing. 
This assumes that you're already running ``saffroncoind`` (or ``saffroncoin-qt``) on mainnet, and would like to set up a
second instance for testnet:

Windows
~~~~~~~~

First, find your current ``saffroncoind`` data directory, which is normally located at ``%APPDATA%\Saffroncoin``. Examples of this are:

- ``C:\Users\<your username>\AppData\Roaming\Saffroncoin`` (Windows 7/8/Server)
- ``C:\Documents and Settings\<your username>\Application Data\Saffroncoin`` (Windows XP)

Alongside that directory (e.g. at the root of your AppData\Roaming dir), create another directory, name it something
like ``SaffroncoinTest``.

- ``C:\Users\<your username>\AppData\Roaming\SaffroncoinTest`` (Windows 7/8/Server)
- ``C:\Documents and Settings\<your username>\Application Data\SaffroncoinTest`` (Windows XP)
 
In this ``SaffroncoinTest`` directory, create a ``saffroncoin.conf`` file with the following contents::

    rpcuser=rpc
    rpcpassword=rpcpw1234
    server=1
    daemon=1
    txindex=1
    testnet=1

Now, make a shortcut to something like the following (assuming you installed to the default
install directory from the .exe installer):

To run ``saffroncoin-qt``: ``"C:\Program Files (x86)\Saffroncoin\saffroncoin-qt.exe" --datadir="C:\Users\<your username\AppData\Roaming\SaffroncoinTest"``
To run ``saffroncoind``: ``"C:\Program Files (x86)\Saffroncoin\saffroncoind.exe" --datadir="C:\Users\<your username>\AppData\Roaming\SaffroncoinTest"``

Note that you can run either. If you want the GUI, run saffroncoin-qt (which will also listen on the RPC interface).
If you are comfortable using ``saffroncoind`` commands (or are using a server), just run ``saffroncoind``.

Then, just launch that shortcut. (Or, if you are having problems, you can just open up a command window and
try running that directly.)

Once launched, ``saffroncoind``/``saffroncoin-qt`` will be listening on testnet RPC API port ``18332``. You can just
run ``csfrd`` with its ``--datadir`` parameter to point to a directory with its own
``csfrd.conf`` file that has the connection parameters to your testnet saffroncoin daemon that's now running.

This means, that like with ``saffroncoind``, you may have two separate ``csfrd`` data directories, each with
their own configuration file and database. The difference
between the configuration files in each datadir will be that the one for your "testnet" ``csfrd`` will simply
specify ``rpc-port=18332``, while the one for your "mainnet" ``csfrd`` will specify ``rpc-port=8332``.


Linux
~~~~~~

Similar to the above, create a second saffroncoin data directory (maybe name it ``.saffroncoin-test``, instead of ``.saffroncoin``). Place
it alongside your main ``.saffroncoin`` directory (e.g. under ``~``). In this directory, create a ``saffroncoin.conf``
file with the same contents as in the above Windows section.

Now, run ``saffroncoind`` or ``saffroncoin-qt``, as such:

To run ``saffroncoin-qt``: ``"saffroncoin-qt --datadir=~/.saffroncoin-test``
To run ``saffroncoind``: ``saffroncoind --data-dir=~/.saffroncoin-test``

For more information, see the Windows section above.


Next Steps
-----------

Once ``csfrd`` is installed and running, you can start running ``csfrd`` commands directly,
or explore the (soon to exist) built-in API via the documentation at the `main csfrd repository <https://github.com/saffroncoin/csfrd>`__.
