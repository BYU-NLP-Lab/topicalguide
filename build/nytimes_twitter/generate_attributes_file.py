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

from sys import argv

def generate_attributes_file(mallet_input_file, output_file):
    print "Building attributes file {0} using {1}".format(output_file, mallet_input_file)
    
    f = open(mallet_input_file)
    w = open(output_file, 'w')
    
    w.write('[\n')
    lines = f.readlines()
    for i in range(0,len(lines)):
        arr = lines[i].split(None)
        source = arr[0].split('_')[0]
        
        w.write('\t{\n')
        w.write('\t\t"attributes": {\n')
        w.write('\t\t\t"source": "' + source + '"\n')
        w.write('\t\t},\n')
        w.write('\t\t"path": "' + arr[0] + '"\n')
        
        w.write('\t}')
        
        if i < len(lines)-1: w.write(',')
        
        w.write('\n')
    w.write(']')

if __name__ == "__main__":
    mallet_input_file = argv[1]
    output_file = argv[2]
    generate_attributes_file(mallet_input_file, output_file)

