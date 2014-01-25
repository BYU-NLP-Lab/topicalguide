from __future__ import print_function

import os
import sys
import json

# This script extracts the documents from the conference_talks dataset

def parse_headers(headers):
	result = {}
	for line in headers:
		parts = line.split(':', 1)
		if len(parts) == 2:
			result[parts[0].strip().lower()] = parts[1].strip()
	return result


def move_and_rename_files(file_name):
	with open(file_name, 'r') as file_with_names:
		list_of_files = file_with_names.read().splitlines()
		for conference_file in list_of_files:
			with open(conference_file, 'r') as file:
				contents = file.read()
				contents = contents.split('\n\n', 1)
				
				parsed_headers = parse_headers(contents[0].splitlines())
				
				new_file_name = parsed_headers['year'] + '_' +\
								parsed_headers['month'] + '_' + \
								parsed_headers['speaker'].replace(' ', '_')
				new_file_name = new_file_name.replace('.', '') + '.txt'
				
				body = contents[1]
				with open(os.path.join('documents', new_file_name), 'w+') as dest_file:
					dest_file.write(contents[0])
					dest_file.write('\n\n')
					dest_file.write(body)
				








if __name__ == "__main__":
	print("Starting conversion.")
	move_and_rename_files("agency.txt")
