from __future__ import division, print_function, unicode_literals
from json import loads

# Get function to turn a csv string into a list and check that the arguments are valid.
def get_list_filter(allowed_values, allow_star=False):
    allowed_values = set(allowed_values)
    def list_filter(s):
        if allow_star and s == '*':
            return '*'
        result = set(s.split(','))
        if '' in result:
            result.remove('')
        for r in result:
            if r not in allowed_values:
                raise Exception('The value "%s" is not recognized.'%(r,))
        return list(result)
    return list_filter
        
# Turn string s into a list (delimited by commas) with no repeating values.
# Treat '*' as an exception since '*' means everything.
def filter_csv_to_list(s):
    if s == '':
        result = set()
    elif s == '*':
        return '*'
    elif s.find('%') >= 0: # Handle any unencoded unicode.
        result = set(s.encode('utf8').replace('%u', '\\u').decode('unicode_escape').split(','))
    else:
        result = set(s.split(','))
    if '' in result:
        result.remove('')
    return list(result)


def get_filter_csv_to_tuple(required_length):
    def filter_csv_to_tuple(s):
        if s == '':
            result = []
        elif s.find('%') >= 0: # Handle any unencoded unicode.
            result = s.encode('utf8').replace('%u', '\\u').decode('unicode_escape').split(',')
        else:
            result = s.split(',')
        if '' in result:
            result.remove('')
        if len(result) != required_length:
            raise Exception('Must have argument of length two.')
        return result
    return filter_csv_to_tuple

def get_filter_csv_to_numeric_tuple(required_length):
    def filter_csv_to_numeric_tuple(s):
        if s == '':
            result = []
        elif s.find('%') >= 0: # Handle any unencoded unicode.
            result = s.encode('utf8').replace('%u', '\\u').decode('unicode_escape').split(',')
        else:
            result = s.split(',')
        if '' in result:
            result.remove('')
        if len(result) != required_length:
            raise Exception('Must have argument of length two.')
        
        return [float (num) for num in result]
    return filter_csv_to_numeric_tuple

# Get function to turn a string into an int within the bounds given.
def get_filter_int(low=-2147483648, high=2147483647):
    def filter_int(s):
        result = int(s)
        if result < low:
            result = low
        if result > high:
            result = high
        return result
    return filter_int
    
def filter_to_json(s):
    return loads(s)

# A do-nothing filter.
def filter_nothing(arg):
    return arg

# Filter the incoming request to make sure that bogus values are removed and errors are thrown.
def filter_request(request_keys, filters):
    result = {}
    for key in request_keys:
        if key in filters:
            result[key] = filters[key](request_keys[key])
        else:
            raise Exception("No such value as "+key+".")
    return result
