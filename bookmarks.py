import redis
import hashlib
import json
import logging
import urllib
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger()

# localhost, defaults
r = redis.StrictRedis(db=0, decode_responses=True)

valid_keys = ['url', 'title', 'tags']


_samples = [
    {'url':'http://kernel.org', 'title':'The Linux Kernel Homepage', 'tags':['linux', 'kernel']},
    {'url':'http://reddit.com', 'title':'The front page of the internet', 'tags':['reddit', 'social', 'news']},
    {'url':'http://news.ycombinator.com', 'title':'Hacker News', 'tags':['hackers', 'news', 'social']},
]


class ValidationError(Exception):
    pass

def validate_entry(entry):
    for k in valid_keys:
        if not k in entry:
            raise ValidationError('Key <{}> not in entry',format(k))
    return entry

def add_entry(entry):
    entry['date'] = datetime.utcnow().isoformat()
    entry['url_domain'] = urllib.parse.urlsplit(entry['url']).netloc

    entry_hash = hashlib.sha1(entry['url'].encode()).hexdigest()
    entry_body = json.dumps(entry)
    entry_tags = set(entry['tags'])

    r.set('entry:'+entry_hash, entry_body)

    for tag in entry_tags:
        r.sadd('tag:'+tag, entry_hash)
    r.sadd('tag_index', *entry_tags)

    r.sadd('index', entry_hash)
    r.sadd('domain:'+entry['url_domain'], entry_hash)
    
    return entry_hash

def remove_entry(entry_hash):
    entry = json.loads(r.get('entry:'+entry_hash))
    entry_tags = set(entry['tags'])

    for tag in entry_tags:
        r.srem('tag:'+tag, entry_hash)

    unused_tags = [t for t in entry_tags if r.scard('tag:'+t) == 0]

    log.debug('Removing unused tags {}'.format(unused_tags))

    for tag in unused_tags:
        r.delete('tag:'+tag)

    r.srem('tag_index', *unused_tags)

    log.debug('Removing entry {}'.format(entry_hash))

    r.srem('index', entry_hash)
    r.delete('entry:'+entry_hash)
