import os
import socket
import sys
from datetime import date


PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

def get_ip_address():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.connect(('1.1.1.1', 80))
        return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        sock.close()


def get_venv_path():
    if os.environ.get('VIRTUAL_ENV'):
        return os.environ['VIRTUAL_ENV']
    if sys.executable:
        # Inside a virtual env, sys.executable should be something
        # like '<venv_path>/bin/python' and is guaranteed to be an
        # absolute path.
        return os.path.dirname(os.path.dirname(sys.executable))
    raise RuntimeError('VIRTUAL_ENV is unset and sys.executable is empty')


# General.
AUTHOR = 'Andrea Corbellini'
SITENAME = 'Andrea Corbellini'
SITEURL = 'http://{}:8000'.format(get_ip_address())
RELATIVE_URLS = False

TIMEZONE = 'UTC'
DEFAULT_LANG = 'en'

OUTPUT_PATH = '/tmp/blog-output'


# URLs and paths.
PAGE_URL = '{slug}/'
ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
CATEGORY_URL = 'category/{slug}/'
TAG_URL = 'tag/{slug}/'

PAGE_SAVE_AS = PAGE_URL + 'index.html'
ARTICLE_SAVE_AS = ARTICLE_URL + 'index.html'
CATEGORY_SAVE_AS = CATEGORY_URL + 'index.html'
TAG_SAVE_AS = TAG_URL + 'index.html'

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

PATH = os.path.join(PROJECT_PATH, 'content')
THEME = os.path.join(PROJECT_PATH, 'theme')

STATIC_PATHS = [
    os.path.join(PATH, 'images'),
]


# Plugins.
PLUGIN_PATHS = [
    os.path.join(PROJECT_PATH, 'plugins'),
]

PLUGINS = [
    'pelican.plugins.webassets',
    'redirects',
    'spellcheck',
    'ubuntuplanet',
    'uniquotes',
]

MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {
            'css_class': 'highlight',
            'guess_lang': False,
        },
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
        'markdown.extensions.toc': {},
    },
}


# Templates.
JINJA_FILTERS = {
}

JINJA_ENVIRONMENT = {
}

DIRECT_TEMPLATES = [
    'categories',
    'index',
    'tags',
]


# Static files.
MINIFY_CSS = False
MINIFY_JS = False


# Pagination and summary.
DEFAULT_PAGINATION = 32

SUMMARY_MAX_LENGTH = 64

PAGINATION_PATTERNS = (
    (1, '{base_name}/', '{base_name}/index.html'),
    (2, '{base_name}/page/{number}/', '{base_name}/page/{number}/index.html'),
)


# Feeds.
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
UBUNTU_FEED_ATOM = None
UBUNTU_FEED_RSS = None


# Spell checking
SPELL_CHECKER_WORDS = os.path.join(PROJECT_PATH, 'words.txt')


# Variables used in template
YEAR = date.today().year
