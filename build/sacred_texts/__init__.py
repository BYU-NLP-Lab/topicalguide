import re
def bible_it():
    started = False
    for line in open('./raw-data/sacred_texts/pg10_bible-kjv.txt'):
        line = line.strip()
        if not started: started = line.startswith('***')
        else:
            if line =='End of the Project Gutenberg EBook of The King James Bible':
                break
            else:
                yield line

def bible_verse_it():
    start_regex = re.compile(r'(?:(?P<chapter>\d+):(?P<verse>\d+) )?(?P<text>.+)')
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
                        d = m.groupdict()
                        _chapter = d['chapter']
                        if _chapter: chapter = _chapter
                        _verse = d['verse']
                        if _verse: verse = _verse
                        _text = m.groupdict()['text']
                        if blank_lines_count > 0:
                            text = _text
                        else:
                            text += ' ' + _text
                    else:
                        if text is None:
                            print 'oops'
                        text += ' ' + line
            blank_lines_count = 0

if __name__=='__main__':
    
    prev = None
    prev_chapter = None
    text = ''
    for x in bible_verse_it():
        testament,book,chapter,verse,_text = x
        
        if prev is None or prev[2] != chapter:
            if text: print '%s %s: %s' % (prev[1], prev[2], text)
            text = _text
        else:
            text += _text
        prev = x
        
    print '%s %s: %s' % (prev[1], prev[2], text)