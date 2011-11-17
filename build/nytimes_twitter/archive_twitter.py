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

import os
import twitter
from time import sleep, time

class TwitterArchiver(object):
    def __init__(self, queries, output_dir):
        super(TwitterArchiver,self).__init__()
        self.queries = queries
        self.api = twitter.Api()
        self.output_dir = output_dir
        self.prev_ids = {}
        for query in queries:
            self.prev_ids[query] = -1
    
    def run(self, duration_in_seconds):
        start_time = time()
        while time() - start_time < duration_in_seconds:
            for query in self.queries:
                self.archive_available_statuses_for_query(query)
            sleep(10)
    
    def archive_available_statuses_for_query(self, query):
        last_size = 1000
        while last_size > 5:
            try:
                statuses = self.get_statuses(query)
            except ValueError as e:
                print "*** ValueError occurred. Resting for 60 seconds... ({0}) ***".format(e)
                sleep(60)
            except twitter.TwitterError as e:
                print "*** Probably polled too frequently. Resting for 60 seconds... ({0}) ***".format(e)
                sleep(60)
            except:
                print "*** Unexpected error. Resting for 60 seconds... ***"
            else:
                self.save_statuses_to_file(statuses)
                last_size = len(statuses)
                sleep(5)
    
    def save_statuses_to_file(self, statuses):
        for s in statuses:
            path = '{0}/twitter_{1}.txt'.format(self.output_dir, s.id)
            print "twitter/" + str(s.id) + " all " + s.text + "\n"
            
            f = open(path, 'w')
            f.write(s.text)

    def get_statuses(self, query):
        most_recent_id = self.prev_ids[query]
        if query == '':
            if most_recent_id == -1:
                statuses = self.api.GetSearch(query)
            else:
                statuses = self.api.GetSearch(query, since_id=most_recent_id)
        else:
            if most_recent_id == -1:
                statuses = self.api.GetPublicTimeline()
            else:
                statuses = self.api.GetPublicTimeline(since_id=most_recent_id)
        
        if len(statuses) > 0:
            self.prev_ids[query] = statuses[0].id
        
        return statuses

if __name__ == '__main__':
    duration = 7*24*60*60
    name = 'all'
    queries = ['politics','#politics', 'congress', '#congress', 'obama', 'republican', 'democrat', 'legislation']
    output_dir = '{0}/Data/twitter.com/{1}'.format(os.environ['HOME'], name)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    ta = TwitterArchiver(queries, output_dir)
    ta.run(duration)