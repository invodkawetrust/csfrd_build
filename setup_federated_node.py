#! /usr/bin/env python3
"""
Sets up an Ubuntu 14.04 x64 server to be a cSFRblock Federated Node.

NOTE: The system should be properly secured before running this script.

TODO: This is admittedly a (bit of a) hack. In the future, take this kind of functionality out to a .deb with
      a postinst script to do all of this, possibly.
"""
import os
import sys
import re
import time
import getopt
import logging
import shutil
import socket
import urllib
import zipfile
import platform
import collections
import tempfile
import subprocess

try: #ignore import errors on windows
    import pwd
    import grp
except ImportError:
    pass

from setup_util import *

USERNAME = "csfr"
DAEMON_USERNAME = "csfrd"
USER_HOMEDIR = "/home/csfr"
QUESTION_FLAGS = collections.OrderedDict({
    "op": ('u', 'r'),
    "role": ('csfrwallet', 'vendingmachine', 'blockexplorer', 'csfrd_only', 'btcpayescrow'),
    "branch": ('master', 'develop'),
    "run_mode": ('t', 'm', 'b'),
    "backend_rpc_mode": ('s', 'p'),
    "blockchain_service": ('b', 'i'),
    "security_hardening": ('y', 'n'),
    "csfrd_public": ('y', 'n'),
    "csfrwallet_support_email": None,
    "autostart_services": ('y', 'n'),
})

def do_base_setup(run_as_user, branch, base_path, dist_path):
    """This creates the csfr and csfrd users and checks out the csfrd_build system from git"""
    #change time to UTC
    runcmd("ln -sf /usr/share/zoneinfo/UTC /etc/localtime")

    #install some necessary base deps
    runcmd("apt-get update")
    runcmd("apt-get -y install git-core software-properties-common python-software-properties build-essential ssl-cert ntp runit")
    
    #install node-js
    #node-gyp building has ...issues out of the box on Ubuntu... use Chris Lea's nodejs build instead, which is newer
    runcmd("apt-get -y remove nodejs npm gyp")
    runcmd("add-apt-repository -y ppa:chris-lea/node.js")
    runcmd("apt-get update")
    runcmd("apt-get -y install nodejs") #includes npm
    gypdir = None
    try:
        import gyp
        gypdir = os.path.dirname(gyp.__file__)
    except:
        pass
    else:
        runcmd("mv %s %s_bkup" % (gypdir, gypdir))
        #^ fix for https://github.com/TooTallNate/node-gyp/issues/363

    #Create csfr user, under which the files will be stored, and who will own the files, etc
    try:
        pwd.getpwnam(USERNAME)
    except:
        logging.info("Creating user '%s' ..." % USERNAME)
        runcmd("adduser --system --disabled-password --shell /bin/false --group %s" % USERNAME)
        
    #Create csfrd user (to run csfrd, csfrblockd, insight, saffroncoind, nginx) if not already made
    try:
        pwd.getpwnam(DAEMON_USERNAME)
    except:
        logging.info("Creating user '%s' ..." % DAEMON_USERNAME)
        runcmd("adduser --system --disabled-password --shell /bin/false --ingroup nogroup --home %s %s" % (USER_HOMEDIR, DAEMON_USERNAME))
    
    #add the run_as_user to the csfr group
    runcmd("adduser %s %s" % (run_as_user, USERNAME))
    
    #Check out csfrd-build repo under this user's home dir and use that for the build
    git_repo_clone("csfrd_build", "https://github.com/saffroncoin/csfrd_build.git",
        os.path.join(USER_HOMEDIR, "csfrd_build"), branch, for_user=run_as_user)

    #enhance fd limits for the csfrd user
    runcmd("cp -af %s/linux/other/csfrd_security_limits.conf /etc/security/limits.d/" % dist_path)

def do_backend_rpc_setup(run_as_user, branch, base_path, dist_path, run_mode, backend_rpc_mode):
    """Installs and configures saffroncoind"""
    backend_rpc_password = pass_generator()
    backend_rpc_password_testnet = pass_generator()

    if backend_rpc_mode == 's': #saffroncoind
        #Install saffroncoind
        SAFFRONCOIND_VER = "1.3.4"
        runcmd("rm -rf /tmp/saffroncoind.tar.gz /tmp/saffroncoin-%s-linux" % SAFFRONCOIND_VER)
        runcmd("wget -O /tmp/saffroncoind.tar.gz https://github.com/saffroncoin/saffroncoin/releases/download/%s/saffroncoin-binary-%s.tar.gz --no-check-certificate" % (SAFFRONCOIND_VER, SAFFRONCOIND_VER))
        runcmd("tar -C /tmp -zxvf /tmp/saffroncoind.tar.gz")
        runcmd("cp -af /tmp/saffroncoind /usr/bin")
        runcmd("rm -rf /tmp/saffroncoind.tar.gz /tmp/saffroncoind")
    
        #Do basic inital saffroncoin config (for both testnet and mainnet)
        runcmd("mkdir -p ~%s/.saffroncoin ~%s/.saffroncoin-testnet" % (USERNAME, USERNAME))
        if not os.path.exists(os.path.join(USER_HOMEDIR, '.saffroncoin', 'saffroncoin.conf')):
            runcmd(r"""bash -c 'echo -e "rpcuser=rpc\nrpcpassword=%s\nserver=1\ndaemon=1\ntxindex=1" > ~%s/.saffroncoin/saffroncoin.conf'""" % (
                backend_rpc_password, USERNAME))
        else: #grab the existing RPC password
            backend_rpc_password = subprocess.check_output(
                r"""bash -c "cat ~%s/.saffroncoin/saffroncoin.conf | sed -n 's/.*rpcpassword=\([^ \n]*\).*/\1/p'" """ % USERNAME, shell=True).strip().decode('utf-8')
        if not os.path.exists(os.path.join(USER_HOMEDIR, '.saffroncoin-testnet', 'saffroncoin.conf')):
            runcmd(r"""bash -c 'echo -e "rpcuser=rpc\nrpcpassword=%s\nserver=1\ndaemon=1\ntxindex=1\ntestnet=1" > ~%s/.saffroncoin-testnet/saffroncoin.conf'""" % (
                backend_rpc_password_testnet, USERNAME))
        else:
            backend_rpc_password_testnet = subprocess.check_output(
                r"""bash -c "cat ~%s/.saffroncoin-testnet/saffroncoin.conf | sed -n 's/.*rpcpassword=\([^ \n]*\).*/\1/p'" """
                % USERNAME, shell=True).strip().decode('utf-8')

        #remove pyrpcwallet startup scripts if present
        runcmd("rm -f /etc/service/pyrpcwallet /etc/service/pyrpcwallet-testnet")
        #install logrotate file
        runcmd("cp -dRf --preserve=mode %s/linux/logrotate/saffroncoind /etc/logrotate.d/saffroncoind" % dist_path)
        #set permissions
        runcmd("chown -R %s:%s ~%s/.saffroncoin ~%s/.saffroncoin-testnet" % (DAEMON_USERNAME, USERNAME, USERNAME, USERNAME))
        #set up runit startup scripts
        config_runit_for_service(dist_path, "saffroncoind", enabled=run_mode in ['m', 'b'])
        config_runit_for_service(dist_path, "saffroncoind-testnet", enabled=run_mode in ['t', 'b'])
    else:
        assert backend_rpc_mode == 'p'
        #checkout pyrpcwallet
        git_repo_clone("pyrpcwallet", "https://github.com/saffroncoin/pyrpcwallet.git",
            os.path.join(USER_HOMEDIR, "pyrpcwallet"), branch="master", for_user=run_as_user, hash="bdeef54ca74ebd5990350d62b57280d970af3c04")
        #remove saffroncoind startup scripts if present
        runcmd("rm -f /etc/service/saffroncoind /etc/service/saffroncoind-testnet")
        #change passwords
        modify_config(r'^RPC_PASSWORD=.*?$', 'RPC_PASSWORD=' + backend_rpc_password, '/etc/sv/pyrpcwallet/run')
        modify_config(r'^RPC_PASSWORD=.*?$', 'RPC_PASSWORD=' + backend_rpc_password_testnet, '/etc/sv/pyrpcwallet-testnet/run')
        #set permissions
        runcmd("mkdir -p ~%s/pyrpcwallet/log ~%s/pyrpcwallet/log-testnet" % (USERNAME, USERNAME))
        runcmd("chown -R %s:%s ~%s/pyrpcwallet ~%s/pyrpcwallet/log ~%s/pyrpcwallet/log-testnet" % (DAEMON_USERNAME, USERNAME, USERNAME, USERNAME, USERNAME))
        #set up runit startup scripts
        config_runit_for_service(dist_path, "pyrpcwallet", enabled=run_mode in ['m', 'b'])
        config_runit_for_service(dist_path, "pyrpcwallet-testnet", enabled=run_mode in ['t', 'b'])
    
    return backend_rpc_password, backend_rpc_password_testnet

def do_csfr_setup(role, run_as_user, docker, branch, base_path, dist_path, run_mode, backend_rpc_password,
backend_rpc_password_testnet, csfrd_public, csfrwallet_support_email):
    """Installs and configures csfrd and csfrblockd"""
    csfrd_rpc_password = '1234' if role == 'csfrd_only' and csfrd_public == 'y' else pass_generator()
    csfrd_rpc_password_testnet = '1234' if role == 'csfrd_only' and csfrd_public == 'y' else pass_generator()
    
    #Run setup.py (as the cSFR user, who runs it sudoed) to install and set up csfrd, csfrblockd
    # as -y is specified, this will auto install csfrblockd full node (mongo and redis) as well as setting
    # csfrd/csfrblockd to start up at startup for both mainnet and testnet (we will override this as necessary
    # based on run_mode later in this function)
    runcmd("sudo python3 ~%s/csfrd_build/setup.py --noninteractive --branch=%s %s --with-testnet --for-user=%s %s" % (
        USERNAME, branch, "" if not docker else '', USERNAME, '--with-csfrblockd' if role != 'csfrd_only' else ''))
    runcmd("cd ~%s/csfrd_build && git config core.sharedRepository group && find ~%s/csfrd_build -type d -print0 | xargs -0 chmod g+s" % (
        USERNAME, USERNAME)) #to allow for group git actions 
    runcmd("chown -R %s:%s ~%s/csfrd_build" % (USERNAME, USERNAME, USERNAME)) #just in case
    runcmd("chmod -R u+rw,g+rw,o+r,o-w ~%s/csfrd_build" % USERNAME) #just in case
    
    #now change the csfrd directories to be owned by the csfrd user (and the csfr group),
    # so that the csfrd account can write to the database, saved image files (csfrblockd), log files, etc
    runcmd("mkdir -p ~%s/.config/csfrd ~%s/.config/csfrd-testnet" % (USERNAME, USERNAME))    
    runcmd("chown -R %s:%s ~%s/.config/csfrd ~%s/.config/csfrd-testnet" % (
        DAEMON_USERNAME, USERNAME, USERNAME, USERNAME))
    runcmd("sed -ri \"s/USER=%s/USER=%s/g\" /etc/sv/csfrd/run /etc/sv/csfrd-testnet/run" % (
        USERNAME, DAEMON_USERNAME))

    #modify the default stored saffroncoind passwords in csfrd.conf
    modify_cp_config(r'^(backend|saffroncoind)\-rpc\-password=.*?$',
        'backend-rpc-password=%s' % backend_rpc_password, config='csfrd', net='mainnet', for_user=USERNAME)
    modify_cp_config(r'^(backend|saffroncoind)\-rpc\-password=.*?$',
        'backend-rpc-password=%s' % backend_rpc_password_testnet, config='csfrd', net='testnet', for_user=USERNAME)

    #modify the csfrd API rpc password in csfrd.conf
    modify_cp_config(r'^rpc\-password=.*?$', 'rpc-password=%s' % csfrd_rpc_password,
        config='csfrd', net='mainnet', for_user=USERNAME)
    modify_cp_config(r'^rpc\-password=.*?$', 'rpc-password=%s' % csfrd_rpc_password_testnet,
        config='csfrd', net='testnet', for_user=USERNAME)

    if role == 'csfrd_only' and csfrd_public == 'y':
        modify_cp_config(r'^rpc\-host=.*?$', 'rpc-host=0.0.0.0', config='csfrd', for_user=USERNAME)
    
    #disable upstart scripts from autostarting on system boot if necessary
    if run_mode not in ['m', 'b']:
        runcmd("rm -f /etc/service/csfrd")
    if run_mode not in ['t', 'b']:
        runcmd("rm -f /etc/service/csfrd-testnet")
        
    if role != 'csfrd_only':
        #now change the csfrblockd directories to be owned by the csfrd user (and the csfr group),
        runcmd("mkdir -p ~%s/.config/csfrblockd ~%s/.config/csfrblockd-testnet" % (USERNAME, USERNAME))    
        runcmd("chown -R %s:%s ~%s/.config/csfrblockd ~%s/.config/csfrblockd-testnet" % (
            DAEMON_USERNAME, USERNAME, USERNAME, USERNAME))
        runcmd("sed -ri \"s/USER=%s/USER=%s/g\" /etc/sv/csfrblockd/run /etc/sv/csfrblockd-testnet/run" % (
            USERNAME, DAEMON_USERNAME))
        
        #modify the default stored saffroncoind passwords in csfrblockd.conf
        modify_cp_config(r'^(backend|saffroncoind)\-rpc\-password=.*?$',
            'backend-rpc-password=%s' % backend_rpc_password, config='csfrblockd', net='mainnet', for_user=USERNAME)
        modify_cp_config(r'^(backend|saffroncoind)\-rpc\-password=.*?$',
            'backend-rpc-password=%s' % backend_rpc_password_testnet, config='csfrblockd', net='testnet', for_user=USERNAME)
    
        #modify the csfrd API rpc password in csfrblockd.conf
        modify_cp_config(r'^csfrd\-rpc\-password=.*?$',
            'csfrd-rpc-password=%s' % csfrd_rpc_password, config='csfrblockd', net='mainnet', for_user=USERNAME)
        modify_cp_config(r'^csfrd\-rpc\-password=.*?$',
            'csfrd-rpc-password=%s' % csfrd_rpc_password_testnet, config='csfrblockd', net='testnet', for_user=USERNAME)
        
        #role-specific csfrblockd.conf values
        modify_cp_config(r'^auto\-btc\-escrow\-enable=.*?$', 'auto-btc-escrow-enable=%s' %
            ('1' if role == 'btcpayescrow' else '0'), config='csfrblockd', for_user=USERNAME)
        modify_cp_config(r'^armory\-utxsvr\-enable=.*?$', 'armory-utxsvr-enable=%s' % 
            ('1' if role == 'csfrwallet' else '0'), config='csfrblockd', for_user=USERNAME)
        if role == 'csfrwallet':
            modify_cp_config(r'^support\-email=.*?$', 'support-email=%s' % csfrwallet_support_email,
                config='csfrblockd', for_user=USERNAME) #may be blank string

        #disable upstart scripts from autostarting on system boot if necessary
        if run_mode not in ['m', 'b']:
            runcmd("rm -f /etc/service/csfrblockd")
        if run_mode not in ['t', 'b']:
            runcmd("rm -f /etc/service/csfrblockd-testnet")

def do_blockchain_service_setup(run_as_user, base_path, dist_path, run_mode, blockchain_service):
    def do_insight_setup():
        """This installs and configures insight"""
        assert blockchain_service
        
        git_repo_clone("insight-api", "https://github.com/bitpay/insight-api.git",
            os.path.join(USER_HOMEDIR, "insight-api"), branch="master", for_user=run_as_user,
            hash="0ca0fdf6991c023fa1cd63c6cc44c480c6c8b53f") #insight-api 0.2.11
        runcmd("rm -rf ~%s/insight-api/node-modules && cd ~%s/insight-api && npm install" % (USERNAME, USERNAME))
        
        #install logrotate file
        runcmd("cp -af %s/linux/logrotate/insight /etc/logrotate.d/insight" % dist_path)
        #permissions, etc.
        runcmd("mkdir -p ~%s/insight-api/db ~%s/insight-api/log ~%s/insight-api/log-testnet" % (USERNAME, USERNAME, USERNAME))
        runcmd("chown -R %s:%s ~%s/insight-api" % (USERNAME, USERNAME, USERNAME))
        runcmd("chown -R %s:%s ~%s/insight-api/db ~%s/insight-api/log ~%s/insight-api/log-testnet" % (
            DAEMON_USERNAME, USERNAME, USERNAME, USERNAME, USERNAME))
        #modify config
        modify_cp_config(r'^blockchain\-service\-name=.*?$', 'blockchain-service-name=insight', config='both', for_user=USERNAME)
        #install runit scripts
        config_runit_for_service(dist_path, "insight", enabled=run_mode in ['m', 'b'])
        config_runit_for_service(dist_path, "insight-testnet", enabled=run_mode in ['t', 'b'])
        
    def do_blockr_setup():
        modify_cp_config(r'^blockchain\-service\-name=.*?$', 'blockchain-service-name=blockr', config='both', for_user=USERNAME)
    
    if blockchain_service == 'i':
        do_insight_setup()
    else: #insight not being used as blockchain service
        runcmd("rm -rf /etc/sv/insight /etc/sv/insight-testnet") # so insight doesn't start if it was in use before
        do_blockr_setup()

def do_nginx_setup(run_as_user, base_path, dist_path, enable=True):
    if not enable:
        runcmd("apt-get -y remove nginx-openresty")
        return
    
    #Build and install nginx (openresty) on Ubuntu
    #Most of these build commands from http://brian.akins.org/blog/2013/03/19/building-openresty-on-ubuntu/
    OPENRESTY_VER = "1.7.2.1"

    #uninstall nginx if already present
    runcmd("apt-get -y remove nginx")
    #install deps
    runcmd("apt-get -y install make ruby1.9.1 ruby1.9.1-dev git-core libpcre3-dev libxslt1-dev libgd2-xpm-dev libgeoip-dev unzip zip build-essential libssl-dev")
    runcmd("gem install fpm")
    #grab openresty and compile
    runcmd("rm -rf /tmp/openresty /tmp/ngx_openresty-* /tmp/nginx-openresty.tar.gz /tmp/nginx-openresty*.deb")
    runcmd('''wget -O /tmp/nginx-openresty.tar.gz http://openresty.org/download/ngx_openresty-%s.tar.gz''' % OPENRESTY_VER)
    runcmd("tar -C /tmp -zxvf /tmp/nginx-openresty.tar.gz")
    runcmd('''cd /tmp/ngx_openresty-%s && ./configure \
--with-luajit \
--sbin-path=/usr/sbin/nginx \
--conf-path=/etc/nginx/nginx.conf \
--error-log-path=/var/log/nginx/error.log \
--http-client-body-temp-path=/var/lib/nginx/body \
--http-fastcgi-temp-path=/var/lib/nginx/fastcgi \
--http-log-path=/var/log/nginx/access.log \
--http-proxy-temp-path=/var/lib/nginx/proxy \
--http-scgi-temp-path=/var/lib/nginx/scgi \
--http-uwsgi-temp-path=/var/lib/nginx/uwsgi \
--lock-path=/var/lock/nginx.lock \
--pid-path=/var/run/nginx.pid \
--with-http_geoip_module \
--with-http_gzip_static_module \
--with-http_realip_module \
--with-http_ssl_module \
--with-http_sub_module \
--with-http_xslt_module \
--with-ipv6 \
--with-sha1=/usr/include/openssl \
--with-md5=/usr/include/openssl \
--with-http_stub_status_module \
--with-http_secure_link_module \
--with-http_sub_module && make''' % OPENRESTY_VER)
    #set up the build environment
    runcmd('''cd /tmp/ngx_openresty-%s && make install DESTDIR=/tmp/openresty \
&& mkdir -p /tmp/openresty/var/lib/nginx \
&& install -m 0755 -D %s/linux/runit/nginx/run /tmp/openresty/etc/sv/nginx/run \
&& install -m 0755 -D %s/linux/nginx/nginx.conf /tmp/openresty/etc/nginx/nginx.conf \
&& install -m 0755 -D %s/linux/nginx/csfrblock.conf /tmp/openresty/etc/nginx/sites-enabled/csfrblock.conf \
&& install -m 0755 -D %s/linux/nginx/csfrblock_api.inc /tmp/openresty/etc/nginx/sites-enabled/csfrblock_api.inc \
&& install -m 0755 -D %s/linux/nginx/csfrblock_api_cache.inc /tmp/openresty/etc/nginx/sites-enabled/csfrblock_api_cache.inc \
&& install -m 0755 -D %s/linux/nginx/csfrblock_socketio.inc /tmp/openresty/etc/nginx/sites-enabled/csfrblock_socketio.inc \
&& install -m 0755 -D %s/linux/logrotate/nginx /tmp/openresty/etc/logrotate.d/nginx''' % (
    OPENRESTY_VER, dist_path, dist_path, dist_path, dist_path, dist_path, dist_path, dist_path))
    #package it up using fpm
    runcmd('''cd /tmp && fpm -s dir -t deb -n nginx-openresty -v %s --iteration 1 -C /tmp/openresty \
--description "openresty %s" \
--conflicts nginx \
--conflicts nginx-common \
-d libxslt1.1 \
-d libgeoip1 \
-d geoip-database \
-d libpcre3 \
--config-files /etc/nginx/nginx.conf \
--config-files /etc/nginx/sites-enabled/csfrblock.conf \
--config-files /etc/nginx/fastcgi.conf.default \
--config-files /etc/nginx/win-utf \
--config-files /etc/nginx/fastcgi_params \
--config-files /etc/nginx/nginx.conf \
--config-files /etc/nginx/koi-win \
--config-files /etc/nginx/nginx.conf.default \
--config-files /etc/nginx/mime.types.default \
--config-files /etc/nginx/koi-utf \
--config-files /etc/nginx/uwsgi_params \
--config-files /etc/nginx/uwsgi_params.default \
--config-files /etc/nginx/fastcgi_params.default \
--config-files /etc/nginx/mime.types \
--config-files /etc/nginx/scgi_params.default \
--config-files /etc/nginx/scgi_params \
--config-files /etc/nginx/fastcgi.conf \
etc usr var''' % (OPENRESTY_VER, OPENRESTY_VER))
    #now install the .deb package that was created (along with its deps)
    runcmd("apt-get -y install libxslt1.1 libgeoip1 geoip-database libpcre3")
    runcmd("dpkg -i /tmp/nginx-openresty_%s-1_amd64.deb" % OPENRESTY_VER)
    #remove any .dpkg-old or .dpkg-dist files that might have been installed out of the nginx config dir
    runcmd("rm -f /etc/nginx/sites-enabled/*.dpkg-old /etc/nginx/sites-enabled/*.dpkg-dist")
    #clean up after ourselves
    runcmd("rm -rf /tmp/openresty /tmp/ngx_openresty-* /tmp/nginx-openresty.tar.gz /tmp/nginx-openresty*.deb")
    #set up init
    runcmd("ln -sf /etc/sv/nginx /etc/service/")

def do_armory_utxsvr_setup(run_as_user, base_path, dist_path, run_mode, enable=True):
    runcmd("apt-get -y install xvfb python-qt4 python-twisted python-psutil xdg-utils hicolor-icon-theme")
    runcmd("rm -f /tmp/armory.deb")
    runcmd("wget -O /tmp/armory.deb https://s3.amazonaws.com/bitcoinarmory-releases/armory_0.92.1_ubuntu-64bit.deb")
    runcmd("mkdir -p /usr/share/desktop-directories/") #bug fix (see http://askubuntu.com/a/406015)
    runcmd("dpkg -i /tmp/armory.deb")
    runcmd("rm -f /tmp/armory.deb")

    runcmd("mkdir -p ~%s/.armory ~%s/.armory/log ~%s/.armory/log-testnet" % (USERNAME, USERNAME, USERNAME))
    runcmd("chown -R %s:%s ~%s/.armory" % (DAEMON_USERNAME, USERNAME, USERNAME))
    
    runcmd("sudo ln -sf ~%s/.saffroncoin-testnet/testnet3 ~%s/.saffroncoin/" % (USERNAME, USERNAME))
    #^ ghetto hack, as armory has hardcoded dir settings in certain place
    
    #make a short script to launch armory_utxsvr
    f = open("/usr/local/bin/armory_utxsvr", 'w')
    f.write("#!/bin/sh\n%s/run.py armory_utxsvr \"$@\"" % base_path)
    f.close()
    runcmd("chmod +x /usr/local/bin/armory_utxsvr")

    #Set up upstart scripts (will be disabled later from autostarting on system startup if necessary)
    config_runit_for_service(dist_path, "armory_utxsvr", enabled=enable and run_mode in ['m', 'b'])
    config_runit_for_service(dist_path, "armory_utxsvr-testnet", enabled=enable and run_mode in ['t', 'b'])

def do_csfrwallet_setup(run_as_user, branch, updateOnly=False):
    #check out csfrwallet from git
    git_repo_clone("csfrwallet", "https://github.com/saffroncoin/csfrwallet.git",
        os.path.join(USER_HOMEDIR, "csfrwallet"), branch, for_user=run_as_user)
    if not updateOnly:
        runcmd("npm install -g grunt-cli bower")
    runcmd("cd ~%s/csfrwallet/src && bower --allow-root --config.interactive=false install" % USERNAME)
    runcmd("cd ~%s/csfrwallet && npm install -g" % USERNAME)
    runcmd("cd ~%s/csfrwallet && grunt build --force" % USERNAME) #will generate the minified site
    runcmd("chown -R %s:%s ~%s/csfrwallet" % (USERNAME, USERNAME, USERNAME)) #just in case
    runcmd("chmod -R u+rw,g+rw,o+r,o-w ~%s/csfrwallet" % USERNAME) #just in case

def do_newrelic_setup(run_as_user, base_path, dist_path, run_mode):
    NR_PREFS_LICENSE_KEY_PATH = "/etc/newrelic/LICENSE_KEY"
    NR_PREFS_HOSTNAME_PATH = "/etc/newrelic/HOSTNAME"
    
    runcmd("mkdir -p /etc/newrelic /var/log/newrelic /var/run/newrelic")
    runcmd("chown %s:%s /etc/newrelic /var/log/newrelic /var/run/newrelic" % (DAEMON_USERNAME, USERNAME))
    
    #try to find existing license key
    nr_license_key = None
    if os.path.exists(NR_PREFS_LICENSE_KEY_PATH):
        nr_license_key = open(NR_PREFS_LICENSE_KEY_PATH).read().strip()
    else:
        while True:
            nr_license_key = input("Enter New Relic license key (or blank to not setup New Relic): ") #gather license key
            nr_license_key = nr_license_key.strip()
            if not nr_license_key:
                return #skipping new relic
            nr_license_key_confirm = ask_question("You entererd '%s', is that right? (Y/n): " % nr_license_key, ('y', 'n'), 'y') 
            if nr_license_key_confirm == 'y': break
        open(NR_PREFS_LICENSE_KEY_PATH, 'w').write(nr_license_key)
    assert nr_license_key
    logging.info("NewRelic license key: %s" % nr_license_key)

    #try to find existing app prefix
    nr_hostname = None
    if os.path.exists(NR_PREFS_HOSTNAME_PATH):
        nr_hostname = open(NR_PREFS_HOSTNAME_PATH).read().strip()
    else:
        while True:
            nr_hostname = input("Enter newrelic hostname/app prefix (e.g. 'cw01'): ") #gather app prefix
            nr_hostname = nr_hostname.strip()
            nr_hostname_confirm = ask_question("You entererd '%s', is that right? (Y/n): " % nr_hostname, ('y', 'n'), 'y')
            if nr_hostname_confirm == 'y': break
        open(NR_PREFS_HOSTNAME_PATH, 'w').write(nr_hostname)
    assert nr_hostname
    logging.info("NewRelic hostname/app prefix: %s" % nr_hostname)

    #install some deps...
    runcmd("sudo apt-get -y install libyaml-dev")
    
    
    #install/setup server agent
    runcmd("add-apt-repository \"deb http://apt.newrelic.com/debian/ newrelic non-free\"")
    runcmd("wget -O- https://download.newrelic.com/548C16BF.gpg | apt-key add -")
    runcmd("apt-get update")
    runcmd("apt-get -y install newrelic-sysmond")
    runcmd("cp -af %s/linux/newrelic/nrsysmond.cfg.template /etc/newrelic/nrsysmond.cfg" % dist_path)
    runcmd("sed -ri \"s/\!LICENSE_KEY\!/%s/g\" /etc/newrelic/nrsysmond.cfg" % nr_license_key)
    runcmd("sed -ri \"s/\!HOSTNAME\!/%s/g\" /etc/newrelic/nrsysmond.cfg" % nr_hostname)
    runcmd("/etc/init.d/newrelic-sysmond restart")
    
    #install/setup meetme agent (mongo, redis)
    runcmd("pip install newrelic_plugin_agent pymongo")
    runcmd("cp -af %s/linux/newrelic/newrelic-plugin-agent.cfg.template /etc/newrelic/newrelic-plugin-agent.cfg" % dist_path)
    runcmd("sed -ri \"s/\!LICENSE_KEY\!/%s/g\" /etc/newrelic/newrelic-plugin-agent.cfg" % nr_license_key)
    runcmd("sed -ri \"s/\!HOSTNAME\!/%s/g\" /etc/newrelic/newrelic-plugin-agent.cfg" % nr_hostname)
    runcmd("ln -sf %s/linux/newrelic/init/newrelic-plugin-agent /etc/init.d/newrelic-plugin-agent" % dist_path)
    runcmd("update-rc.d newrelic-plugin-agent defaults")
    runcmd("/etc/init.d/newrelic-plugin-agent restart")
    
    #install/setup nginx agent
    runcmd("sudo apt-get -y install ruby ruby-bundler")
    runcmd("rm -rf /tmp/newrelic_nginx_agent.tar.gz /opt/newrelic_nginx_agent")
    #runcmd("wget -O /tmp/newrelic_nginx_agent.tar.gz http://nginx.com/download/newrelic/newrelic_nginx_agent.tar.gz")
    #runcmd("tar -C /opt -zxvf /tmp/newrelic_nginx_agent.tar.gz")
    runcmd("git clone https://github.com/crowdlab-uk/newrelic-nginx-agent.git /opt/newrelic_nginx_agent")
    runcmd("cd /opt/newrelic_nginx_agent && bundle install")
    runcmd("cp -af %s/linux/newrelic/newrelic_nginx_plugin.yml.template /opt/newrelic_nginx_agent/config/newrelic_plugin.yml" % dist_path)
    runcmd("sed -ri \"s/\!LICENSE_KEY\!/%s/g\" /opt/newrelic_nginx_agent/config/newrelic_plugin.yml" % nr_license_key)
    runcmd("sed -ri \"s/\!HOSTNAME\!/%s/g\" /opt/newrelic_nginx_agent/config/newrelic_plugin.yml" % nr_hostname)
    runcmd("ln -sf /opt/newrelic_nginx_agent/newrelic_nginx_agent.daemon /etc/init.d/newrelic_nginx_agent")
    runcmd("update-rc.d newrelic_nginx_agent defaults")
    runcmd("/etc/init.d/newrelic_nginx_agent restart")
    
def do_security_setup(run_as_user, branch, base_path, dist_path, enable=True):
    """Some helpful security-related tasks, to tighten up the box"""
    
    if not enable:
        #disable security setup if enabled
        runcmd("apt-get -y remove unattended-upgrades fail2ban psad rkhunter chkrootkit logwatch apparmor auditd iwatch")
        return
    
    #modify host.conf
    modify_config(r'^nospoof on$', 'nospoof on', '/etc/host.conf')
    
    #enable automatic security updates
    runcmd("apt-get -y install unattended-upgrades")
    runcmd('''bash -c "echo -e 'APT::Periodic::Update-Package-Lists "1";\nAPT::Periodic::Unattended-Upgrade "1";' > /etc/apt/apt.conf.d/20auto-upgrades" ''')
    runcmd("dpkg-reconfigure -fnoninteractive -plow unattended-upgrades")
    
    #sysctl
    runcmd("install -m 0644 -o root -g root -D %s/linux/other/sysctl_rules.conf /etc/sysctl.d/60-tweaks.conf" % dist_path)

    #set up fail2ban
    runcmd("apt-get -y install fail2ban")
    runcmd("install -m 0644 -o root -g root -D %s/linux/other/fail2ban.jail.conf /etc/fail2ban/jail.d/csfrblock.conf" % dist_path)
    runcmd("service fail2ban restart")
    
    #set up psad
    runcmd("apt-get -y install psad")
    modify_config(r'^ENABLE_AUTO_IDS\s+?N;$', 'ENABLE_AUTO_IDS\tY;', '/etc/psad/psad.conf')
    modify_config(r'^ENABLE_AUTO_IDS_EMAILS\s+?Y;$', 'ENABLE_AUTO_IDS_EMAILS\tN;', '/etc/psad/psad.conf')
    for f in ['/etc/ufw/before.rules', '/etc/ufw/before6.rules']:
        modify_config(r'^# End required lines.*?# allow all on loopback$',
            '# End required lines\n\n#CUSTOM: for psad\n-A INPUT -j LOG\n-A FORWARD -j LOG\n\n# allow all on loopback',
            f, dotall=True)
    runcmd("psad -R && psad --sig-update")
    runcmd("service ufw restart")
    runcmd("service psad restart")
    
    #set up chkrootkit, rkhunter
    runcmd("apt-get -y install rkhunter chkrootkit")
    runcmd('bash -c "rkhunter --update; exit 0"')
    runcmd("rkhunter --propupd")
    runcmd('bash -c "rkhunter --check --sk; exit 0"')
    runcmd("rkhunter --propupd")
    
    #logwatch
    runcmd("apt-get -y install logwatch libdate-manip-perl")
    
    #apparmor
    runcmd("apt-get -y install apparmor apparmor-profiles")
    
    #auditd
    #note that auditd will need a reboot to fully apply the rules, due to it operating in "immutable mode" by default
    runcmd("apt-get -y install auditd audispd-plugins")
    runcmd("install -m 0640 -o root -g root -D %s/linux/other/audit.rules /etc/audit/rules.d/csfrblock.rules" % dist_path)
    modify_config(r'^USE_AUGENRULES=.*?$', 'USE_AUGENRULES="yes"', '/etc/default/auditd')
    runcmd("service auditd restart")

    #iwatch
    runcmd("apt-get -y install iwatch")
    modify_config(r'^START_DAEMON=.*?$', 'START_DAEMON=true', '/etc/default/iwatch')
    runcmd("install -m 0644 -o root -g root -D %s/linux/other/iwatch.xml /etc/iwatch/iwatch.xml" % dist_path)
    modify_config(r'guard email="root@localhost"', 'guard email="noreply@%s"' % socket.gethostname(), '/etc/iwatch/iwatch.xml')
    runcmd("service iwatch restart")

def find_configured_services():
    services = ["saffroncoind", "saffroncoind-testnet", "insight", "insight-testnet", "csfrd", "csfrd-testnet",
        "csfrblockd", "csfrblockd-testnet", "armory_utxsvr", "armory_utxsvr-testnet"]
    configured_services = []
    for s in services:
        if os.path.exists("/etc/service/%s" % s):
            configured_services.append(s)
    return configured_services

def command_services(command, prompt=False):
    assert command in ("stop", "restart")
    
    if prompt:
        confirmation = ask_question("%s services? (y/N)" % command.capitalize(), ('y', 'n',), 'n')
        if confirmation == 'n':
            return False
    
    logging.warn("STOPPING SERVICES" if command == 'stop' else "RESTARTING SERVICES")
    
    if os.path.exists("/etc/init.d/iwatch"):
        runcmd("sv %s iwatch" % command, abort_on_failure=False)
        
    configured_services = find_configured_services()
    for s in configured_services:
        runcmd("sv %s %s" % (command, s), abort_on_failure=False)
    return True

def gather_build_questions(answered_questions, noninteractive, docker):
    if 'role' not in answered_questions and noninteractive:
        answered_questions['role'] = '1' 
    elif 'role' not in answered_questions:
        role = ask_question("Enter the number for the role you want to build:\n"
                + "\t1: SFRDirect wallet server\n\t2: Vending machine\n\t3: Blockexplorer server\n"
                + "\t4: csfrd-only\n\t5: BTCPay Escrow Server\n"
                + "Your choice",
            ('1', '2', '3', '4', '5'), '1')
        if role == '1':
            role = 'csfrwallet'
            role_desc = "SFRDirect wallet server"
        elif role == '2':
            role = 'vendingmachine'
            role_desc = "Vending machine/gateway"
        elif role == '3':
            role = 'blockexplorer'
            role_desc = "Block explorer server"
        elif role == '4':
            role = 'csfrd_only'
            role_desc = "csfrd server"
        elif role == '5':
            role = 'btcpayescrow'
            role_desc = "BTCPay escrow server"
        print("\tBuilding a %s" % role_desc)
        answered_questions['role'] = role
    assert answered_questions['role'] in QUESTION_FLAGS['role']
    if answered_questions['role'] in ('vendingmachine', 'blockexplorer'):
        raise NotImplementedError("This role not implemented yet...")

    if 'branch' not in answered_questions and noninteractive:
        answered_questions['branch'] = 'master' 
    elif 'branch' not in answered_questions:
        branch = ask_question("Build from branch (M)aster or (d)evelop? (M/d)", ('m', 'd'), 'm')
        if branch == 'm': branch = 'master'
        elif branch == 'd': branch = 'develop'
        print("\tWorking with branch: %s" % branch)
        answered_questions['branch'] = branch
    assert answered_questions['branch'] in QUESTION_FLAGS['branch']

    if 'run_mode' not in answered_questions and noninteractive:
        answered_questions['run_mode'] = 'b' 
    elif 'run_mode' not in answered_questions:
        answered_questions['run_mode'] = ask_question(
            "Run as (t)estnet node, (m)ainnet node, or (B)oth? (t/m/B)", ('t', 'm', 'b'), 'b')
        print("\tSetting up to run on %s" % ('testnet' if answered_questions['run_mode'].lower() == 't' 
            else ('mainnet' if answered_questions['run_mode'].lower() == 'm' else 'testnet and mainnet')))
    assert answered_questions['run_mode'] in QUESTION_FLAGS['run_mode']
    
    if 'backend_rpc_mode' not in answered_questions and noninteractive:
        answered_questions['backend_rpc_mode'] = 's' 
    elif 'backend_rpc_mode' not in answered_questions:
        answered_questions['backend_rpc_mode'] = ask_question(
            "Backend RPC services, use (S)affroncoind or (p)yrpcwallet? (S/p)", ('s', 'p'), 's')
        print("\tUsing %s" % ('saffroncoind' if answered_questions['backend_rpc_mode'] == 's' else 'pyrpcwallet'))
    assert answered_questions['backend_rpc_mode'] in QUESTION_FLAGS['backend_rpc_mode']

    if 'blockchain_service' not in answered_questions and noninteractive:
        answered_questions['blockchain_service'] = 'b' 
    elif 'blockchain_service' not in answered_questions:
        answered_questions['blockchain_service'] = ask_question(
            "Auxiliary blockchain services, use (B)lockr.io (remote) or (i)nsight (local)? (B/i)", ('b', 'i'), 'b')
        print("\tUsing %s" % ('blockr.io' if answered_questions['blockchain_service'] == 'b' else 'insight'))
    assert answered_questions['blockchain_service'] in QUESTION_FLAGS['blockchain_service']
    
    if answered_questions['role'] == 'csfrd_only':
        if 'csfrd_public' not in answered_questions and noninteractive:
            answered_questions['csfrd_public'] = 'y' 
        elif 'csfrd_public' not in answered_questions:
            answered_questions['csfrd_public'] = ask_question(
                "Enable public csfrd setup (listen on all network interfaces w/ rpc/1234 user) (Y/n)", ('y', 'n'), 'y')
        else:
            answered_questions['csfrd_public'] = answered_questions.get('csfrd_public', 'n') #does not apply
        assert answered_questions['csfrd_public'] in QUESTION_FLAGS['csfrd_public']
    else: answered_questions['csfrd_public'] = None

    if answered_questions['role'] == 'csfrwallet':
        csfrwallet_support_email = None
        if 'csfrwallet_support_email' not in answered_questions and noninteractive:
            answered_questions['csfrwallet_support_email'] = '' 
        elif 'csfrwallet_support_email' not in answered_questions:
            while True:
                csfrwallet_support_email = input("Email address where support cases should go (blank to disable): ")
                csfrwallet_support_email = csfrwallet_support_email.strip()
                if csfrwallet_support_email:
                    csfrwallet_support_email_confirm = ask_question(
                        "You entererd '%s', is that right? (Y/n): " % csfrwallet_support_email, ('y', 'n'), 'y') 
                    if csfrwallet_support_email_confirm == 'y': break
                else: break
            answered_questions['csfrwallet_support_email'] = csfrwallet_support_email
        else:
            answered_questions['csfrwallet_support_email'] = answered_questions.get('csfrwallet_support_email', '').strip()
    else: answered_questions['csfrwallet_support_email'] = None

    if 'security_hardening' not in answered_questions and noninteractive:
        answered_questions['security_hardening'] = 'y' 
    elif 'security_hardening' not in answered_questions:
        if not docker:
            answered_questions['security_hardening'] = ask_question("Set up security hardening? (Y/n)", ('y', 'n'), 'y')
        else:
            answered_questions['security_hardening'] = 'n' 
    assert answered_questions['security_hardening'] in QUESTION_FLAGS['security_hardening']
    
    if 'autostart_services' not in answered_questions and noninteractive:
        answered_questions['autostart_services'] = 'n' 
    elif 'autostart_services' not in answered_questions:
        if not docker:
            answered_questions['autostart_services'] = ask_question("Autostart services (including on boot)? (y/N)", ('y', 'n'), 'n')
        else:
            answered_questions['autostart_services'] = 'n' 
    assert answered_questions['autostart_services'] in QUESTION_FLAGS['autostart_services']

    logging.debug("answered_questions: %s" % answered_questions)
    return answered_questions

def usage():
    print("SYNTAX: %s [-h] [--docker] [--noninteractive] %s" % (
        sys.argv[0], ' '.join([('[--%s=%s]' % (q, '|'.join(v) if v else '')) for q, v in QUESTION_FLAGS.items()])))

def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s|%(levelname)s: %(message)s')
    do_federated_node_prerun_checks()
    run_as_user = os.environ["SUDO_USER"]
    assert run_as_user
    answered_questions = {}

    #parse any command line objects
    docker = False
    noninteractive = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "docker", "noninteractive"] + ['%s=' % q for q in QUESTION_FLAGS.keys()])
    except getopt.GetoptError as err:
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o == "--docker":
            docker = True
        elif o == "--noninteractive":
            noninteractive = True
        elif o in ['--%s' % q for q in QUESTION_FLAGS.keys()]: #process flags for non-interactivity
            answered_questions[o.lstrip('-')] = a
        else:
            assert False, "Unhandled or unimplemented switch or option"

    base_path = os.path.join(USER_HOMEDIR, "csfrd_build")
    dist_path = os.path.join(base_path, "dist")

    #Detect if we should ask the user if they just want to update the source and not do a rebuild
    do_rebuild = 'r'
    try:
        pwd.getpwnam(USERNAME) #hacky check ...as this user is created by the script
    except:
        answered_questions['op'] = 'r' #do a build
    else: #setup has already been run at least once
        if not (answered_questions.get('op', None) in QUESTION_FLAGS['op']):
            answered_questions['op'] = ask_question(
                "It appears this setup has been run already. (r)ebuild node, or just (U)pdate from git? (r/U)",
                ('r', 'u'), 'u')
            assert answered_questions['op'] in QUESTION_FLAGS['op']

    if answered_questions['op'] == 'u': #just refresh csfrd, csfrblockd, and csfrwallet, etc. from github
        if os.path.exists("/etc/init.d/iwatch"):
            runcmd("service iwatch stop", abort_on_failure=False)
        
        #refresh csfrd_build, csfrd and csfrblockd (if available)
        runcmd("sudo python3 %s/setup.py --noninteractive --branch=AUTO --for-user=csfr %s update" % (base_path,
            '--with-csfrblockd' if os.path.exists(os.path.join(dist_path, "csfrblockd")) else ''))
        
        #refresh csfrwallet (if available)
        if os.path.exists(os.path.exists(os.path.expanduser("~%s/csfrwallet" % USERNAME))):
            do_csfrwallet_setup(run_as_user, "AUTO", updateOnly=True)

        #offer to restart services
        restarted = command_services("restart", prompt=not noninteractive)
        if not restarted and os.path.exists("/etc/init.d/iwatch"):
            runcmd("service iwatch start", abort_on_failure=False)
        sys.exit(0) #all done

    #If here, a) federated node has not been set up yet or b) the user wants a rebuild
    answered_questions = gather_build_questions(answered_questions, noninteractive, docker)
    
    command_services("stop")

    do_base_setup(run_as_user, answered_questions['branch'], base_path, dist_path)
    
    backend_rpc_password, backend_rpc_password_testnet \
        = do_backend_rpc_setup(run_as_user, answered_questions['branch'], base_path, dist_path,
            answered_questions['run_mode'], answered_questions['backend_rpc_mode'])
    
    do_csfr_setup(answered_questions['role'], run_as_user, docker, answered_questions['branch'],
        base_path, dist_path, answered_questions['run_mode'],
        backend_rpc_password, backend_rpc_password_testnet,
        answered_questions['csfrd_public'], answered_questions['csfrwallet_support_email'])
    
    do_blockchain_service_setup(run_as_user, base_path, dist_path,
        answered_questions['run_mode'], answered_questions['blockchain_service'])
    
    do_nginx_setup(run_as_user, base_path, dist_path, enable=answered_questions['role'] != "csfrd_only")
    
    do_armory_utxsvr_setup(run_as_user, base_path, dist_path,
        answered_questions['run_mode'], enable=answered_questions['role'] == 'csfrwallet')
    if answered_questions['role'] == 'csfrwallet':
        do_csfrwallet_setup(run_as_user, answered_questions['branch'])

    if not docker:
        do_newrelic_setup(run_as_user, base_path, dist_path, answered_questions['run_mode']) #optional
    
    assert not (docker and answered_questions['security_hardening']) 
    do_security_setup(run_as_user, answered_questions['branch'], base_path, dist_path,
        enable=answered_questions['security_hardening'] == 'y')
    
    logging.info("cSFRblock Federated Node Build Complete (whew).")
    
    if answered_questions['autostart_services'] == 'y':
        configured_services = find_configured_services()
        for s in configured_services:
            config_runit_disable_manual_control(s)

if __name__ == "__main__":
    main()
