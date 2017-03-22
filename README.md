A Redis-based bookmarks service - like Pocket
---------------------------------------------

Enables users to easily recall bookmarked sited by aggregating them by day and 
by associating them with tags and domains.

Bookmarks can initally be browsed by day (default), by tag, or by domain.

Display bookmarked sites by __selecting__ them:

* by day and then further groupping them by tag (with `by domain` as an alternative)
* by tag and then further groupping them by day and sorting them chronologically (with a sub-groupping `by domain` as an option)
* by domain and then further groupping them by day and sub-groupping by tag


A Chrome extension will enable easy adding of bookmarks and tagging them. Just like Pocket.


Architecture
------------

* The Angular GUI manages bookmarks (reads/deletes from the API)
* The Chrome extension adds bookmarks (adds to the API)
* The API is a Flask or Sanic app that exposes routes which map to the bookmarks lib
* Bookmarks lib stores bookmarks in Redis

    -----------------
    |  Angular GUI  |
    -----------------      --------------------
    |      API      | <--- | Chrome extension |
    -----------------      --------------------
    | Bookmarks lib |
    -----------------


Todo
----

* Auth
* Multi-user support
* Chrome ext.
