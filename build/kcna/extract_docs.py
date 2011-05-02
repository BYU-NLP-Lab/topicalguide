#wget --mirror http://kcna.co.jp/item/2011/calendar-2011e.html
import os
import subprocess as sub
import re
import codecs
import common.anyjson as anyjson
import sys

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
        dict = re.match(regex, path).groupdict()
        dict['item'] = '01'
        return dict

def extract(src_dir, dest_dir, attributes_file):
    attributes = []
    for dirpath, dirnames, filenames in [x for x in os.walk(src_dir) if 'news' in x[0]]:
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



if __name__ == '__main__':
    extract('/home/jjfresh/Data/kcna.co.jp/kcna.co.jp/item', '/home/jjfresh/Projects/topicbrowser/datasets/kcna/files', '/home/jjfresh/Projects/topicbrowser/datasets/kcna/attributes.json')
