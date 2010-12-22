import re
import os
from nltk.tokenize import TreebankWordTokenizer
import codecs

chron_entry_regex = r"\[\[(?P<title>(?P<president_name>.+)'s? .*State of the Union Address)\|(?P<address_number>\w+) State of the Union Address\]\] - \[\[author:(?P<author_name>.+)\|.+\]\], \((?P<day>\d+) (?P<month>\w+) \[\[w:(?P<year>\d+)\|(?P=year)\]\]\)"

def metadata(chron_list_wiki_file):
    text = codecs.open(chron_list_wiki_file,'r','utf-8').read()
    return [m for m in re.finditer(chron_entry_regex, text, re.IGNORECASE)]

tokenizer = TreebankWordTokenizer()
def lines_to_string(lines):
    raw_txt = u' '.join(lines)
    tokens = tokenizer.tokenize(raw_txt)
    tokenized_txt = u' '.join(tokens)
    return tokenized_txt


def extract_state_of_the_union(chron_list_filename, addresses_filename, dest_dir):
    print "extract_state_of_the_union({0},{1},{2})".format(chron_list_filename, addresses_filename, dest_dir)
    titles = [m.group('title') for m in metadata(chron_list_filename)]#data_dir+'/chronological_list.wiki')]
    print 'Addresses in index: ' + str(len(titles))
    extracted_count = 0
    if not os.path.exists(dest_dir): os.mkdir(dest_dir)
    
    current_speech_title = None
    lines = []
    for line in codecs.open(addresses_filename,'r','utf-8'):#data_dir+'/state_of_the_union_addresses.txt'):
        line = line.strip()
        if line in titles:
            if current_speech_title is not None:
                w = codecs.open(dest_dir+'/'+current_speech_title.replace(' ','_')+'.txt','w','utf-8')
                w.write(lines_to_string(lines))
                lines = []
                print 'Extracted "{0}"'.format(current_speech_title)
                extracted_count += 1
            current_speech_title = line
        else:
            lines += [line]
    
    w = codecs.open(dest_dir+'/'+current_speech_title.replace(' ','_')+'.txt','w','utf-8')
    w.write(lines_to_string(lines))
    print 'Extracted "{0}"'.format(current_speech_title)
    extracted_count += 1
    print 'Addresses extracted: ' + str(extracted_count)



if __name__=='__main__':
#    print metadata('../../datasets/state_of_the_union/chronological_list.wiki')
    extract_state_of_the_union('../../datasets/state_of_the_union/chronological_list.wiki','../../datasets/state_of_the_union/state_of_the_union_addresses.txt','../../datasets/state_of_the_union/files')
