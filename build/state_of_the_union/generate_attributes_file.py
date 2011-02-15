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

from extract_sotua_documents import metadata,filename

def generate_attributes_file(chron_list_file, output_file):
    print "Building attributes file {0} using {1}".format(output_file, chron_list_file)
    
    meta = metadata(chron_list_file)
    w = open(output_file, 'w')
    
    w.write('[\n')
    for i,m in enumerate(meta):
        #[(?P<title>(?P<president_name>.+)'s? .*State of the Union Address)\|(?P<address_number>\w+) State of the Union Address\]\] - \[\[author:(?P<author_name>.+)\|.+\]\], \((?P<day>\d+) (?P<month>\w+) \[\[w:(?P<year>\d+)\|(?P=year)\]\]\)"
        w.write('\t{\n')
        w.write('\t\t"attributes": {\n')
        
        attr_entries = []
        for attr,val in m.groupdict().items():
            attr_entries += ['\t\t\t"{0}": "{1}"'.format(attr,val)]
        w.write(',\n'.join(attr_entries))
        w.write('\n\t\t},\n')
        w.write('\t\t"path": "{0}"\n'.format(filename(m)))
        
        w.write('\t}')
        
        if i < len(meta)-1: w.write(',')
        
        w.write('\n')
    w.write(']')