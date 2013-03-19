## -*- coding: utf-8 -*-
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

import codecs
import os
import re

from topic_modeling import anyjson

def update_config(config):
    config['num_topics'] = 100
    config['num_iterations'] = 500
    config['token_regex'] = '[A-Za-zÂâ]+'.decode('utf-8') # Not sure why it's necessary to use .decode('utf-8'), but it doesn't work otherwise
    config['suppress_default_document_metadata_task'] = True
    config['extra_stopwords_file'] = lambda c: '%s/early-modern-english-extra-stopwords.txt' % c['raw_data_dir']
    config['num_topics'] = 100
    config['dataset_name'] = 'small_sacred'
    config['dataset_readable_name'] = 'Sacred Texts'
    config['dataset_description'] = 'A bunch of public domain religious texts.'
    config['pairwise_document_metrics'] = ['topic correlation']
    config['metadata_filenames'] = lambda c: {
          'datasets': '%s/datasets.json' % c['raw_data_dir']
    }

def create_tasks(c):

    def task_extract_data():
        task = dict()
        task['targets'] = [c['files_dir'], c['metadata_filenames']['documents']]
        task['actions'] = [
            (_extract, [c['raw_data_dir'], c['files_dir'], c['metadata_filenames']['documents']]
            )
        ]
        task['clean'] = ['rm -rf '+c['files_dir'], 'rm -rf '+c['metadata_filenames']['documents']]
        task['uptodate'] = [os.path.exists(c['files_dir'])]
        return task
    
    return [task_extract_data]

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

def _extract(data_dir, output_dir, metadata_filename):
    metadata_types = {
        'collection':'text',
        'work':'text',
        'title':'text',
        'chapter':'int',
        'number':'text',
        'name':'text',
        'other_number':'text'
    }
    metadata_data = {}
    
    # _extract_bible(data_dir + '/pg10_bible-kjv.txt', output_dir, metadata_data)
    _extract_book_of_mormon(data_dir + '/pg17_the-book-of-mormon.txt', output_dir, metadata_data)
    # _extract_koran(data_dir + '/pg3434_the-koran.txt', output_dir, metadata_data)
    # _extract_sacred_books_of_east(data_dir + '/pg12894_sacred-books-of-the-east.txt', output_dir, metadata_data)
    
    metadata = {'types':metadata_types, 'data':metadata_data}
    fp = open(metadata_filename, 'w')
    fp.write(anyjson.serialize(metadata))
    fp.close()

def _extract_bible(filename, output_dir, metadata):
    for testament, book, chapter, text in _bible_chapter_iterator(filename):
        subdir = '%s/%s' % (filename_abbrev[testament], filename_abbrev[book])
        subdir_abs = output_dir + '/' + subdir
        if not os.path.exists(subdir_abs): os.makedirs(subdir_abs)
        filename = subdir + '/' + chapter + '.txt'
        filename_abs = output_dir + '/' + filename
        
        fp = open(filename_abs, 'w')
        fp.write('%s\nChapter %s\n%s' % (book, chapter, text))
        print '%s %s' % (book, chapter)
        fp.close()
        
        #FIXME Psalms %num% -> Psalm %num%
        book_title = title_abbrev.get(book, filename_abbrev[book])
        title = '%s %s' % (book_title, chapter)
        
        metadata[filename] = {'collection':testament, 'work':book, 'title':title, 'chapter':chapter}
    
def _bible_iterator(filename):
    started = False
    for line in open(filename):
        line = line.strip()
        if not started: started = line.startswith('***')
        else:
            if line =='End of the Project Gutenberg EBook of The King James Bible':
                break
            else:
                yield line

def _bible_verse_iterator(filename):
    start_regex = re.compile(r'(?:(?P<chapter>\d+):(?P<verse>\d+) )?(?P<text>.+)')
    testament = None
    book = None
    chapter = None
    verse = None
    text = None
    blank_lines_count = 0
    for line in _bible_iterator(filename):
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

def _bible_chapter_iterator(filename):
    prev_testament, prev_book, prev_chapter = None, None, None
    text = None
    for x in _bible_verse_iterator(filename):
        testament,book,chapter,verse,_text = x
        
        if prev_chapter is None or prev_chapter != chapter:
            if text: yield (prev_testament, prev_book, prev_chapter, '\n\n'.join(text))
            text = ['%s:%s %s' % (chapter, verse, _text)]
        else:
            text += ['%s:%s %s' % (chapter, verse, _text)]
        prev_testament, prev_book, prev_chapter = testament, book, chapter
        
    yield (prev_testament, prev_book, prev_chapter, '\n\n'.join(text))

def _extract_koran(koran_filename, output_dir, metadata):
    subdir = 'Koran'
    subdir_abs = output_dir + '/' + subdir
    if not os.path.exists(subdir_abs): os.makedirs(subdir_abs)
    for num,name,newnum,text in koran_sura_iterator(koran_filename):
        filename = subdir + '/' + num + '.txt'
        filename_abs = output_dir + '/' + filename
        
        fp = open(filename_abs, 'w')
        _name = '\n'+name if name is not None else ''
        fp.write('The Koran\nSura %s%s\n\n%s' % (num, _name, text))
#        print '\n%s\nChapter %s\n%s' % (book, chapter, text)
        print 'Koran Sura %s' % (num)
        fp.close()
        
        title = 'Sura %s "%s"' % (num, name)
        metadata[filename] = {'collection':'The Koran', 'work':'The Koran', 'title':title, 'number':num, 'name':name, 'other_number':newnum}

def koran_iterator(filename):
    started = False
    for line in open(filename):
        line = line.strip()
        if not started: started = line=='*** START OF THE PROJECT GUTENBERG EBOOK, THE KORAN ***'
        else:
            if line=='End of The Project Gutenberg Etext of The Koran as translated by Rodwell End':
                break
            else:
                line = ''.join([c for c in line if c not in ('0123456789')])
                yield line.replace('',"'").replace('','"').replace('','"').replace('',' ')

romannum = '(?P<number>[IVXLC]+)'
def koran_sura_iterator(filename):
    sura_regex = re.compile('SURA1? '+romannum+'\.1? (?:(?P<name>[^1]+)1? )?\[(?P<newnumber>[IVXLC]+)\.\]')
    footnote_regex = re.compile('_+')
    sura_num, sura_name, sura_newnum = None,None,None
    text = None
    found_footnotes = False
    for line in koran_iterator(filename):
        m = sura_regex.match(line)
        if m:
            if text is not None and len(text) > 0:
                yield (sura_num, sura_name, sura_newnum, '\n'.join(text))
            text = []
            found_footnotes = False
            sura_num, sura_name, sura_newnum = m.groupdict()['number'], m.groupdict()['name'], m.groupdict()['newnumber']
        else:
            if not found_footnotes:
                m = footnote_regex.match(line)
                if m:
                    found_footnotes = True
                elif text is not None:
                    text += [line]
                
    yield (sura_num, sura_name, sura_newnum, '\n'.join(text))

def _extract_sacred_books_of_east(sboe_filename, output_dir, metadata):
    
    for d in _sboe_section_iterator(sboe_filename):
        subdir = 'SBOE/' + d['work'].replace(' ','_')
        subdir_abs = output_dir + '/' + subdir
        if not os.path.exists(subdir_abs): os.makedirs(subdir_abs)
        filename = subdir + '/' + d['title'].replace(' ','_') + '.txt'
        filename_abs = output_dir + '/' + filename
        
        fp = codecs.open(filename_abs, mode='w', encoding='utf-8')
        fp.write(d.pop('text'))
        fp.close()
        
        d['collection'] = 'Sacred Books of the East'
        metadata[filename] = d
        print d['title']

def _sboe_iterator(filename):
    started = False
    for line in codecs.open(filename, encoding='utf-8'):
        line = line.strip()
        if not started: started = line=='Division of the Sariras'
        else:
            if line=='***END OF THE PROJECT GUTENBERG EBOOK SACRED BOOKS OF THE EAST***':
                break
            else:
                yield line

caps = '[A-Z \-:\[\]0123456789,Â]+'
def _sboe_section_iterator(filename):
    min_length = 105
    def clean(text):
        for i in range(0,10) + ['[',']']:
            text = text.replace(str(i),'')
        return text
    def yield_me():
        if text:
            fulltext = '\n'.join(text)
            if len(fulltext) > min_length:
                d = {'text':fulltext}
                d['work'] = titles[0]
                d['title'] = ' '.join(titles[1:])
                return d
            else:
                raise Exception()
        else:
            raise Exception()
    sections = ('VEDIC HYMNS','SELECTIONS FROM THE ZEND-AVESTA','THE DHAMMAPADA','THE UPANISHADS','SELECTIONS FROM THE KORAN','LIFE OF BUDDHA')
    subsections = ['INTRODUCTION','TO THE UNKNOWN GOD','TO THE MARUTS','TO THE MARUTS AND INDRA','TO INDRA AND THE MARUTS','TO RUDRA','TO AGNI AND THE MARUTS','TO SOMA AND RUDRA','TO V\xc3\x82TA','TO V\xc3\x82YU','INDRA AND AGASTYA: A DIALOGUE']
    subsections += ['DISCOVERY OF THE ZEND-AVESTA', 'THE CREATION', 'MYTH OF YIMA', 'THE EARTH', 'CONTRACTS AND OUTRAGES', 'UNCLEANNESS', 'FUNERALS AND PURIFICATION', 'CLEANSING THE UNCLEAN', 'SPELLS RECITED DURING THE CLEANSING', 'TO FIRES, WATERS, PLANTS', 'TO THE EARTH AND THE SACRED WATERS', 'PRAYER FOR HELPERS', 'A PRAYER FOR SANCTITY AND ITS BENEFITS', 'TO THE FIRE', 'TO THE BOUNTIFUL IMMORTALS', 'PRAISE OF THE HOLY BULL', 'TO RAIN AS A HEALING POWER', 'TO THE WATERS AND LIGHT OF THE SUN', 'TO THE WATERS AND LIGHT OF THE MOON', 'TO THE WATERS AND LIGHT OF THE STARS']
    subsections += ['CHAPTER I', 'CHAPTER II', 'CHAPTER III', 'CHAPTER IV', 'CHAPTER V', 'CHAPTER VI', 'CHAPTER VII', 'CHAPTER VIII', 'CHAPTER IX', 'CHAPTER X', 'CHAPTER XI', 'CHAPTER XII', 'CHAPTER XIII', 'CHAPTER XIV', 'CHAPTER XV', 'CHAPTER XVI', 'CHAPTER XVII', 'CHAPTER XVIII', 'CHAPTER XIX', 'CHAPTER XX', 'CHAPTER XXI', 'CHAPTER XXII', 'CHAPTER XXIII', 'CHAPTER XXIV', 'CHAPTER XXV', 'CHAPTER XXVI']
    subsections += ['THE COUCH OF BRAHMAN', 'KNOWLEDGE OF THE LIVING SPIRIT', 'LIFE AND CONSCIOUSNESS']
    subsections += ['MOHAMMED AND MOHAMMEDANISM']
    titles = None
    text = None
    blank_lines = 0
    caps_regex = re.compile('^(?P<title>'+caps+')$')
    
    for line in _sboe_iterator(filename):
        if line:
            if line in sections:
                try: yield yield_me()
                except: pass
                titles, text = [line],[]
            else:
                m = caps_regex.match(line)
                if m:
                    try: yield yield_me()
                    except: pass
                    text = []
                    
                    new_titles = [clean(m.groupdict()['title'])]
                    
                    if new_titles[0] in subsections:
                        titles = titles[:1] + new_titles
                    else:
                        if len(titles) > 1:
                            if titles[1] in subsections:
                                if titles[1].startswith('CHAPTER '):
                                    titles[1] = titles[1] + ': ' + new_titles[0]
                                else:
                                    titles = titles[:2] + new_titles
                            else:
                                titles = titles[:1] + new_titles
                        else:
                            titles += new_titles
                else:
                    text += [line]
            blank_lines = 0
        else: blank_lines += 1

def _extract_book_of_mormon(bom_filename, output_dir, metadata):
    for d in _bom_chapter_iterator(bom_filename):
        subdir = (d['collection'] + '/' + d['work']).replace(' ','_')
        subdir_abs = output_dir + '/' + subdir
        if not os.path.exists(subdir_abs): os.makedirs(subdir_abs)
        filename = subdir + '/' + d['chapter'].replace(' ','_') + '.txt'
        filename_abs = output_dir + '/' + filename
        
        fp = open(filename_abs, mode='w')
        fp.write(d.pop('text'))
        fp.close()
        
        metadata[filename] = d
        print d['title']

def _bom_iterator(filename):
    started = False
    for line in open(filename):
        line = line.strip()
        if not started: started = line=='*** START OF THIS PROJECT GUTENBERG EBOOK THE BOOK OF MORMON ***'
        else:
            if line=='End of the Project Gutenberg EBook of The Book Of Mormon, by Anonymous':
                break
            else:
                yield line

def _bom_verse_iterator(filename):
    verse_regex = re.compile('(?P<book>(?:\d )?[^\d]+) (?P<chapter>\d+):(?P<verse>\d+)')
    book,chapter,verse,text = None,None,None,None
    def yield_me():
        return book, chapter, verse, '\n'.join(text).strip()
    for line in _bom_iterator(filename):
        if line:
            m = verse_regex.match(line)
            if m:
                book,chapter,verse = m.groups()
                text = []
            else:
                if text is not None: text += [line]
        else:
            if text:
                yield yield_me()
                text = None

def _bom_chapter_iterator(filename):
    book, chapter = None, None
    text = None
    
    def yield_me():
        title = '%s %s' % (book, chapter)
        return {'collection':'The Book of Mormon', 'work':book, 'title':title, 'chapter':chapter, 'text':'\n\n'.join(text).strip()}
    
    for x in _bom_verse_iterator(filename):
        book_,chapter_,_verse,_text = x
        
        if chapter is None or chapter != chapter_:
            if text: yield yield_me()
            text = [_text]
        else:
            text += [_text]
        book, chapter = book_, chapter_
        
    yield yield_me()

if __name__=='__main__':
    for line in _bom_chapter_iterator('/home/josh/Projects/topicalguide/raw-data/small_sacred/pg17_the-book-of-mormon.txt'):
        print line
#    for num,name,newnum,text in koran_sura_iterator('/home/josh/Projects/topicalguide/raw-data/small_sacred/pg3434_the-koran.txt'):
#        print '%s "%s" (%s)\n\n%s' % (num,name,newnum,text)
#        print '%s "%s" (%s)' % (num,name,newnum)
