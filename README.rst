Last updated: 01 Oct 2013

--------------------------------------------
The Topical Guide
--------------------------------------------

Copyright 2010-2012 Brigham Young University

About
=====

The topical guide is a tool aimed at helping laymen (and experts) intuitively
navigate the topic distribution produced by a topic model (such as LDA) for a
given dataset.

Installation
============

1. Clone the source
-------------------

::

   git clone git://github.com/BYU-NLP-Lab/topicalguide.git

2. Install dependencies
-----------------------

You can either use the pip `requirements.txt file`_::

    pip install -r requirements.txt

.. _`requirements.txt file`: http://www.pip-installer.org/en/latest/requirements.html

Or you can install the python dependencies some other way (yum, by hand,
etc.); they're listed in the `requirements.txt` file.

.. include:: requirements.txt
   :literal:

3. Generate the SECRET_KEY
--------------------------

Go to this website to generate your SECRET_KEY 
http://www.miniwebtool.com/django-secret-key-generator/

Navigate to topicalguide/topic_modeling/settings.py.  
Insert your generated SECRET_KEY where it says

	SECRET_KEY=''

Be sure not to commit/push your settings.py file with your SECRET_KEY in it.

4. Sync the database
--------------------

Run `topic_modeling/manage.py syncdb`. Note that this requires the user to select whether or not
to enter a super user password for the site. Currently it doesn't matter if you select yes or no.

5. Import a dataset
-------------------

Run `./topicalguide.py import raw_data/state_of_the_union` to run the default import.
Run `./topicalguide.py -h` for more options.
Alternatively you can create your own custom import by inheriting from the `AbstractDataset` 
class in the `import_tool/dataset_classes/abstract_dataset.py` and use the methods available in 
`import_tool/import_utilities.py` to import a dataset, run analyses, or run metrics.

6. Done!
--------

Start up the development web server with the following command::

   python topic_modeling/manage.py runserver

and then open a web browser and navigate to http://localhost:8000/.

Dependencies
-------------

See `requirements.txt`

POSTGRESQL
==========

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

Apache
======

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

Contributing
============

We welcome contributions to the code of this project. The best way to do so is
to fork the code on github (https://github.com/BYU-NLP-Lab/topicalguide) and
then submit a `pull request`_. For licensing purposes we ask that you assign
the copyright of any patch that you contribute to Brigham Young University.

.. _pull request: https://help.github.com/articles/using-pull-requests

More Information
================

Further information, documentation, and a live demo of the code can be found at
the project website: http://nlp.cs.byu.edu/topicalguide.  We choose not to
repeat most of the documentation in the code itself, though we give some simple
instructions on how to run the code below.

Citations
=========

We also request that any published papers resulting from the use of this code
cite the following paper:

Matthew J. Gardner, Joshua Lutes, Jeff Lund, Josh Hansen, Dan Walker, Eric
Ringger, Kevin Seppi. "The Topic Browser: An Interactive Tool for Browsing
Topic Models".  In the Proceedings of the Workshop on Challenges of Data
Visualization, held in conjunction with the 24th Annual Conference on Neural
Information Processing Systems (NIPS 2010). December 11, 2010. Whistler, BC,
Canada.

Licence
=======

This file is part of the Topical Guide <http://github.com/BYU-NLP-Lab/topicalguide/wiki>.

The Topical Guide is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

The Topical Guide is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
for more details.

You should have received a copy of the GNU Affero General Public License along
with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.

If you have inquiries regarding any further use of the Topical Guide, please
contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
        Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

