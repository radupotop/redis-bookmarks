import redis
import hashlib
import json
import logging
import urllib
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger('Bookmarks-lib')

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
    entry = json.loads(r.get('entry:'+entry_hash) or 'null')
    if not entry:
        return False

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
    return True

def get_all_entries(start=0, end=-1):
    """Get all entries with paging"""
    return r.zrevrange('entry_index', start, end)

def get_paged_entries(start_page=0, pg_size=2):
    """Get all entries with paging. Returns a generator."""
    skip = pg_size * start_page
    start, end = 0 + skip, pg_size -1 + skip
    while True:
        entries = r.zrevrange('entry_index', start, end)
        if not entries:
            break
        yield entries
        start, end = start + pg_size, end + pg_size

def _get_day_boundaries(days_delta=0):
    """
    Get a day's boundaries
    A days_delta of 0 means today.
    A days_delta of 1 means yesterday.

    UTC is not okay. we should use the user's timezone.
    """
    base_date = datetime.utcnow() - timedelta(days=int(days_delta))
    start_day = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = start_day + timedelta(days=1)
    log.debug('Day boundary start {} end {}'.format(start_day, end_day))
    return (start_day.timestamp(), end_day.timestamp())

def get_page_by_day(days_delta=0):
    """
    TODO
    Paging entries by a number (as done above) is not interesting.
    What would really help me recall bookmarks is paging them by days.
    Helping users recall bookmarked sites by putting them in the day's context.

    We could also group bookmarks by domain inside the day's view.
    """
    start, end = _get_day_boundaries(days_delta)
    return r.zrevrangebyscore('entry_index', end, start)

def group_by_domain(hash_entries):
    """
    Group entries by domain and then inside each domain, sort them by time,
    and then sort domains by the time of the first entry from each.
    Or alphabetically.
    
    Or better yet, do this on the frontend.
    """
    entries = (get_entry(h) for h in hash_entries)
    domains = {}
    for e in entries:
        domains[e['url_domain']] = domains.get(e['url_domain']) or []
        domains[e['url_domain']].append(e)
    return [{'domain': name, 'entries': ent} for name, ent in domains.items()]

def get_entry(entry_hash):
    return json.loads(r.get('entry:'+entry_hash) or 'null')

def get_entries(entry_list):
    return [get_entry(e) for e in entry_list]

def get_all_tags():
    return r.smembers('tag_index')

def get_entries_for_tag(tagname):
    return r.smembers('tag:'+tagname)

def get_all_domains():
    return r.smembers('domain_index')

def get_entries_for_domain(domain):
    return r.smembers('domain:'+domain)
