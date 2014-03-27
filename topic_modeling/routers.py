# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
from __future__ import print_function
import threading

import settings

request_cfg = threading.local()

class DatabaseRouterMiddleware(object):
    """
    A router to make sure that the database has the necessary url information
    to route queries correctly.
    """
    def process_view(self, request, view_func, args, kwargs):
        """
        Set which database to use.
        """
        if 'dataset' in kwargs:
            request_cfg.dataset = kwargs['dataset']
        return None
    
    def process_response(self, request, response):
        """
        Delete the variable previously created to prevent problems occuring.
        """
        if hasattr(request_cfg, 'dataset'):
            del request_cfg.dataset
        return response

class DatabaseRouter(object):
    """
    A router to make sure that database information is only stored in the 
    default database, and that url requests hit the correct database.
    This class relies on the RouterMiddleware class to route requests correctly.
    """
    def db_for_read(self, model, **hints):
        """
        Route reads for external database information to 'default' database.
        Route dataset requests to the correct database.
        """
        if hasattr(model, '_MODEL_NAME') and model._MODEL_NAME == 'ExternalDataset':
            return 'default'
        elif hasattr(request_cfg, 'dataset') and request_cfg.dataset in settings.DATASET_TO_DATABASE_MAPPING:
            return settings.DATASET_TO_DATABASE_MAPPING[request_cfg.dataset]
        return None
    
    def db_for_write(self, model, **hints):
        """
        Route writes for external database information to 'default' database.
        """
        if hasattr(model, '_MODEL_NAME') and model._MODEL_NAME == 'ExternalDataset':
            return 'default'
        elif hasattr(request_cfg, 'dataset') and request_cfg.dataset in settings.DATASET_TO_DATABASE_MAPPING:
            return settings.DATASET_TO_DATABASE_MAPPING[request_cfg.dataset]
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Forward request to default router.
        """
        return None
    
    def allow_migrate(self, db, model):
        """
        Ensure that external database tables are only in the default database.
        """
        return self.allow_syncdb(db, model)
    
    def allow_syncdb(self, db, model):
        """
        Ensure that external database tables are only in the default database.
        """
        if db == 'default':
            return True
        elif hasattr(model, '_MODEL_NAME') and model._MODEL_NAME == 'ExternalDataset':
            return False
        else:
            return None

