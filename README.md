# The Topical Guide

Copyright 2010-2015 Brigham Young University

## About

The Topical Guide is a tool aimed at helping laymen and experts intuitively
navigate the topic distribution produced by a topic model, such as LDA, over a
given dataset.

Learn more by visiting [the wiki](https://github.com/BYU-NLP-Lab/topicalguide/wiki).

## Requirements

- Python 3.10 or higher
- Django 4.2 (LTS)
- MALLET (for topic modeling)
- See `requirements.txt` for complete list of dependencies

## Installation

### 1. Clone the Source

Clone the source with the following:
    
    git clone https://github.com/BYU-NLP-Lab/topicalguide.git

Then navigate to the `topicalguide` directory.

### 2. Install Dependencies

**It is strongly recommended to use a virtual environment.** You can create one using Python's built-in `venv` module:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

You must activate your virtual environment any time that `(venv)` does not appear in front of your command line.

Once activated, install all dependencies:

```bash
pip install -r requirements.txt
```

Note: If you encounter issues, ensure you're using Python 3.10 or higher:

```bash
python --version
```

If you want to use the word stemmer then run the following:
    
    cd tools/stemmer/
    ./make_english_stemmer.sh

### 3. Configure Django Settings

The project uses Django 4.2. If you need to customize settings, copy the template:

```bash
cp topicalguide/settings.py.template topicalguide/settings.py
```

Then edit `topicalguide/settings.py`:

1. Generate a `SECRET_KEY` at [django-secret-key-generator](http://www.miniwebtool.com/django-secret-key-generator/) and insert it
2. The default SQLite database configuration should work out of the box
3. For development, keep `DEBUG = True` (already set)
4. For production, set `DEBUG = False` and configure `ALLOWED_HOSTS`

**For most users, the existing `settings.py` file should work without modification.**

### 3a. Initialize the Database

Run Django migrations to set up the database:

```bash
python manage.py migrate
```

### 4. Import a Dataset

#### State of the Union Dataset (1790-2025)

The project includes a State of the Union addresses dataset spanning from 1790 to 2025.

**Option 1: Quick Import (recommended)**

```bash
python tg.py import default_datasets/state_of_the_union/ --identifier state_of_the_union --public --verbose
python tg.py analyze state_of_the_union --number-of-topics 20 --stopwords stopwords/english_all.txt --verbose
```

**Option 2: Using the provided script**

```bash
./default_datasets/import_state_of_the_union.sh
```

The project includes several stopword files in the `stopwords/` directory (`english_all.txt`, `english_mallet.txt`, `en.txt`) for filtering common words during topic modeling.

#### Updating the State of the Union Dataset

To download the most recent State of the Union addresses (2011-2025):

```bash
python download_sotu.py
```

This will fetch recent speeches from the American Presidency Project and save them in the proper format.

#### Custom Datasets

For more options on importing custom datasets:

```bash
python tg.py -h
```

### 5. Start the Web Server

Make sure your virtual environment is activated, then start the Django development server:

```bash
python manage.py runserver
```

Open a web browser and navigate to:

**http://localhost:8000/**

You should see the Topical Guide interface with your imported dataset(s).

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
