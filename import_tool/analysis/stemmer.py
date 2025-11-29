
import os
import io
import subprocess
from os.path import join, abspath

class Stemmer(object):
    """This uses the Snowball program to find stems."""
    
    def __init__(self, directory, topical_guide_root_dir):
        """
        directory is the directory to be used to make temporary files, it should be an absolute path.
        topical_guide_root_dir is the directory from which this process can find the stemmer.
        """
        self.directory = directory
        self.input_file = join(directory, 'porter2_snowball_input.txt')
        self.output_file = join(directory, 'porter2_snowball_output.txt')
        self.stemmer_path = abspath(join(topical_guide_root_dir, 'tools/stemmer/stemmer'))
    
    def stem(self, token_sequence):
        with io.open(self.input_file, 'w', encoding='utf8') as f:
            for token in token_sequence:
                f.write(token+'\n')
        
        cmd = [self.stemmer_path, self.input_file,
               '-o', self.output_file]
        
        try:
            subprocess.check_call(cmd)
        except: # cleanup if an error occurs before propagating the error
            self._cleanup()
            print('Make sure you ran: make_english_stemmer.sh from the directory tools/stemmer/')
            print('This will compile the stemmer for your machine.')
            raise
        
        result = []
        with io.open(self.output_file, 'r', encoding='utf8') as f:
            for line in f:
                result.append(line.strip())
        
        #~ self._cleanup()
        
        return result
    
    def _cleanup(self):
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
