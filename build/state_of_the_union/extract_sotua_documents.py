import re
import os

chron_entry_regex = r"\[\[(?P<title>(?P<president_name>.+)'s? .*State of the Union Address)\|(?P<address_number>\w+) State of the Union Address\]\] - \[\[author:(?P<author_name>.+)\|.+\]\], \((?P<day>\d+) (?P<month>\w+) \[\[w:(?P<year>\d+)\|(?P=year)\]\]\)"

def metadata(chron_list_wiki_file):
    
    text = open(chron_list_wiki_file).read()
#    print text
    return re.findall(chron_entry_regex, text, re.IGNORECASE)

def extract_state_of_the_union(data_dir, dest_dir):
    titles = [m[0] for m in metadata(data_dir+'/chronological_list.wiki')]
#    print titles
    if not os.path.exists(dest_dir): os.mkdir(dest_dir)
    
    current_speech_title = None
    lines = []
    for line in open(data_dir+'/state_of_the_union_addresses.txt'):
        line = line.strip()
        if line in titles:
            if current_speech_title is not None:
                w = open(dest_dir+'/'+current_speech_title.replace(' ','_')+'.txt','w')
                w.write(u' '.join(lines))
                lines = []
                print 'Extracted "{0}"'.format(current_speech_title)
            current_speech_title = line
        else:
            lines += [line]
    
    w = open(dest_dir+'/'+current_speech_title.replace(' ','_')+'.txt','w')
    w.write(u' '.join(lines))
    print 'Extracted "{0}"'.format(current_speech_title)
    
if __name__=='__main__':
#    print len(metadata('../../datasets/state_of_the_union/chronological_list.wiki'))
    extract_state_of_the_union('../../datasets/state_of_the_union', '../../datasets/state_of_the_union/raw_files')