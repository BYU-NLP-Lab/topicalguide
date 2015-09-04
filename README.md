# The Topical Guide

Copyright 2010-2015 Brigham Young University

## About

The topical guide is a tool aimed at helping laymen and experts intuitively
navigate the topic distribution produced by a topic model, such as LDA, over a
given dataset.

Learn more by visiting [the wiki](https://github.com/BYU-NLP-Lab/topicalguide/wiki).

## Installation

### 1. Clone the Source

Clone the source with the following:
    
    git clone https://github.com/BYU-NLP-Lab/topicalguide.git

Then navigate to the `topicalguide` directory.

### 2. Install Dependencies

Superuser permissions are necessary to install the Topical Guide as shown in the 
current instructions.

In order to circumvent the need for superuser permissions, you can create a virtual
environment using `virtualenv`, `virtualenvwrapper`, `pyenv`, or another tool.

To use `virtualenv`, type the following inside the project's root directory:

    virtualenv ENV
    source ENV/bin/activate

You must activate your virtual environment by typing the second line above any time
that `(ENV)` does not appear in front of your command line.

Documentation for all of the above mentioned tools can be found here:
[virtualenv](https://virtualenv.pypa.io/en/latest/)
[virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/)
[pyenv](https://github.com/yyuu/pyenv#installation)


Dependencies are listed in the `requirements.txt` file and can be easily installed with:

    pip install -r requirements.txt

If you want to use the word stemmer then run the following:
    
    cd tools/stemmer/
    ./make_english_stemmer.sh

### 3. Create Settings

In order for django to run it needs `settings.py` to be created.
First, copy the template:

    cp topicalguide/settings.py.template topicalguide/settings.py

Second, go to [this website](http://www.miniwebtool.com/django-secret-key-generator/) to generate your `SECRET_KEY`.

Third, open `topicalguide/settings.py` in your favorite text editor.  
Within this file:

(1) Insert your generated `SECRET_KEY` where it says

	SECRET_KEY=''

(2) Set your database settings. You could use sqlite, which is configured for you. 
If you want to use Postgres there are instructions below for setting it up on Fedora.

(3) Set `DEBUG = True` to use the developement server.
If DEBUG is set to False then ALLOWED_HOSTS must be set. See Django's documentation for further details.

(4) Optionally, configure other various django options.

### 4. Import a Dataset

You can run (from the project's root directory):
    
    ./default_datasets/import_state_of_the_union.sh
    
or

    python tg.py import default_datasets/state_of_the_union/ --identifier state_of_the_union --public --public-documents
    python tg.py analyze state_of_the_union --number-of-topics 100

For more options on importing see the documentation by running:

    python tg.py -h

### 5. Done!

Start up the development web server with the following command:

    python manage.py runserver

and then open a web browser and navigate to http://localhost:8000/.

## POSTGRESQL

It can be tons faster to use postgres. Because it took me a bit of hunting to
get it to behave, here's how to do it on Fedora::

    sudo yum install postgres*
    sudo yum install python-psycopg2

    sudo systemctl enable postgresql.service
    sudo postgresql-setup initdb
    sudo -u postgres createdb topicalguide

In your settings.py you'll then need to switch DBTYPE to 'postgres' and
update the settings for the postgres database. For a local connection, we
prefer to use peer authentication, so we leave the user and password blank.
If you prefer to use md5 authentication, set the user and password
appropriately. Update the name field to 'topicalguide', or whatever you named
the database created for the topical guide.

Once the database is setup run the commands starting at step 4 with the prefix
`sudo -u postgres`.

## Apache

As an example, the following template apache configuration file could be 
filled in and placed in /etc/httpd/conf.d to run your server assuming your 
project is located at /srv/topicalguide::

    ServerAdmin your_admin_email@somewhere.com
    ServerName your.server.com
    ErrorLog /var/log/httpd/your-error_log
    CustomLog /var/log/httpd/your-access_log common
    LogLevel warn

    Alias /scripts /srv/topicalguide/topic_modeling/media/scripts/
    Alias /styles /srv/topicalguide/topic_modeling/media/styles/
    Alias /site-media /srv/topicalguide/topic_modeling/media
    <Directory "/srv/topicalguide/topic_modeling/media">
       Require all granted
    </Directory>

    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptAlias / /srv/topicalguide/topic_modeling/apache/django.wsgi
    <Directory "/srv/topicalguide/topic_modeling/apache">
       Require all granted
    </Directory>

Note that the django.wsgi file we use is included in the repository.
Further information on setting up Django to run with Apache can be found
in the official Django documentation.

## Contributing

We welcome contributions to the code of this project. 
The best way to do so is to fork the code and then submit a [pull request](https://help.github.com/articles/using-pull-requests). 
For licensing purposes we ask that you assignthe copyright of any patch that you contribute to Brigham Young University.

## Citations

We also request that any published papers resulting from the use of this code
cite the following paper:

Matthew J. Gardner, Joshua Lutes, Jeff Lund, Josh Hansen, Dan Walker, Eric
Ringger, Kevin Seppi. "The Topic Browser: An Interactive Tool for Browsing
Topic Models".  In the Proceedings of the Workshop on Challenges of Data
Visualization, held in conjunction with the 24th Annual Conference on Neural
Information Processing Systems (NIPS 2010). December 11, 2010. Whistler, BC,
Canada.

## Licence

This file is part of the [Topical Guide](http://github.com/BYU-NLP-Lab/topicalguide/wiki).

The Topical Guide is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or any later version.

The Topical Guide is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
for more details.

You should have received a copy of the [GNU Affero General Public License](http://www.gnu.org/licenses/) along
with the Topical Guide.

If you have inquiries regarding any further use of the Topical Guide, please
contact:

    Copyright Licensing Office
    Brigham Young University
    3760 HBLL
    Provo, UT 84602
    Phone: (801) 422-9339 or (801) 422-3821
    Email: copyright@byu.edu
