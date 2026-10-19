import os
import sys

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_PATH)

from pelicanconf import *


# General.
SITEURL = 'https://andrea.corbellini.blog'
OUTPUT_PATH = os.path.dirname(PROJECT_PATH)


# Static files.
MINIFY_CSS = True
MINIFY_JS = True


# Comments.
REMARK42_URL = 'https://comments.andrea.corbellini.blog'
REMARK42_SITE_ID = 'andrea.corbellini.blog'


# Stats.
GOATCOUNTER_URL = 'https://cor.goatcounter.com/count'


# Feeds.
FEED_ATOM = 'feed.atom'
FEED_RSS = 'feed.rss'
FEED_UBUNTU_RSS = 'ubuntu.rss'
RSS_FEED_SUMMARY_ONLY = False
