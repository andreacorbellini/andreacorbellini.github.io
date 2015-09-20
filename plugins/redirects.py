import logging
from pelican import signals


logger = logging.getLogger(__name__)


REDIRECT_TEMPLATE = """<!doctype html>
<html>
  <head>
    <title>{{ title|e }}</title>
    <link ref="canonical" href="{{ SITEURL|e }}/{{ redirect_url|e }}">
    <meta http-equiv="refresh" \
content="0;url='{{ SITEURL|e }}/{{ redirect_url|e }}'">
    <meta name="robots" content="noindex">
  </head>
  <body>
    <p>This page has moved to \
<a href="{{ SITEURL|e }}/{{ redirect_url|e }}">\
{{ SITEURL|e }}/{{ redirect_url|e }}</a></p>
    <script>window.url = '{{ SITEURL|e }}/{{ redirect_url|e }}';</script>
  </body>
</html>"""


def iter_content_redirects(contents):
    for content in contents:
        alias = content.metadata.get('alias')
        if not alias:
            continue

        alias_url_format = content.url_format.copy()
        alias_url_format['slug'] = alias

        setting_key = content.__class__.__name__.upper() + '_SAVE_AS'
        save_as = content.settings[setting_key].format_map(alias_url_format)

        yield save_as, content.url, content.title


def write_redirects(generator, writer, redirects):
    template = generator.env.from_string(REDIRECT_TEMPLATE)

    for save_as, redirect_url, title in redirects:
        logger.info('Redirect %s => %s', save_as, redirect_url)
        writer.write_file(
            save_as, template, generator.context,
            redirect_url=redirect_url, title=title)


def write_article_redirects(generator, writer):
    redirects = iter_content_redirects(generator.articles)
    write_redirects(generator, writer, redirects)


def write_page_redirects(generator, writer):
    redirects = iter_content_redirects(generator.pages)
    write_redirects(generator, writer, redirects)


def write_custom_redirects(generator, writer):
    redirects = generator.settings.get('REDIRECTS')
    if redirects:
        write_redirects(generator, writer, redirects)


def register():
    signals.article_writer_finalized.connect(write_article_redirects)
    signals.article_writer_finalized.connect(write_custom_redirects)
    signals.page_writer_finalized.connect(write_page_redirects)
