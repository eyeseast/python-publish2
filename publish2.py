"""
My first attempt at an API wrapper.

Publish2 is a collaborative bookmarking tool for journalists.
While it doesn't have an API in the strictest sense, it does
provide JSON and ATOM feeds of any set of links.

Each feed provides metadata on the journalist or newsgroup
submitting links. Each item lists a title, link, tags, publication,
date submitted, date published and public comment.
"""
import datetime
import urllib, urllib2
try:
    import json
except ImportError:
    import simplejson as json


class Publish2Error(Exception):
    "Exception for Publish2 errors"

BASE_URL = 'http://www.publish2.com'

# results

class Publish2Object(object):
    "Base class for Publish2"
    def __init__(self, d):
        self.__dict__ = d
        
    
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__str__())

    def __str__(self):
        return ''


class Publish2Tag(Publish2Object):
    "A tag on a link"
    
    def __str__(self):
        return self.name


class Publish2Link(Publish2Object):
    "Link from a Publish2 feed"
        
    def __init__(self, d):
        self.__dict__ = d
        self.publication_date = self._set_pub_date()
        self.created_date = self._set_created()
        if hasattr(self, 'tags'):
            tags = self.tags[0].values()
            self.tags = [Publish2Tag(t) for t in tags]
        else:
            self.tags = []
        
    def _set_pub_date(self):
        "Returns a python datetime object from Publish2's date string"
        
        try:
            pd = datetime.datetime.strptime(self.publication_date, u'%B %d, %Y')
            return pd
        except ValueError:
            return self.publication_date
    
    def _set_created(self):
        format = u'%B %d, %Y at %I:%M%p %Z'
        try:
            dt = datetime.datetime.strptime(self.created_date, format)
            return dt
        except ValueError:
            return self.created_date
    
    def __str__(self):
        return self.title


class Publish2Feed(Publish2Object):
    "A feed of publish2 links"
    def __init__(self, d):
        self.__dict__ = d
        self.items = [Publish2Link(i) for i in getattr(self, 'items', [])]
        
    def __str__(self):
        return self.title


# utils
def slugify(value):
    "Simpler version of Django's slugify filter"
    return unicode(value).lower().replace(' ', '-')


def _parse_date(date_str, format_str):
    "Thin wrapper for error handling"
    try:
        dt = datetime.datetime.strptime(date_str, format_str)
    except ValueError:
        dt = None
    return dt


def _make_path(url):
    if url.startswith('/'):
        url = BASE_URL + url
    
    if url.endswith('/'):
        url = url.rstrip('/') + '.json'
    elif url.endswith('rss'):
        url = url.replace('.rss', '.json')
    
    if not url.endswith(u'.json'):
        url += u'.json'
    
    return url



def get_feed(url):
    if not url.endswith(u'.json'):
        url = _make_path(url)
    
    try:
        request = urllib2.urlopen(url).read()
        feed = json.loads(request)
        result = Publish2Feed(feed)
        return result
    except urllib2.HTTPError, e:
        raise Publish2Error(e.read())
    except (ValueError, KeyError), e:
        raise Publish2Error('Invalid response')


def get_for_journalist(name, topic=''):
    url = u'http://www.publish2.com/journalists/%(username)s/links' % {u'username': slugify(name)}
    if topic:
        url += u"/%s" % slugify(topic)
    url += u".json"
    return get_feed(url)


def get_for_newsgroup(name, topic=''):
    url = u'http://www.publish2.com/newsgroups/%s' % slugify(name)
    if topic:
        url += u"/%s" % slugify(topic)
    url += u".json"
    return get_feed(url)
