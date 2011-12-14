import re
def bible_it():
    started = False
    stopped = False
    
    for line in open('./datasets/sacred_texts/raw/pg10_bible-kjv.txt'):
        line = line.strip()
        if not started: started = line.startswith('***')
        else:
            stopped = line.startswith('***')
            if not stopped: yield line
#                if line:
#                    yield line

def bible_verse_it():
    start_regex = re.compile(r'(?P<chapter>\d+):(?P<verse>\d+).*')
    testament = None
    book = None
    chapter = None
    verse = None
    text = None
    blank_lines_count = 0
    for line in bible_it():
        if not line: blank_lines_count += 1
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
            blank_lines_count = 0
#        m = start_regex.match(line)
#        if m:
#            if text:
#                pass
#        else:
#            pass
        if testament and book:
            yield (testament, book, chapter, verse, text)

if __name__=='__main__':
    prev_book = None
    for x in bible_verse_it():
        testament,book,chapter,verse,text = x
        if prev_book is None or book!=prev_book:
            print x
            prev_book = book
#    for book,chapter,verse,text in bible_verse_it():
#        print '%s %s:%s\n%s' % (book,chapter,verse,text)
#    for x in bible_it(): print x