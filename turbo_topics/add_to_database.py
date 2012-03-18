#!/usr/bin/env python

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

import os, sys

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from django.db import transaction
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, TopicMetaInfo
from topic_modeling.visualize.models import TopicMetaInfoValue

@transaction.commit_manually
def add_information(dataset, analysis, force_import=False, *args, **kwargs):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    if 'ngrams' in kwargs and kwargs['ngrams']:
        ngrams = True
    else:
        ngrams = False
    if ngrams:
        info_name = "Turbo Topics N-Grams"
    else:
        info_name = "Turbo Topics Cloud"
    try:
        info = TopicMetaInfo.objects.get(name=info_name)
        if not force_import:
            raise RuntimeError('%s is already in the database '
                    'for this analysis!' % info_name)
    except TopicMetaInfo.DoesNotExist:
        info = TopicMetaInfo(name=info_name)
        info.save()

    for root, _dirs, files in os.walk(kwargs['output_dir']):
        for file in files:
            f = open(root+'/'+file)
            output = ''
            for line in f:
                if ngrams:
                    fields = line.split()
                    words = ' '.join(fields[:-1])
                    if ' ' in words:
                        output += words + '\n'
                else:
                    output += line
            topic_num = int(file.split('.')[0][5:])
            topic = analysis.topics.get(number=topic_num)
            eti_value = TopicMetaInfoValue(topic=topic, info_type=info,
                    text_value=output)
            eti_value.save()
    transaction.commit()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-d', '--dataset-name',
            dest='dataset_name',
            help='The name of the dataset for which to add this topic metric',
            )
    parser.add_option('-a', '--analysis-name',
            dest='analysis_name',
            help='The name of the analysis for which to add this topic metric',
            )
    parser.add_option('-f', '--force-import',
            dest='force_import',
            action='store_true',
            help='Force the import of this metric even if the script thinks the'
            ' metric is already in the database',
            )
    parser.add_option('', '--n-grams',
            dest='ngrams',
            action='store_true',
            help='Add only n-grams to the database instead of a word cloud',
            )
    parser.add_option('-o', '--output-dir',
            dest='output_dir',
            help='The directory to find the output from the turbo-topics code',
            )
    options, args = parser.parse_args()
    dataset = options.dataset_name
    analysis = options.analysis_name
    force_import = options.force_import
    output_dir = options.output_dir
    ngrams = options.ngrams
    add_information(dataset, analysis, force_import, output_dir=output_dir,
            ngrams=ngrams)

# vim: et sw=4 sts=4
