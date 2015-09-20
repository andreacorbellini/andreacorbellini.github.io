from pelican import signals


def write_ubuntu_feeds(generator, writer):
    articles = []

    for article in generator.articles:
        if not article.metadata.get('skip-ubuntu-planet'):
            articles.append(article)

    if generator.settings.get('FEED_UBUNTU_ATOM'):
        writer.write_feed(
            articles, generator.context,
            generator.settings['FEED_UBUNTU_ATOM'])

    if generator.settings.get('FEED_UBUNTU_RSS'):
        writer.write_feed(
            articles, generator.context,
            generator.settings['FEED_UBUNTU_RSS'], feed_type='rss')


def register():
    signals.article_writer_finalized.connect(write_ubuntu_feeds)
