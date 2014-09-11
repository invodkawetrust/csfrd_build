Setting up saffroncoind
====================

.. warning::

    This section sets up ``csfrd`` to run on mainnet, which means that when using it, **you will be working with real XCP**.
	  If you would like to run on testnet instead, please see the section entitled **Running csfrd on testnet** in
	  :doc:`Additional Topics <AdditionalTopics>`.

``csfrd`` communicates with the Saffroncoin reference client (``saffroncoind``). Normally, you'll run ``saffroncoind``
on the same computer as your instance of ``csfrd`` runs on. However, you can also use a ``saffroncoind`` instance
sitting on a different server entirely.

This step is necessary whether you're :doc:`building csfrd from source <BuildingFromSource>` or
using the :doc:`installer package <UsingTheInstaller>`.


On Windows
-----------

If you haven't already, go to `the saffroncoind download page <http://saffroncoin.org/en/download>`__
and grab the installer for Windows. Install it with the default options.

Once installed, type Windows Key-R and enter ``cmd.exe`` to open a Windows command prompt. Type the following::

    cd %APPDATA%\Saffroncoin
    notepad saffroncoin.conf  

Say Yes to when Notepad asks if you want to create a new file, then paste in the text below::

    rpcuser=rpc
    rpcpassword=rpcpw1234
    server=1
    daemon=1
    txindex=1

**NOTE**:

- If you want ``saffroncoind`` to be on testnet, not mainnet, see the section entitled **Running csfrd on testnet** in :doc:`Additional Topics <AdditionalTopics>`.
- You should change the RPC password above to something more secure.
    
Once done, press CTRL-S to save, and close Notepad.  The config file will be saved here::

    ``%AppData%\Roaming\Saffroncoin\csfrd\csfrd.conf``

New Blockchain Download
^^^^^^^^^^^^^^^^^^^^^^^^

Next, if you haven't ever run Saffroncoin on this machine (i.e. no blockchain has been downloaded),
you can just launch ``saffroncoind`` or ``saffroncoin-qt`` and wait for the blockchain to finish downloading.

Already have Blockchain
^^^^^^^^^^^^^^^^^^^^^^^^

If you have already downloaded the blockchain on your computer (e.g. you're already using the Saffroncoin client) **and** 
you did not have the configuration parameter ``txindex=1`` enabled, you will probably need to open up a command prompt
window, change to the Saffroncoin program directory (e.g. ``C:\Program Files (x86)\Saffroncoin\``) and run::

    saffroncoin-qt.exe --reindex
    
or::

    daemon\saffroncoind.exe --reindex
    
This will start up saffroncoin to do a one time reindexing of the blockchain on disk. The reason this is is because we 
added the ``txindex=1`` configuration parameter above to the saffroncoin config file, which means that it will need to
run through the blockchain again to generate the necessary indexes, which may take a few hours. After doing
this once, you shouldn't have to do it again.   

Next steps
^^^^^^^^^^^

Once this is done, you have two options:

- Close Saffroncoin-QT and run ``saffroncoind.exe`` directly. You can run it on startup by adding to your
  Startup program group in Windows, or using something like `NSSM <http://nssm.cc/usage>`__.
- You can simply restart Saffroncoin-QT (for the configuration changes to take effect) and use that. This is
  fine for development/test setups, but not normally suitable for production systems. (You can have
  Saffroncoin-QT start up automatically by clicking on Settings, then Options and checking the
  box titled "Start Saffroncoin on system startup".)


On Ubuntu Linux
----------------

If not already installed (or running on a different machine), do the following
to install it (on Ubuntu, other distros will have similar instructions)::

    sudo apt-get install software-properties-common python-software-properties
    sudo add-apt-repository ppa:saffroncoin/saffroncoin
    sudo apt-get update
    sudo apt-get install saffroncoind
    mkdir -p ~/.saffroncoin/
    echo -e "rpcuser=rpc\nrpcpassword=rpcpw1234\nserver=1\ndaemon=1\ntxindex=1" > ~/.saffroncoin/saffroncoin.conf

Please then edit the ``~/.saffroncoin/saffroncoin.conf`` file and set the file to the same contents specified above in 
saffroncoin.conf example for Windows.

New Blockchain Download
^^^^^^^^^^^^^^^^^^^^^^^^

Next, if you haven't ever run ``saffroncoin-qt``/``saffroncoind`` on this machine (i.e. no blockchain has been downloaded),
you can just start ``saffroncoind``::

    saffroncoind

In either of the above cases, the saffroncoin server should now be started. The blockchain will begin to download automatically. You must let it finish 
downloading entirely before going to the next step. You can check the status of this by running::

     saffroncoind getinfo | grep blocks

When done, the block count returned by this command will match the value given from
`this page <http://blockexplorer.com/q/getblockcount>`__.

Already have Blockchain
^^^^^^^^^^^^^^^^^^^^^^^^

If you *have* already downloaded the blockchain before you modified your config and you did not have ``txindex=1`` 
enabled, you'll probably need to launch ``saffroncoind`` as follows:

    saffroncoind --reindex

    
This will start up saffroncoin to do a one time reindexing of the blockchain on disk. The reason this is is because we added the
``txindex=1`` configuration parameter above to the saffroncoin config file, which means that it will need to
run through the blockchain again to generate the necessary indexes, which may take a few hours. After doing
this once, you shouldn't have to do it again.

If you had the blockchain index parameter always turned on before, reindexing should not be necessary.

Next steps
^^^^^^^^^^^

At this point you should be good to go from a ``saffroncoind`` perspective.
For automatic startup of ``saffroncoind`` on system boot, `this page <https://saffroncointalk.org/index.php?topic=25518.0>`__
provides some good tips.
