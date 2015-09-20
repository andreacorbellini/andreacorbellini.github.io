import os
import sys

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_PATH)

from pelicanconf import *


# General.
SITEURL = 'http://andrea.corbellini.name'
OUTPUT_PATH = os.path.dirname(PROJECT_PATH)


# Static files.
MINIFY_CSS = True


# Comments.
DISQUS_SITENAME = 'andreacorbellini'


# Analytics.
GOOGLE_ANALYTICS = 'UA-59812311-1'


# Feeds.
FEED_ATOM = 'feed.atom'
FEED_RSS = 'feed.rss'
FEED_UBUNTU_RSS = 'ubuntu.rss'
