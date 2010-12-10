# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

from topic_modeling.visualize.models import Analysis, Dataset, Document, Topic

def remove_dataset(dataset_name):
    print "remove_dataset({0})".format(dataset_name)
    dataset = Dataset.objects.get(name=dataset_name)
    for doc in Document.objects.filter(dataset=dataset):
        print "\tremove doc " + str(doc)
        doc.delete()
    
    for analysis in Analysis.objects.filter(dataset=dataset):
        print "\tremove analysis " + str(analysis)
        remove_analysis_obj(analysis)
    
    dataset.delete()

def remove_analysis(dataset_name, analysis_name):
    dataset = Dataset.objects.get(name=dataset_name)
    analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
    remove_analysis_obj(analysis)

def remove_analysis_obj(analysis):
    for topic in Topic.objects.filter(analysis=analysis):
        print "\t\tremove topic " + str(topic)
        topic.delete()
    analysis.delete()