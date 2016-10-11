from aiohttp import web
import json
import logging

import bookmarks

logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger()

headers = {
    'Content-type': 'application/json',
    'Server': 'Bookmarks HTTP',
}

async def index(Request):
    """A GraphQL inspired HTTP API"""
    resource = Request.match_info.get('resource')
    subresource = Request.match_info.get('subresource')

    if resource in [None]:
        all_entries = json.dumps(list(bookmarks.get_all_entries()))
        return web.Response(text=all_entries, headers=headers)

app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/{resource}', index)
app.router.add_get('/{resource}/{subresource}', index)

web.run_app(app)
