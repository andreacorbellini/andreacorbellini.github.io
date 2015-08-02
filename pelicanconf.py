import socket
from flask.json import tojson_filter


def get_ip_address():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('8.8.8.8', 80))
        return sock.getsockname()[0]
    finally:
        sock.close()


# General.
AUTHOR = 'Andrea Corbellini'
SITENAME = 'Andrea Corbellini'
SITEURL = 'http://{}:8000'.format(get_ip_address())
RELATIVE_URLS = False

TIMEZONE = 'UTC'
DEFAULT_LANG = 'en'


# URLs and paths.
PAGE_URL = '{slug}/'
ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
CATEGORY_URL = 'category/{slug}/'
TAG_URL = 'tag/{slug}/'
SEARCH_URL = 'search/'

PAGE_SAVE_AS = PAGE_URL + 'index.html'
ARTICLE_SAVE_AS = ARTICLE_URL + 'index.html'
CATEGORY_SAVE_AS = CATEGORY_URL + 'index.html'
TAG_SAVE_AS = TAG_URL + 'index.html'
SEARCH_SAVE_AS = SEARCH_URL + 'index.html'

DRAFT_SAVE_AS = ''
AUTHOR_SAVE_AS = ''
AUTHORS_SAVE_AS = ''
TAGS_SAVE_AS = ''
CATEGORIES_SAVE_AS = ''
ARCHIVES_SAVE_AS = ''
YEAR_ARCHIVE_SAVE_AS = ''
MONTH_ARCHIVE_SAVE_AS = ''
DAY_ARCHIVE_SAVE_AS = ''
ARTICLE_LANG_SAVE_AS = ''
DRAFT_LANG_SAVE_AS = ''
PAGE_LANG_SAVE_AS = ''

PATH = 'content'
THEME = 'theme'

STATIC_PATHS = [
    'CNAME',
    'images',
]


# Plugins.
PLUGIN_PATHS = [
    'plugins',
]

PLUGINS = [
    'redirects',
    'tipue_search',
    'ubuntuplanet',
]


# Templates.
JINJA_FILTERS = {
    'tojson': tojson_filter,
}

JINJA_EXTENSIONS = [
    'jinja2.ext.autoescape',
    'jinja2.ext.do',
]

DIRECT_TEMPLATES = [
    'categories',
    'index',
    'search',
    'tags',
]


# Pagination and summary.
DEFAULT_PAGINATION = 8

SUMMARY_MAX_LENGTH = 64


# Feeds.
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
UBUNTU_FEED_ATOM = None
UBUNTU_FEED_RSS = None
