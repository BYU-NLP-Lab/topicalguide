import re
def bible_it():
    started = False
    stopped = False
    stop_count = 0
    for line in open('./raw-data/sacred_texts/pg10_bible-kjv.txt'):
        line = line.strip()
        if not started: started = line.startswith('***')
        else:
            if line =='End of the Project Gutenberg EBook of The King James Bible':
                break
            else:
                yield line
#            if stop_count < 2: yield line
#            else: break
#            stopped = line.startswith('***')
#            if not stopped: yield line
#            else: break
#                if line:
#                    yield line

def bible_verse_it():
    start_regex = re.compile(r'(?P<chapter>\d+):(?P<verse>\d+) (?P<text>.+)')
    testament = None
    book = None
    chapter = None
    verse = None
    text = None
    blank_lines_count = 0
    for line in bible_it():
        if not line.strip():
            blank_lines_count += 1
            if testament and book and chapter and verse and text:
                yield (testament, book, chapter, verse, text)
                text = None
        else:
            if 'Old Testament' in line or 'New Testament' in line:
                testament = line
                book = None
                chapter = None
                verse = None
                text = None
            else:
                if blank_lines_count > 3:
                    book = line
                else:
                    m = start_regex.match(line)
                    if m:
                        chapter = m.groupdict()['chapter']
                        verse = m.groupdict()['verse']
                        text = m.groupdict()['text']
                    else:
                        text += line
            blank_lines_count = 0

        

if __name__=='__main__':
    prev_book = None
    for x in bible_verse_it():
        testament,book,chapter,verse,text = x
        if prev_book is None or book!=prev_book:
            print x
            prev_book = book

#    for x in bible_it(): print x