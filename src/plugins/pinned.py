from pelican import signals


def collect_pinned(generator):
    pinned_articles = generator.context.setdefault('pinned_articles', [])
    for article in generator.articles:
        if 'pin' in article.metadata:
            pinned_articles.append(article)
    pinned_articles.sort(key=lambda article: int(article.metadata['pin']))


def register():
    signals.article_generator_finalized.connect(collect_pinned)
