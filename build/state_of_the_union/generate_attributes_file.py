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

from extract_sotua_documents import metadata,filename

head = '''{
    "types": {
        "address_number": "int",
        "title": "text",
        "author_name": "text",
        "month": "text",
        "president_name": "text",
        "year": "int",
        "day": "int"
    },
    "data": {'''

tail = '''\t}
}'''

address_nums = {'First':1, 'Second':2, 'Third':3, 'Fourth':4, 'Fifth':5,
    'Sixth':6, 'Seventh':7, 'Eighth':8, 'Ninth':9, 'Tenth':10, 'Eleventh':11,
    'Twelfth':12}

def generate_attributes_file(chron_list_file, output_file):
    print "Building attributes file {0} using {1}".format(output_file, chron_list_file)
    
    meta = metadata(chron_list_file)
    w = open(output_file, 'w')
    
    w.write(head)
    w.write('\n')
    for i,m in enumerate(meta):
        w.write('\t\t"%s": {\n' % filename(m))
        
        attr_entries = []
        for attr,val in m.groupdict().items():
            if attr=="address_number": val=address_nums[val]
            attr_entries += ['\t\t\t"{0}": "{1}"'.format(attr,val)]
        w.write(',\n'.join(attr_entries))
        w.write('\n\t\t}')
        
        if i < len(meta)-1: w.write(',')
        
        w.write('\n')
    w.write(tail)