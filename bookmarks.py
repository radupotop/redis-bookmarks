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
    {'url':'http://reddit.com/r/aww', 'title':'Things that make you go AWW!', 'tags':['reddit', 'social', 'aww', 'pics']},
    {'url':'https://reddit.com/r/programming', 'title':'r/programming', 'tags':['reddit', 'programming', 'development']},
]


class ValidationError(Exception):
    pass

def validate_entry(entry):
    for k in valid_keys:
        if not k in entry:
            raise ValidationError('Key <{}> not in entry',format(k))
    return entry

def add_entry(entry):
    _now = datetime.utcnow()
    unix_ts = _now.timestamp()

    entry['date'] = _now.isoformat()
    entry['url_domain'] = urllib.parse.urlsplit(entry['url']).netloc

    entry_hash = hashlib.sha1(entry['url'].encode()).hexdigest()
    entry_body = json.dumps(entry)
    entry_tags = set(entry['tags'])

    r.set('entry:'+entry_hash, entry_body)
    r.zadd('entry_index', unix_ts, entry_hash)

    for tag in entry_tags:
        r.sadd('tag:'+tag, entry_hash)
    r.sadd('tag_index', *entry_tags)
    
    r.sadd('domain:'+entry['url_domain'], entry_hash)
    r.sadd('domain_index', entry['url_domain'])
    
    return entry_hash

def remove_entry(entry_hash):
    entry = json.loads(r.get('entry:'+entry_hash))
    entry_tags = set(entry['tags'])
    domain_key = 'domain:'+entry['url_domain']

    for tag in entry_tags:
        r.srem('tag:'+tag, entry_hash)

    unused_tags = [t for t in entry_tags if r.scard('tag:'+t) == 0]

    log.debug('Removing unused tags {}'.format(unused_tags))

    for tag in unused_tags:
        r.delete('tag:'+tag)

    r.srem('tag_index', *unused_tags)

    r.srem(domain_key, entry_hash)
    if r.scard(domain_key) == 0:
        r.delete(domain_key)
        r.srem('domain_index', entry['url_domain'])
        log.debug('Deleted empty domain {}'.format(domain_key))

    log.debug('Removing entry {}'.format(entry_hash))

    r.zrem('entry_index', entry_hash)
    r.delete('entry:'+entry_hash)

def get_all_entries(start=0, end=-1):
    """Get all entries with paging"""
    return r.zrevrange('entry_index', start, end)

def get_paged_entries(pg_size=2):
    """Get all entries with paging. Returns a generator."""
    start, end = 0, pg_size-1
    while True:
        entries = r.zrevrange('entry_index', start, end)
        if not entries:
            break
        yield entries
        start, end = start + pg_size, end + pg_size

def get_entry(entry_hash):
    return json.loads(r.get('entry:'+entry_hash))

def get_all_tags():
    return r.smembers('tag_index')

def get_entries_for_tag(tagname):
    return r.smembers('tag:'+tagname)

def get_all_domains():
    return r.smembers('domain_index')

def get_entries_for_domain(domain):
    return r.smembers('domain:'+domain)
