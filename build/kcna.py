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

#wget --mirror http://kcna.co.jp/item/2011/calendar-2011e.html

import codecs
import os
import re
import sys
import subprocess as sub

import topic_modeling.anyjson as anyjson

def update_config(c):
    c['dataset_name'] = "kcna"
    c['dataset_description'] = "News releases/propaganda from North Korea's Korean Central News Agency (KCNA)"
    c['url'] = "http://kcna.co.jp/"
    c['data_dir'] = os.environ['HOME'] + "/Data"
    c['kcna_dir'] = c['data_dir'] + "/kcna.co.jp"
    c['suppress_default_attributes_task'] = True

def create_tasks(c):

    def task_download_kcna():
        task = dict()
        task['actions'] = ["mkdir -p {kcna_dir} && cd {kcna_dir}  && wget --mirror -nH {url}".format(kcna_dir=c['kcna_dir'],url=c['url'])]
        task['clean'] = ["rm -rf " + c['kcna_dir']]
        task['uptodate'] = [os.path.exists(c['kcna_dir'])]
        return task

    def task_extract_data():
        task = dict()
        task['targets'] = [c['files_dir'], c['metadata_filenames']['documents']]
        task['actions'] = ["mkdir -p "+c['files_dir'],
                (extract, [c['kcna_dir'], c['files_dir'], c['metadata_filenames']['documents']])]
        task['clean'] = ['rm -rf '+c['files_dir'], 'rm -f '+c['metadata_filenames']['documents']]
        task['task_dep'] = ['download_kcna']
        task['uptodate'] = [os.path.exists(c['files_dir']) and os.path.exists(c['metadata_filenames']['documents'])]
        return task
    
    return [task_download_kcna, task_extract_data]

old_date_regex = r'.+item/(?P<year>\d\d(?P<year_short>\d\d))/(?:(?P=year)|(?P=year_short))(?P<month>\d(?P<month_digit_two>\d))/news(?:(?P=month)|(?P=month_digit_two))/(?P<day>\d\d)\.htm'
new_date_regex_strict = r'.+item/(?P<year>\d\d\d\d)/(?P=year)(?P<month>\d\d)/news(?P<day>\d\d)/(?P=year)(?P=month)(?P=day)-(?P<item>\d\d)ee?\.html'
new_date_regex_lax    = r'.+item/(?P<year>\d\d\d\d)/(?P=year)(?P<month>\d\d)/news(?P<day>\d\d)/\d\d\d\d\d\d\d\d-(?P<item>\d+)ee?\.html'

def parse_date(path):
    if path.endswith('e.html'):
        #/home/jjfresh/Data/kcna.co.jp/kcna.co.jp/item/2010/201008/news01/20100708-04ee.html
        #/home/jjfresh/Data/kcna.co.jp/kcna.co.jp/item/2010/201002/news06/20100206-13ee.html
        date = re.match(new_date_regex_strict, path)
        if date is not None:
            return date.groupdict()
        else:
            print 'Falling back to lax parsing on ' + path
            return re.match(new_date_regex_lax, path).groupdict()
            
    else:
        #/home/jjfresh/Data/kcna.co.jp/kcna.co.jp/item/2004/200410/news10/27.htm
        regex = old_date_regex
        d = re.match(regex, path).groupdict()
        d['item'] = '01'
        return d

def extract(src_dir, dest_dir, attributes_file):
    attributes = []
    for dirpath, _dirnames, filenames in [x for x in os.walk(src_dir) if 'news' in x[0]]:
        for filename in filenames:
            full_path = dirpath + '/' + filename
            date = parse_date(full_path)
            sys.stdout.write('.')
            sys.stdout.flush()
#            print '----------------------------------------------------------------------------'
#            print 'Filename: ' + full_path
#            print 'Date: ' + str(date)
    #        print full_path, str(parse_date(full_path))
            args = ['html2text', full_path]
            p = sub.Popen(args,stdout=sub.PIPE,stderr=sub.PIPE)
            output, _errors = p.communicate()
            sections = output.split('===============================================================================')
            # could use: output.split('=' * 79)
            if len(sections) > 1:
                sections = sections[1:len(sections)-1]
            for num,section in enumerate(sections):
                cleaned_text = section.replace('calendar>>','').replace('Copyright (C) KOREA NEWS SERVICE(KNS) All Rights Reserved.','').replace('&quot;','"').strip()
                output_filename = '{year}-{month}-{day}-{item}-{number}.txt'.format(year=date['year'],month=date['month'],day=date['day'],item=date['item'],number=num)
                output_path = dest_dir + '/' + output_filename
#                codecs.open(output_path,mode='w',encoding='utf-8').write(cleaned_text)
                open(output_path, 'w').write(cleaned_text)
                
                attrs = {}
                attrs['year'] = date['year']
                attrs['month'] = date['month']
                attrs['day'] = date['day']
                attrs['item'] = date['item']
                attrs['entry'] = str(num)
                attrs['original_filename'] = filename
                doc = {'attributes':attrs, 'path':output_filename}
                attributes += [doc]
        
    f = codecs.open(attributes_file, mode='w', encoding='utf-8')
    f.write(anyjson.dumps(attributes))
    f.close()

