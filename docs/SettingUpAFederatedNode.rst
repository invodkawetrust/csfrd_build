Setting up a cSFRblock Federated Node
==============================================

Introduction
-------------

A cSFRblock Federated Node is a self-contained server that runs the software necessary to support one or more "roles".
Such roles may be:
   * cSFRwallet server
   * Vending machine (future)
   * Block explorer server (future)
   * A plain old ``csfrd`` server

Each backend server runs `multiple services <components>`__ (some required, and some optional, or based on the role chosen).
As each server is self-contained, they can be combined by the client-side software to allow for high-availability/load balancing.

For instance, software such as cSFRwallet may then utilize these backend servers in making API calls either sequentially (i.e. failover) or in
parallel (i.e. consensus-based). For instance, with cSFRwallet, when a user logs in, this list is shuffled so that
in aggregate, user requests are effectively load-balanced across available servers. Indeed, by setting up multiple such
(cSFRblock) Federated Nodes, one can utilize a similar redundancy/reliability model in one's own 3rd party application
that cSFRwallet utilizes. Or, one can utilize a simplier configuration based on a single, stand-alone server.

This document describes how one can set up their own cSFRblock Federated Node server(s). It is primarily intended
for system administrators and developers.


.. _components:

Node Services/Components
-------------------------

csfrd (Required)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``csfrd`` is the SFRDirect reference client itself. It's responsibilities include parsing out SFRDirect
transactions from the Saffroncoin blockchain. It has a basic command line interface, and a reletively low-level API for
getting information on specific transactions, or general state info.

csfrblockd (Required, unless csfrd only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``csfrblockd`` daemon provides a more high-level API that layers on top of ``csfrd``'s API, and includes extended
information, such as market and price data, trade operations, asset history, and more. It is used extensively by cSFRwallet
itself, and is appropriate for use by applications that require additional API-based functionality beyond the scope of
what ``csfrd`` provides.

``csfrblockd`` also provides a proxy-based interface to all ``csfrd`` API methods, via the ``proxy_to_csfrd`` API call.

insight (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^

``insight`` allows for local querying of balance information and UTXOs for arbitrary addresses. This is a feature not available
to ``saffroncoind`` itself. Alternatives to running ``insight`` on the server are using a service like ``blockr.io``, which
both ``csfrd`` and ``csfrblockd`` support. For the most reliable service, we recommend that production
servers (at least) run ``insight`` locally.

armory_utxsvr (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^

This service is used by ``csfrblockd`` with cSFRwallet, to allow for the creation of unsigned transaction
ASCII text blocks, which may then be used with an `Offline Armory configuration <https://bitcoinarmory.com/about/using-our-wallet/>`__.
This service requires Armory itself, which is automatically installed as part of the Federated Node setup procedure.

cSFRwallet, etc.
^^^^^^^^^^^^^^^^^^^^

The specific end-functionality, that builds off of the base services provided. For instance.


Federated Node Provisioning
--------------------------------

Production
^^^^^^^^^^^^

Here are the recommendations and/or requirements when setting up a production-grade cSFRblock Federated Node:

**Server Hardware/Network Recommendations:**

- Xeon E3+ or similar-class processor
- 16GB+ RAM (ECC)
- Disk drives in RAID-1 (mirrored) configuration (SSD prefered)
- Hosted in a secure data center with physical security and access controls
- DDOS protection recommended if you will be offering your service to others

** Disk Space Requirements **
The exact disk space required will be dependent on what services are run on the node::

* Base System: **20GB** (to be safe)
* ``csfrd``, ``csfrblockd`` databases: **~200MB**
* ``insight``: **~30GB** (mainnet), **~3GB** (testnet)
* ``armory_utxsvr``: **~25GB** (mainnet), **~3GB** (testnet)

Generally, we recommend building on a server with at least 120GB of available disk space.

**Server Software:**

- Ubuntu 14.04 64-bit required

**Server Security:**

The build script includes basic automated security hardening.

Before running this script, we strongly advise the following:

- SSH should run on a different port, with root access disabled
- Use ufw (software firewall) in addition to any hardware firewalls:

  - sudo ufw allow ssh   #(or whatever your ssh port is, as '12345/tcp', in place of 'ssh')
  - sudo ufw allow http
  - sudo ufw allow https
  - sudo ufw enable

- Only one or two trusted individuals should have access to the box. All root access through ``sudo``.
- Utilize 2FA (two-factor authentication) on SSH and any other services that require login.
  `Duo <https://www.duosecurity.com/>`__ is a good choice for this (and has great `SSH integration <https://www.duosecurity.com/unix>`__).
- The system should have a proper hostname (e.g. csfrblock.myorganization.org), and your DNS provider should be DDOS resistant
- If running multiple servers, consider other tweaks on a per-server basis to reduce homogeneity.  
- Enable Ubuntu's  `automated security updates <http://askubuntu.com/a/204>`__ (our script will do this if you didn't)


Testing / Development
^^^^^^^^^^^^^^^^^^^^^^

If you'd like to set up a cSFRblock Federated Node system for testing and development, the requirements are minimal. Basically you
need to set up a Virtual Machine (VM) instance (or hardware) at the Ubuntu version listed above, at least **2 GB**
of memory, and enough disk space to cover the installation and use of the desired components.

Node Setup
-----------

Once the server is provisioned and set up as above, you will need to install all of the necessary software and dependencies. We have an
installation script for this, that is fully automated **and installs ALL dependencies, including ``saffroncoind`` and ``insight``**::

    cd && wget -qO setup_federated_node.py https://raw.github.com/saffroncoin/csfrd_build/master/setup_federated_node.py
    sudo python3 setup_federated_node.py

Then just follow the on-screen prompts (choosing to build from *master* if you are building a production node,
or from *develop* **only** if you are a developer or want access to bleeding edge code that is not fully tested).

Once done, start up ``saffroncoind`` daemon(s)::

    sudo service saffroncoind start
    sudo service saffroncoind-testnet start
    
    sudo tail -f ~csfr/.saffroncoin/debug.log 

That last command will give you information on the Saffroncoin blockchain download status. After the blockchain starts
downloading, **if you've elected to install and use** ``insight``, you can launch the ``insight`` daemon(s)::

    sudo service insight start
    sudo service insight-testnet start
    
    sudo tail -f ~csfr/insight-api/insight.log 

As well as ``armory_utxsvr``, if you're using that (cSFRwallet role only)::

    sudo service armory_utxsvr start
    sudo service armory_utxsvr-testnet start
    
    sudo tail -f ~csfr/.config/armory/armory_utxsvr.log

And ``csfrd`` itself::

    sudo service csfrd start
    sudo service csfrd-testnet start
    
    sudo tail -f ~csfr/.config/csfrd/csfrd.log

Then, watching these log, wait for the insight sync (as well as the saffroncoind sync and csfrd syncs) to finish,
which should take between 7 and 12 hours. After this is all done, reboot the box for the new services to
start (which includes both ``csfrd`` and ``csfrblockd``).

``csfrblockd``, after starting up must then sync to ``csfrd``. It will do this automatically, and the
process will take between 20 minutes to 1 hour most likely. You can check on the status of ``csfrblockd``'s
sync using::

    sudo tail -f ~csfr/.config/csfrblockd/csfrblockd.log

Once it is fully synced up, you should be good to proceed. The next step is to simply open up a web browser, and
go to the IP address/hostname of the server. You will then be presented to accept your self-signed SSL certificate, and
after doing that, should see the web interface for the role you selected (e.g. cSFRwallet login screen, if cSFRwallet
was chosen at node setup time). From this point, you can proceed testing the necessary functionality on your own system(s).


Getting a SSL Certificate
--------------------------

By default, the system is set up to use a self-signed SSL certificate. If you are hosting your services for others, 
you should get your own SSL certificate from your DNS registrar so that your users don't see a certificate warning when
they visit your site. Once you have that certificate, create a nginx-compatible ``.pem`` file, and place that
at ``/etc/ssl/certs/csfrblockd.pem``. Then, place your SSL private key at ``/etc/ssl/private/csfrblockd.key``.

After doing this, edit the ``/etc/nginx/sites-enabled/csfrblock.conf`` file. Comment out the two development
SSL certificate lines, and uncomment the production SSL cert lines, like so::

    #SSL - For production use
    ssl_certificate      /etc/ssl/certs/csfrblockd.pem;
    ssl_certificate_key  /etc/ssl/private/csfrblockd.key;
  
    #SSL - For development use
    #ssl_certificate      /etc/ssl/certs/ssl-cert-snakeoil.pem;
    #ssl_certificate_key  /etc/ssl/private/ssl-cert-snakeoil.key;

Then restart nginx::

    sudo service nginx restart


Troubleshooting
------------------------------------

If you experience issues with your cSFRblock Federated Node, a good start is to check out the logs. Something like the following should work::

    #mainnet
    sudo tail -f ~csfr/.config/csfrd/csfrd.log
    sudo tail -f ~csfr/.config/csfrblockd/countewalletd.log
    sudo tail -f ~csfr/.config/csfrd/api.error.log
    sudo tail -f ~csfr/.config/csfrblockd/api.error.log

    #testnet
    sudo tail -f ~csfr/.config/csfrd-testnet/csfrd.log
    sudo tail -f ~csfr/.config/csfrblockd-testnet/csfrblockd.log
    sudo tail -f ~csfr/.config/csfrd-testnet/api.error.log
    sudo tail -f ~csfr/.config/csfrblockd-testnet/api.error.log
    
    #relevant nginx logs
    sudo tail -f /var/log/nginx/csfrblock.access.log
    sudo tail -f /var/log/nginx/csfrblock.error.log

These logs should hopefully provide some useful information that will help you further diagnose your issue. You can also
keep tailing them (or use them with a log analysis tool like Splunk) to gain insight on the current
status of ``csfrd``/``csfrblockd``.

Also, you can start up the daemons in the foreground, for easier debugging, using the following sets of commands::

    #saffroncoind
    sudo su -s /bin/bash -c 'saffroncoind -datadir=/home/csfr/.saffroncoin' csfrd
    sudo su -s /bin/bash -c 'saffroncoind -datadir=/home/csfr/.saffroncoin-testnet' csfrd

    #csfrd & csfrblockd mainnet
    sudo su -s /bin/bash -c 'csfrd --data-dir=/home/csfr/.config/csfrd' csfrd
    sudo su -s /bin/bash -c 'csfrblockd --data-dir=/home/csfr/.config/csfrblockd -v' csfrd
    
    #csfrd & csfrblockd testnet
    sudo su -s /bin/bash -c 'csfrd --data-dir=/home/csfr/.config/csfrd-testnet --testnet' csfrd
    sudo su -s /bin/bash -c 'csfrblockd --data-dir=/home/csfr/.config/csfrblockd-testnet --testnet -v' csfrd

You can also run ``saffroncoind`` commands directly, e.g.::

    #mainnet
    sudo su - csfrd -s /bin/bash -c "saffroncoind -datadir=/home/csfr/.saffroncoin getinfo"
    
    #testnet
    sudo su - csfrd -s /bin/bash -c "saffroncoind -datadir=/home/csfr/.saffroncoin-testnet getinfo"


Monitoring the Server
----------------------

To monitor the server, you can use a 3rd-party service such as [Pingdom](http://www.pingdom.com) or [StatusCake](http://statuscake.com).
The federated node allows these (and any other monitoring service) to query the basic status of the server (e.g. the ``nginx``,
``csfrblockd`` and ``csfrd`` services) via making a HTTP GET call to one of the following URLs:

* ``/_api/`` (for mainnet) 
* ``/_t_api/`` (for testnet)

If all services are up, a HTTP 200 response with the following data will be returned::

    {"csfrd": "OK", "csfrblockd_ver": "1.3.0", "csfrd_ver": "9.31.0", "csfrblockd": "OK",
    "csfrblockd_check_elapsed": 0.0039348602294921875, "csfrd_last_block": {
    "block_hash": "0000000000000000313c4708da5b676f453b41d566832f80809bc4cb141ab2cd", "block_index": 311234,
    "block_time": 1405638212}, "local_online_users": 7, "csfrd_check_elapsed": 0.003687143325805664, 
    "csfrblockd_error": null, "csfrd_last_message_index": 91865}
    
Note the ``"csfrd": "OK"`` and ``"csfrblockd": "OK"`` items.

If all services but ``csfrd`` are up, a HTTP 500 response with ``"csfrd": "NOT OK"``, for instance.

If ``csfrblockd`` is not working properly, ``nginx`` will return a HTTP 503 (Gateway unavailable) or 500 response.

If ``nginx`` is not working properly, either a HTTP 5xx response, or no response at all (i.e. timeout) will be returned.


Other Topics
--------------

User Configuration
^^^^^^^^^^^^^^^^^^^^

Note that when you set up a federated node, the script creates two new users on the system: ``sfr`` and ``csfrd``. (The
``sfr`` user also has an ``sfr`` group created for it as well.)

The script installs ``csfrd``, ``csfrwallet``, etc into the home directory of the ``sfr`` user. This
user also owns all installed files. However, the daemons (i.e. ``saffroncoind``, ``insight``, ``csfrd``,
``csfrblockd``, and ``nginx``) are actually run as the ``csfrd`` user, which has no write access to the files
such as the ``csfrwallet`` and ``csfrd`` source code files. The reason things are set up like this is so that
even if there is a horrible bug in one of the products that allows for a RCE (or Remote Control Exploit), where the attacker
would essentially be able to gain the ability to execute commands on the system as that user, two things should prevent this:

* The ``csfrd`` user doesn't actually have write access to any sensitive files on the server (beyond the log and database
  files for ``saffroncoind``, ``csfrd``, etc.)
* The ``csfrd`` user uses ``/bin/false`` as its shell, which prevents the attacker from gaining shell-level access

This setup is such to minimize (and hopefully eliminate) the impact from any kind of potential system-level exploit.

Easy Updating
^^^^^^^^^^^^^^^^

To update the system with new code releases, you simply need to rerun the ``setup_federated_node`` script, like so::

    cd ~csfr/csfrd_build
    sudo ./setup_federated_node.py
    
As prompted, you should be able to choose just to update from git ("G"), instead of to rebuild. However, you would choose the rebuild
option if there were updates to the ``csfrd_build`` system files for the federated node itself (such as the
``nginx`` configuration, or the init scripts) that you wanted/needed to apply. Otherwise, update should be fine. 


cSFRwallet-Specific
-----------------------

cSFRwallet Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

cSFRwallet can be configured via creating a small file called ``csfrwallet.conf.json`` in the ``csfrwallet/`` directory.
This file will contain a valid JSON-formatted object, containing an a number of possible configuration properties. For example::

    { 
      "servers": [ "csfrblock1.mydomain.com", "csfrblock2.mydomain.com", "csfrblock3.mydomain.com" ],
      "forceTestnet": true,
      "googleAnalyticsUA": "UA-48454783-2",
      "googleAnalyticsUA-testnet": "UA-48454783-4",
      "rollbarAccessToken": "39d23b5a512f4169c98fc922f0d1b121",
      "disabledFeatures": ["rps", "betting"],
      "restrictedAreas": {
        "pages/betting.html": ["US"],
        "pages/openbets.html": ["US"],
        "pages/matchedbets.html": ["US"],
        "pages/rps.html": ["US"],
        "dividend": ["US"]
      },
      "autoBTCEscrowServer": "btcescrow.csfrwallet.co"
    }

Here's a description of the possible fields:

**Required fields:**

* **servers**: cSFRwallet should work out-of-the-box in a scenario where you have a single cSFRblock Federated Node that both hosts the
static site content, as well as the backend cSFRblock API services. However, cSFRwallet can also be set up to work
in MultiAPI mode, where it can query more than one server (to allow for both redundancy and load balancing). To do this,
set this ``servers`` parameter as a list of multiple server URIs. Each URI can have a ``http://`` or ``https://`` prefix
(we strongly recommend using HTTPS), and the strings must *not* end in a slash (just leave it off). If the server hostname
does not start with ``http://`` or ``https://``, then ``https://`` is assumed.

*If you just want to use the current server (and don't have a multi-server setup), just specify this as ``[]`` (empty list).*

**Optional fields:**

* **forceTestnet**: Set to true to always use testnet (not requiring 'testnet' in the FQDN, or the '?testnet=1' parameter in the URL.
* **googleAnalyticsUA** / **googleAnalyticsUA-testnet**: Set to enable google analytics for mainnet/testnet. You must have a google analytics account.
* **rollbarAccessToken**: Set to enable client-side error tracking via rollbar.com. Must have a rollbar account.
* **disabledFeatures**: Set to a list of zero or more features to disable in the UI. Possible features are:
  ``betting``, ``rps``, ``dividend``, ``exchange``, ``leaderboard``, ``portfolio``, ``stats`` and ``history``. Normally
  this can just be ``[]`` (an empty list) to not disable anything.
* **restrictedAreas**: Set to an object containing a specific page path as the key (or "dividend" for dividend functionality),
  and a list of one or more ISO 2-letter country codes as the key value, to allow for country-level blacklisting of pages/features.
* **autoBTCEscrowServer**: The hostname to use for automatic BTC escrow services (where an external server will hold the BTC
  related to open orders selling BTC and make BTCpays from it automatically). If not specified, or left blank, then
  automatic BTC escrows will be disabled.

Once done, save this file and make sure it exists on all servers you are hosting cSFRwallet static content on. Now, when you go
to your cSFRwallet site, the server will read in this file immediately after loading the page, and set the list of
backend API hosts from it automatically.

Giving Op Chat Access
^^^^^^^^^^^^^^^^^^^^^^

cSFRwallet has its own built-in chatbox. Users in the chat box are able to have operator (op) status, which allows them
to do things like ban or rename other users. Any op can give any other user op status via the ``/op`` command, typed into
the chat window. However, manual database-level intervention is required to give op status to the first op in the system.

Doing this, however, is simple. Here's an example that gives ``testuser1`` op access. It needs to be issued at the
command line for every node in the cluster::

    #mainnet
    mongo csfrblockd
    db.chat_handles.update({handle: "testuser1"}, {$set: {op: true}})
    
    #testnet
    mongo csfrblockd_testnet
    db.chat_handles.update({handle: "testuser1"}, {$set: {op: true}})

cSFRwallet MultiAPI specifics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

    By default, cSFRblock Federated Nodes can also host cSFRwallet content (this will change in the future).
    Regarding this, the Saffroncoin team itself operates the primary cSFRwallet platform. However, as cSFRwallet is open source
    software, it is possible to host your own site with cSFRwallet site (for your personal use, or as an offering to
    others), or to even host your own cSFRwallet servers to use with your own SFRDirect wallet implementation.
    The Saffroncoin team supports this kind of activity (as long as the servers are secure), as it aids with increasing decentralization.
        
    Also note that due to the nature of cSFRwallet being a deterministic wallet, users using one cSFRwallet platform (i.e. the
    official one, for instance) have the flexibility to start using a different cSFRwallet platform instead at any time,
    and as funds (i.e. private keys) are not stored on the server in any fashion, they will be able to see their funds on either.
    (Note that the only thing that will not migrate are saved preferences, such as address aliases, the theme setting, etc.)

cSFRwallet utilizes a sort of a "poor man's load balancing/failover" implementation called multiAPI (and implemented
[here](https://github.com/saffroncoin/csfrwallet/blob/master/src/js/util.api.js)). multiAPI can operate in a number of fashions.

**multiAPIFailover for Read API (``get_``) Operations**

*multiAPIFailover* functionality is currently used for all read API operations. In this model, the first Federated Node
on the shuffled list is called for the data, and if it returns an error or the request times out, the second one on the
list is called, and so on. The result of the first server to successfully return are used.

Here, a "hacked" server could be modified to return bogus data. As (until being discovered) the server would be in the
shuffled list, some clients may end up consulting it. However, as this functionality is essentially for data queries only,
the worse case result is that a cSFRwallet client is shown incorrect/modified data which leads to misinformed actions
on the user's behalf. Moreover, the option always exists to move all read-queries to use multiAPIConsensus in the future should the need arise.

**multiAPIConsensus for Action/Write (``create_``) Operations**

Based on this multiAPI capability, the wallet itself consults more than one of these Federated Nodes via consensus especially
for all ``create_``-type operations. For example, if you send csfr, csfrd on each server is still composing and sending
back the unsigned raw transaction, but for data security, it compares the results returned from all servers, and will 
only sign and broadcast (both client-side) if all the results match). This is known as *multiAPIConsensus*.

The ultimate goal here is to have a federated net of semi-trusted backend servers not tied to any one country, provider, network or
operator/admin. Through requiring consensus on the unsigned transactions returned for all ``create_`` operations, 'semi-trust'
on a single server basis leads to an overall trustworthy network. Worst case, if backend server is hacked and owned
(and the csfrd code modified), then you may get some invalid read results, but it won't be rewriting your csfr send
destination address, for example. The attackers would have to hack the code on every single server in the same exact
way, undetected, to do that.

Moreover, the cSFRwallet web client contains basic transaction validation code that will check that any unsigned Saffroncoin
transaction returned from a cSFRblock Federated Node contains expected inputs and outputs. This provides further
protection against potential attacks.

multiAPIConsensus actually helps discover any potential "hacked" servers as well, since a returned consensus set with
a divergent result will be rejected by the client, and thus trigger an examination of the root cause by the team.

**multiAPINewest for Redundant storage**

In the same way, these multiple servers are used to provide redundant storage of client-side preferences, to ensure we
have no single point of failure. In the case of the stored preferences for instance, when retrieved on login, the data from all servers
is taken in, and the newest result is used. This *multiAPINewest* functionality effectively makes a query across all available
Federated Nodes, and chooses the newest result (based on a "last updated"-type timestamp).

Note that with this, a "hacked" server could be modified to always return the latest timestamp, so that its results
were used. However, wallet preferences (and other data stored via this functionality) is non-sensitive, and thus user's
funds would not be at risk before the hacked server could be discovered and removed.

