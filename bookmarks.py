import redis
import hashlib
import json
from datetime import datetime

# localhost, defaults
r = redis.StrictRedis(db=0, decode_responses=True)

valid_keys = ['url', 'title', 'tags']

class ValidationError(Exception):
    pass

def validate_entry(entry):
    for k in valid_keys:
        if not k in entry:
            raise ValidationError('Key <{}> not in entry',format(k))
    return entry

def add_tags(entry_tags, entry_hash):
    for tag in entry_tags:
        r.sadd('tag:'+tag, entry_hash)

def add_entry(entry):
    entry['date'] = datetime.utcnow()
    entry_hash = hashlib.sha1(entry['url'].encode()).hexdigest()
    entry_body = json.dumps(entry)

    r.set('entry:'+entry_hash, entry_body)
    add_tags(entry['tags'], entry_hash)
    
    return entry_hash

def update_index(entry_hash):
    r.sadd('index', entry_hash)

def remove_entry(entry_hash):
    r.del('entry:'+entry_hash)
