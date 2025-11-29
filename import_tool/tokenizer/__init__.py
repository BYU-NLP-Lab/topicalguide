from regex import RegexTokenizer

# Put any custom tokenizers here.
tokenizers = {
}

def get_tokenizer(tokenizer_name):
    """Return a tokenizer according to the given name. If there is
    no tokenizer by the name, the name is assumed to be a python token regex.
    """
    if tokenizer_name in tokenizers:
        return tokenizers[tokenizer_name]()
    else: 
        return RegexTokenizer(tokenizer_name)
