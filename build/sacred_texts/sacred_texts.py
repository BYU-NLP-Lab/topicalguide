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
import os
import re
from topic_modeling import anyjson

dataset_name = 'sacred_texts'
dataset_readable_name = 'Sacred Texts'
dataset_description = '''A bunch of public domain religious texts.'''
suppress_default_document_metadata_task = True
extra_stopwords_file = os.curdir + '/build/sacred_texts/early-modern-english-extra-stopwords.txt'
metadata_filenames = {'datasets': '%s/raw-data/%s/datasets.json' % (os.curdir, dataset_name)}

filename_abbrev = {
    'The New Testament of the King James Bible':'NT',
    'The Old Testament of the King James Version of the Bible':'OT',
    'The Acts of the Apostles':'Acts',
    'The First Epistle of Paul the Apostle to Timothy':'1_Timothy',
    'The Epistle of Paul the Apostle to the Colossians':'Colossians',
    'The General Epistle of James':'James',
    'The Epistle of Paul the Apostle to the Ephesians':'Ephesians',
    'The Gospel According to Saint John':'John',
    'The Epistle of Paul the Apostle to the Galatians':'Galatians',
    'The Gospel According to Saint Luke':'Luke',
    'The Epistle of Paul the Apostle to the Hebrews':'Hebrews',
    'The Gospel According to Saint Mark':'Mark',
    'The Epistle of Paul the Apostle to the Philippians':'Philippians',
    'The Gospel According to Saint Matthew':'Matthew',
    'The Epistle of Paul the Apostle to the Romans':'Romans',
    'The Revelation of Saint John the Devine':'Revelation',
    'The Epistle of Paul the Apostle to Titus':'Titus',
    'The Second Epistle of Paul the Apostle to the Corinthians':'2_Corinthians',
    'The First Epistle General of John':'1_John',
    'The Second Epistle of Paul the Apostle to the Thessalonians':'2_Thessalonians',
    'The First Epistle General of Peter':'1_Peter',
    'The Second Epistle of Paul the Apostle to Timothy':'2_Timothy',
    'The First Epistle of Paul the Apostle to the Corinthians':'1_Corinthians',
    'The Second General Epistle of Peter':'2_Peter',
    'The First Epistle of Paul the Apostle to the Thessalonians':'1_Thessalonians',
    'Amos':'Amos',
    'Malachi':'Malachi',
    'The Book of Nehemiah':'Nehemiah',
    'The First Book of Samuel':'1_Samuel',
    'The Second Book of the Chronicles':'2_Chronicles',
    'Ecclesiastes':'Ecclesiastes',
    'Micah':'Micah',
    'The Book of Psalms':'Psalms',
    'The First Book of the Chronicles':'1_Chronicles',
    'The Second Book of the Kings':'2_Kings',
    'Ezra':'Ezra',
    'Nahum':'Nahum',
    'The Book of Ruth':'Ruth',
    'The First Book of the Kings':'1_Kings',
    'The Song of Solomon':'Song',
    'Habakkuk':'Habakkuk',
    'The Book of Daniel':'Daniel',
    'The Book of the Prophet Ezekiel':'Ezekiel',
    'The Fourth Book of Moses:  Called Numbers':'Numbers',
    'The Third Book of Moses:  Called Leviticus':'Leviticus',
    'Haggai':'Haggai',
    'The Book of Esther':'Esther',
    'The Book of the Prophet Isaiah':'Isaiah',
    'The Lamentations of Jeremiah':'Lamentations',
    'Zechariah':'Zechariah',
    'Hosea':'Hosea',
    'The Book of Job':'Job',
    'The Book of the Prophet Jeremiah':'Jeremiah',
    'The Proverbs':'Proverbs',
    'Zephaniah':'Zephaniah',
    'Joel':'Joel',
    'The Book of Joshua':'Joshua',
    'The Fifth Book of Moses:  Called Deuteronomy':'Deuteronomy',
    'The Second Book of Moses:  Called Exodus':'Exodus',
    'Jonah':'Jonah',
    'The Book of Judges':'Judges',
    'The First Book of Moses:  Called Genesis':'Genesis',
    'The Second Book of Samuel':'2_Samuel'
}

title_abbrev = {
    'The New Testament of the King James Bible':'The New Testament',
    'The Old Testament of the King James Version of the Bible':'The Old Testament',
    'The First Epistle of Paul the Apostle to Timothy':'1st Timothy',
    'The Second Epistle of Paul the Apostle to the Corinthians':'2nd Corinthians',
    'The First Epistle General of John':'1st John',
    'The Second Epistle of Paul the Apostle to the Thessalonians':'2nd Thessalonians',
    'The First Epistle General of Peter':'1st Peter',
    'The Second Epistle of Paul the Apostle to Timothy':'2nd Timothy',
    'The First Epistle of Paul the Apostle to the Corinthians':'1st Corinthians',
    'The Second General Epistle of Peter':'2nd Peter',
    'The First Epistle of Paul the Apostle to the Thessalonians':'1st Thessalonians',
    'The First Book of Samuel':'1st Samuel',
    'The Second Book of the Chronicles':'2nd Chronicles',
    'The First Book of the Chronicles':'1st Chronicles',
    'The Second Book of the Kings':'2nd Kings',
    'The First Book of the Kings':'1st Kings',
    'The Song of Solomon':'Song of Solomon',
    'The Second Book of Samuel':'2nd Samuel'
}

def task_extract_data():
    task = dict()
    task['targets'] = [files_dir, metadata_filenames['documents']]
    task['actions'] = [
        (_extract, [raw_data_dir, files_dir, metadata_filenames['documents']]
        )
    ]
    task['clean'] = ['rm -rf '+files_dir, 'rm -rf '+metadata_filenames['documents']]
    task['uptodate'] = [os.path.exists(files_dir)]
    return task

def _extract(data_dir, output_dir, metadata_filename):
    metadata_types = {'testament':'text','book':'text','chapter':'int','title':'text'}
    metadata_data = {}
    bible_filename = data_dir + '/sacred_texts/pg10_bible-kjv.txt'
    for testament, book, chapter, text in bible_chapter_iterator(bible_filename):
        subdir = '%s/%s' % (filename_abbrev[testament], filename_abbrev[book])
        subdir_abs = output_dir + '/' + subdir
        if not os.path.exists(subdir_abs): os.makedirs(subdir_abs)
        filename = subdir + '/' + chapter + '.txt'
        filename_abs = output_dir + '/' + filename
        
        fp = open(filename_abs, 'w')
        fp.write('%s\nChapter %s\n%s' % (book, chapter, text))
#        print '\n%s\nChapter %s\n%s' % (book, chapter, text)
        print '%s %s' % (book, chapter)
        fp.close()
        
        #FIXME Psalms %num% -> Psalm %num%
        book_title = title_abbrev.get(book, filename_abbrev[book])
        title = '%s %s' % (book_title, chapter)
        
        metadata_data[filename] = {'testament':testament, 'book':book, 'chapter':chapter, 'title':title}
    
    metadata = {'types':metadata_types, 'data':metadata_data}
    fp = open(metadata_filename, 'w')
    fp.write(anyjson.serialize(metadata))
    fp.close()

def bible_it(filename):
    started = False
    for line in open(filename):
        line = line.strip()
        if not started: started = line.startswith('***')
        else:
            if line =='End of the Project Gutenberg EBook of The King James Bible':
                break
            else:
                yield line

def bible_verse_it(filename):
    start_regex = re.compile(r'(?:(?P<chapter>\d+):(?P<verse>\d+) )?(?P<text>.+)')
    testament = None
    book = None
    chapter = None
    verse = None
    text = None
    blank_lines_count = 0
    for line in bible_it(filename):
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

def bible_chapter_iterator(filename):
    prev_testament, prev_book, prev_chapter = None, None, None
    text = None
    for x in bible_verse_it(filename):
        testament,book,chapter,verse,_text = x
        
        if prev_chapter is None or prev_chapter != chapter:
            if text: yield (prev_testament, prev_book, prev_chapter, '\n\n'.join(text))
            text = ['%s:%s %s' % (chapter, verse, _text)]
        else:
            text += ['%s:%s %s' % (chapter, verse, _text)]
        prev_testament, prev_book, prev_chapter = testament, book, chapter
        
    yield (prev_testament, prev_book, prev_chapter, '\n\n'.join(text))
