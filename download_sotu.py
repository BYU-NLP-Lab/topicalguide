#!/usr/bin/env python3
"""
Download State of the Union Addresses from American Presidency Project

This script downloads recent State of the Union addresses (2011-2025) from the
American Presidency Project website and formats them for use in the Topical Guide.

The script:
- Downloads speeches from specified URLs
- Extracts the speech text from HTML
- Formats metadata (president, date, address number)
- Saves files to default_datasets/state_of_the_union/documents/

Usage:
    python download_sotu.py

The downloaded speeches will be saved as:
    default_datasets/state_of_the_union/documents/{President_Name}_{Number}.txt

Requirements:
    - requests
    - beautifulsoup4

Note: WikiSource provides speeches from 1790-2010. This script complements that
dataset with speeches from 2011-2025.
"""

import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path

# State of the Union speeches to download from American Presidency Project
SPEECHES = [
    # Obama (continued)
    {"president": "Barack Obama", "num": 3, "date": "2011-01-25", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-19"},
    {"president": "Barack Obama", "num": 4, "date": "2012-01-24", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-20"},
    {"president": "Barack Obama", "num": 5, "date": "2013-02-12", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-21"},
    {"president": "Barack Obama", "num": 6, "date": "2014-01-28", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-22"},
    {"president": "Barack Obama", "num": 7, "date": "2015-01-20", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-23"},
    {"president": "Barack Obama", "num": 8, "date": "2016-01-12", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-24"},

    # Trump (first term)
    {"president": "Donald Trump", "num": 1, "date": "2017-02-28", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-0"},
    {"president": "Donald Trump", "num": 2, "date": "2018-01-30", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-25"},
    {"president": "Donald Trump", "num": 3, "date": "2019-02-05", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-26"},
    {"president": "Donald Trump", "num": 4, "date": "2020-02-04", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-27"},

    # Biden
    {"president": "Joe Biden", "num": 1, "date": "2021-04-28", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-1"},
    {"president": "Joe Biden", "num": 2, "date": "2022-03-01", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-7"},
    {"president": "Joe Biden", "num": 3, "date": "2023-02-07", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-8"},
    {"president": "Joe Biden", "num": 4, "date": "2024-03-07", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-the-state-the-union-9"},

    # Trump (second term)
    {"president": "Donald Trump", "num": 5, "date": "2025-03-04", "url": "https://www.presidency.ucsb.edu/documents/address-before-joint-session-the-congress-4"},
]

def download_speech(speech_info):
    """Download and parse a speech from the American Presidency Project"""
    print(f"Downloading {speech_info['president']} #{speech_info['num']} ({speech_info['date']})...")

    try:
        response = requests.get(speech_info['url'], timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the speech content
        content_div = soup.find('div', class_='field-docs-content')
        if not content_div:
            print(f"  ERROR: Could not find content for {speech_info['president']} #{speech_info['num']}")
            return None

        # Extract text and clean it up
        paragraphs = content_div.find_all('p')
        text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

        # Parse the date
        year, month, day = speech_info['date'].split('-')
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        month_name = month_names[int(month)]

        # Create metadata
        metadata = f"""address_number: {speech_info['num']}
title: {speech_info['president']}'s {'Ordinal' if speech_info['num'] == 1 else 'Ordinal'} State of the Union Address
author_name: {speech_info['president']}
month: {month_name}
president_name: {speech_info['president']}
year: {year}
day: {int(day)}

"""

        # Fix ordinal numbers
        ordinals = {1: 'First', 2: 'Second', 3: 'Third', 4: 'Fourth', 5: 'Fifth',
                   6: 'Sixth', 7: 'Seventh', 8: 'Eighth', 9: 'Ninth', 10: 'Tenth'}
        ordinal = ordinals.get(speech_info['num'], f"{speech_info['num']}th")
        metadata = metadata.replace('Ordinal', ordinal)

        full_text = metadata + text

        return full_text

    except Exception as e:
        print(f"  ERROR downloading {speech_info['president']} #{speech_info['num']}: {e}")
        return None

def save_speech(speech_info, content):
    """Save a speech to a file"""
    # Create filename
    president_name = speech_info['president'].replace(' ', '_')
    filename = f"{president_name}_{speech_info['num']}.txt"
    filepath = Path('default_datasets/state_of_the_union/documents') / filename

    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Saved to {filename}")

def main():
    """Download all speeches"""
    print("Downloading recent State of the Union addresses...")
    print()

    for speech in SPEECHES:
        content = download_speech(speech)
        if content:
            save_speech(speech, content)
        print()

    print("Done!")

if __name__ == '__main__':
    main()
