import os, json, codecs, re
from build.nytimes_twitter.clean_tweets import TweetCleaner

dataset_name = 'twitter_state_union'
dataset_description = '''Twitters sample feed from ten minutes before the start of the address to half an hour after.'''

num_topics = 1000
mallet_num_iterations = 1000

twitter_stream_file = 'twitter_stream.txt'

def task_attributes():
    task = dict()
    task['targets'] = [attributes_file]
    task['actions'] = [(generate_attributes_file,
                        [dataset_dir + '/' + twitter_stream_file,
                         attributes_file])]
    task['clean'] = ['rm -f ' + attributes_file]
    return task

def task_extract_data():
    task = dict()
    task['targets'] = [files_dir]
    task['actions'] = [
        (extract_twitter_data,
         [dataset_dir + '/' + twitter_stream_file,
          files_dir]
        )
    ]
    task['clean'] = ['rm -rf ' + files_dir]
    task['uptodate'] = [os.path.exists(files_dir)]
    return task

def valid_tweet(tweet):
    if 'text' not in tweet:
        return False
    elif 'id' not in tweet:
        return False
    elif 'user' not in tweet:
        return False
    elif 'followers_count' not in tweet['user']:
        return False
    elif 'friends_count' not in tweet['user']:
        return False
    else:
        return True

def extract_twitter_data(data_file, dest_dir):
    data_file = codecs.open(data_file, encoding='utf-8', mode='r')
    decoder = json.JSONDecoder()
    if not os.path.exists(dest_dir): os.mkdir(dest_dir)
    cleaner = TweetCleaner('', '')

    for line in data_file:
        tweet = decoder.decode(line)
        if not valid_tweet(tweet):
            continue
        text = cleaner.cleaned_text(tweet['text'].lower())
        id = tweet['id']
        filename = "{0}.txt".format(str(id))
        file = codecs.open(dest_dir + '/' + filename,
                           encoding='utf-8',
                           mode='w')
        file.write(text)

#this ugly function could be nicer if the plot tab
#could sort numeric attribute properly
def bin_tweet_count(count):
    if not count or count <= 10:
        return 'a 10'
    elif count <= 20:
        return 'b 20'
    elif count <= 50:
        return 'c 50'
    elif count <= 100:
        return 'd 100'
    elif count <= 500:
        return 'e 500'
    elif count <= 1000:
        return 'f 1000'
    elif count <= 5000:
        return 'g 5000'
    elif count <= 10000:
        return 'h 10000'
    elif count <= 50000:
        return 'i 50000'
    elif count <= 100000:
        return 'j 100000'
    elif count <= 500000:
        return 'k 500000'
    elif count <= 1000000:
        return 'l 1000000'
    else:
        return 'm 1000000+'

def bin_tweet_name(name, count):
    if count < 100000:
        return 'none-star'
    else:
        return name

def generate_attributes_file(data_file, output_file):
    out = codecs.open(output_file, encoding='utf-8', mode='w')
    decoder = json.JSONDecoder()
    data = codecs.open(data_file, encoding='utf-8', mode='r')

    out.write('[\n')
    for line in data:
        tweet = decoder.decode(line)
        if not valid_tweet(tweet):
            continue

        #get attrs and path
        followers = tweet['user']['followers_count']
        name = bin_tweet_name(tweet['user']['screen_name'], followers)
        followers = bin_tweet_count(followers)
        friends = bin_tweet_count(tweet['user']['friends_count'])
        if re.match('\\brt\\b', tweet['text'].lower()):
            retweet = 'True'
        else:
            retweet = 'False'
        filename = '{0}.txt'.format(tweet['id'])

        out.write('{')
        out.write('"attributes": {')
        out.write('"followers":"{0}",'.format(followers))
        out.write('"friends":"{0}",'.format(friends))
        out.write(u'"name":"{0}",'.format(name))
        out.write('"retweet":"{0}"'.format(retweet))
        out.write('},')
        out.write('"path": "{0}"'.format(filename))
        out.write('},\n')# HACK!!! still have to manually remove last comma...

    out.write(']')

#these metrics were taking 20 secs per document
#too slow for 60k+ docs
def task_pairwise_document_metrics():
    task = dict()
    task['actions'] = None
    return task
