from sanic import Sanic
from sanic.response import json
import logging
from pprint import pprint

import bookmarks

logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger()

app = Sanic(__name__)

@app.route('/entries')
async def index(request):
    return json(bookmarks.get_all_entries())

@app.route('/entries/day/<day:int>')
async def get_day(request, day):
    """Get entries paged by day"""
    return json(bookmarks.get_page_by_day(day))

@app.route('/entries/tag/<tag>')
async def get_entries_for_tag(request, tag):
    return json(bookmarks.get_entries_for_tag(tag))

@app.route('/entries/domain/<domain>')
async def get_entries_for_domain(request, domain):
    pprint(domain)
    return json(bookmarks.get_entries_for_domain(domain))

@app.route('/tags')
async def get_all_tags(request):
    return json(bookmarks.get_all_tags())

@app.route('/domains')
async def get_all_domains(request):
    return json(bookmarks.get_all_domains())

app.run(host='0.0.0.0', port=8000, debug=True)
