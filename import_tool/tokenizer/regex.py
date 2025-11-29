import re
from .abstract_tokenizer import AbstractTokenizer


class RegexTokenizer(AbstractTokenizer):
    def __init__(self, regex):
        self._comipiled_regex = re.compile(regex, re.UNICODE)
    
    def tokenize(self, text):
        seq = []
        for match in self._compiled_regex.finditer(text):
            seq.append((match.group().lower(), match.start()))
        return seq
