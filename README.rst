Last updated: 13 Dec 2012

--------------------------------------------
The Topical Guide
--------------------------------------------

Copyright 2010-2012 Brigham Young University

About
=====

The topical guide is a tool aimed at helped laymen (and experts) intuitively
naviagate the topic distribution produced by a topic model (such as LDA) for a
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

3. Configure local settings
---------------------------

Copy `topic_modeling/local_settings.py.sample` to
`topic_modeling/local_settings.py` and make any changes you want. The defaults
should be reasonable::

    cp topic_modeling/local_settings.py.sample topic_modeling/local_settings.py

4. Import a dataset
-------------------

In local settings you can configure what dataset to import (default is the
'state of the union addresses'), and then run `./backend.py` to run the
import.

5. Done!
--------

Start up the web server with the following command::

   python topic_modeling/manage.py runserver

and then open a web browser and navigate to http://localhost:8000/.

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

This file is part of the Topical Guide <http://nlp.cs.byu.edu/topicalguide>.

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

