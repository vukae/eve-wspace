Install: Ubuntu 12.04 LTS with MySQL and Nginx
==============================================

This guide will walk you through installing Eve W-Space on Ubuntu 12.04 LTS using a local MySQL server and serving requests with Nginx and Gunicorn. It assumes a clean install and root shell access.

Requirements
------------
* 764MB RAM with 1GB preferred for high-traffic instances. This may be flexible depending on your specific load.
* The following packages in addition to the normal core install:
  
    * git-core 
    * build-essential
    * python-dev
    * python-pip
    * nginx
    * bzip2
    * memcached
    * libmysqlclient-dev
    * mysql-server
    * libxml2-dev
    * libxslt-dev
    * rabbitmq-server
    * supervisor

You can install all required packages with the following. You will be prompted for a mysql root password. You may leave this blank if you wish, but it is recommended that you set a secure password and remember it for later.

:command:`$ sudo apt-get install git-core build-essential python-dev python-pip nginx bzip2 memcached libmysqlclient-dev mysql-server libxml2-dev libxslt-dev rabbitmq-server supervisor`

You will also be needing to edit text, so make sure to install your favorite text editor if *nano* or *vi* (not *vim*) aren't your cup of tea:

:command:`$ sudo apt-get install vim` 

Next, you will need to upgrade *distribute* and install *virtualenv*:
:command:`$ sudo easy_install -U distribute`

:command:`$ sudo pip install virtualenv`

Finally, you must create the MySQL database for Eve-Wspace to use:

:command:`$ mysql -u root -p`

Enter the root password you set when installing MySQL before:

:command:`Password:`

Then, create the database and grant access to it to a new mysql user called *maptool* with a password you should remember for later. If you want to simply use the root MySQL user, simply ignore the *GRANT PRIVILEGES* command.::

    mysql> CREATE DATABASE evewspace CHARACTER SET utf8;

    mysql> GRANT ALL PRIVILEGES ON evewspace.* TO 'maptool'@'localhost' IDENTIFIED BY '<insert a password>;

    mysql> quit

Create a User
-------------

You should not run Eve W-Space as root for security. We will create a dedicated account called *maptool* with a home directory of */home/maptool*. You can name this user whatever you want, just replace all instances of */home/maptool* with your user's home directory.

:command:`$ sudo useradd -m -s /bin/bash maptool`

:command:`$ sudo passwd maptool`

Set Up the Home Directory
-------------------------

Let's become our user for this part to ensure permissions are proper and switch to the install location:

:command:`$ sudo su maptool`

:command:`$ cd /home/maptool`

Now, let's create a directory to be used for serving static files later:

:command:`$ mkdir /home/maptool/static`

Next, you need to get the Eve W-Space files. We can either clone the latest revision from *git* or you can download a packaged release and unpack it.

To clone from Github:

:command:`$ git clone https://github.com/marbindrakon/eve-wspace.git`

To use a packaged release:

We need to download eve-wspace from http://marbindrakon.github.com/eve-wspace/ to get latest zip or tarball package (0.1.1 at time of writing):
	
:command:`$ wget https://github.com/marbindrakon/eve-wspace/archive/v0.1.1.tar.gz`

Then you can unpack the file and rename the directory to *eve-wspace* to match the clone method:

:command:`$ tar xvzf v0.1.1.tar.gz && mv eve-wspace-0.1.1 eve-wspace`

Install Eve-Wspace Environment
------------------------------

Next, you should create and activate a virtual Python environment for Eve W-Space so that it cannot conflict with any system Python packages: 

:command:`$ virtualenv --no-site-packages /home/maptool/eve-wspace`

:command:`$ source /home/maptool/eve-wspace/bin/activate`

You will notice that your shell changes to include *(eve-wspace)* when the virtual environment is active.

Now you can install the required Python packages:

:command:`(eve-wspace)$ pip install -r /home/maptool/eve-wspace/requirements.txt`

Configuring local_settings.py
-----------------------------

Now for the fun part, copy the local_settings.py.example file to local_settings.py in the same directory, open it up, and edit it to suit your enviornment:

:command:`(eve-wspace)$ cd /home/maptool/eve-wspace/evewspace/evewspace`

:command:`(eve-wspace)$ cp local_settings.py.example local_settings.py`

:command:`(eve-wspace)$ nano local_settings.py`

While editing, you should pay particular attention to the top part of th efile, ensuring that the database statement matches the database, user, and password you created in MySQL earlier and that you add a SECRET_KEY and set the STATIC_ROOT value:::

    #Example:

    # Set this to False for production or you'll leak memory
    DEBUG = False
    #DEBUG = True

    # Set this to a secret value, google "django secret key" will give you
    # plenty of generators to choose from

    SECRET_KEY = 'sadf98709283j7r098j09a8fd7sdfj89j7f9a8sdf09a8fd'

    # Set this to the directory you are service static files out of so that
    # manage.py collectstatic can put them in the right place

    STATIC_ROOT = "/home/maptool/static/"

    DATABASES = {
            'default': {
                    'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
                    'NAME': 'evewspace',                      # Or path to database file if using sqlite3.
                    'USER': 'maptool',                      # Not used with sqlite3.
                    'PASSWORD': 'really_secure_password',                  # Not used with sqlite3.
                    'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
                    'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
            }
    }

Look at the rest of the *local_settings.py* file and see if there is anything you want to change. The default values for memcached and amqp work for the Ubuntu memcached and rabbitmq defaults.

Initializing the Database
-------------------------

Initializing the database falls into two parts: Loading the Eve static data and initializing the Eve W-Space instance.

Static Data
^^^^^^^^^^^

CCP releases a Static Data Export for each major patch in MS SQL format. Steve Ronuken makes MySQL conversions available shortly thereafter. These conversions can be downloaded from http://www.fuzzwork.co.uk/dump/ if you are going to be installing multiple instances, you should download the dump once and re-use it if at all possible.::

    (eve-wspace)$ cd /home/maptool
    (eve-wspace)$ curl -O http://www.fuzzwork.co.uk/dump/mysql55-retribution-1.1-84566.tbz2
    (eve-wspace)$ bunzip2 mysql55-retribution-1.1-84566.tbz2
    (eve-wspace)$ tar xvf mysql55-retribution-1.1-84566.tar
    (eve-wspace)$ mysql -u evewspace -p<password> < retribution-1.1-84566/mysql55-retribution-1.1-84566.sql

The sql import will take a few minutes to run. When it completes, your MySQL database will have all of the Static Data Export tables available.

Initializing Eve W-Space
^^^^^^^^^^^^^^^^^^^^^^^^

Next you will need to run several commands to set up the Eve W-Space tables and preload them with data. If you encounter errors here, they are most likely caused by bad settings in *local_settings.py*, not having the virtual environment activated, or permissions.::

    (eve-wspace)$ cd /home/maptool/eve-wspace/evewspace
    (eve-wspace)$ ./manage.py syncdb --all --noinput
    (eve-wspace)$ ./manage.py migrate --fake
    (eve-wspace)$ ./manage.py buildsystemdata
    Note:This will take a while (~5-10min)
    (eve-wspace)$ ./manage.py loaddata */fixtures/*.json
    (eve-wspace)$ ./manage.py defaultsettings
    (eve-wspace)$ ./manage.py resetadmin
    (eve-wspace)$ ./manage.py syncrss
    (eve-wspace)$ ./manage.py collectstatic --noinput

Using the Development Server
----------------------------

If you've made it this far, congratulations! Eve W-Space is set up. From here, you can run the console development server directly or continue with setting up the rest of a production environment (Nginx, Gunicorn, Supervisor).

To start the development server:

:command:`(eve-wspace)$ cd /home/maptool/eve-wspace/evewspace`

:command:`(eve-wspace$ ./manage.py runserver 0.0.0.0:8000`

Now you can navigate to your server on port 8000 and see your instance. However, you need to have celery running as well for many tasks to work properly. In another shell:

:command:`(eve-wspace)$ cd /home/maptool/eve-wspace/evewspace`
:command:`(eve-wspace)$ ./manage.py celery worker -B --loglevel=info`

When both are running at the same time, you should be able to use all functions. If you want things to run a bit more permanently, continue reading.

Setting Up a Production Stack
-----------------------------

To serve Eve W-Space in production, you should use a dedicated http daemon to serve static files and either serve the Eve W-Space application itself either through the http daemon itself (as with Apache's mod_wsgi setup) or through a seperate tool which the http daemon will proxy requests to. This guide follows the latter route.

Installing Gunicorn
^^^^^^^^^^^^^^^^^^^

This guide uses Gunicorn, a lightweight wsgi server written in Python to serve the Django app itself.

To install:

:command:`(eve-wspace)$ pip install gunicorn`

Configuring Supervisor
^^^^^^^^^^^^^^^^^^^^^^

Unless you want to run celery and gunicorn through the console in *screen* or *tmux*, you will want to daemonize them in some way. This guide uses supervisor, but there are many other options available.

At this point, you can log out of the maptool user and go back to our normal account:

:command:`(eve-wspace)$ deactivate`
:command:`$ exit`

You need to tell supervisor about the tools you want it to run, to do that, you need to create a config file in */etc/supervisor/conf.d* for gunicorn and celeryd:

:command:`$ sudo nano /etc/supervisor/conf.d/celeryd.conf`::

    [program:celeryd]
    command=python manage.py celery worker -B --loglevel=info
    directory=/home/maptool/eve-wspace/evewspace
    environment=PATH=/home/maptool/eve-wspace/bin
    user=maptool
    autostart=true
    autorestart=true
    redirect_stderr=True

:command:`$ sudo nano /etc/supervisor/conf.d/gunicorn.conf`::

    [program:gunicorn]
    command=gunicorn_django --workers=4 -b 0.0.0.0:8000 settings.py
    directory=/home/maptool/eve-wspace/evewspace/evewspace
    environment=PATH=/home/maptool/eve-wspace/bin
    user=maptool
    autostart=true
    autorestart=true
    redirect_stderr=True

To finish it off, you need to stop and then start supervisor to reload the config and start the services:

:command:`$ sudo service supervisor stop`
:command:`$ sudo service supervisor start`

And confirm that both started successfully:

:command:`$ sudo supervisorctl status`::

    celeryd                          RUNNING    pid 4335, uptime 33 days, 19:16:02
    gunicorn                         RUNNING    pid 4302, uptime 33 days, 19:16:03

If either are not in the RUNNING state, either examine the log files in */var/log/supervisor/celeryd-stdout-xxxxxxxxxx.log* and */var/log/supervisor/gunicorn-stdout-xxxxxxxx.log* or try running them interactively as discussed previously.

Configuring Nginx
^^^^^^^^^^^^^^^^^

Now that Eve W-Space itself is running, you need to get people to it. That's where Nginx comes into play. Configuring Nginx is as simple as filling in one config file, creatng a symlink, and reloading the daemon.

:command:`$ sudo nano /etc/nginx/sites-available/evewspace`::

	#Example - replace x.x.x.x with your IP or host name if doing name-based vhosts
    server {
        listen 80;
        server_name x.x.x.x;
        underscores_in_headers on;

        location /static {
            alias /home/maptool/static;
        }
        location / {
            proxy_pass_header Server;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_connect_timeout 10;
            proxy_read_timeout 30;
            proxy_pass http://localhost:8000;
        }
    }


:command:`$ sudo rm /etc/nginx/sites-enabled/default`
:command:`$ sudo ln -s /etc/nginx/sites-available/evewspace /etc/nginx/sites-enabled/evewspace`
:command:`$	sudo service nginx reload`

Congratulations! Your Eve W-Space instance should now be available at whatever 
your ip or host name was from the Nginx config. Please see the :doc:`getting_started` page for your next steps. Keep in mind that your instance 
will have a default administrator registration code until you change it, so do that ASAP.
