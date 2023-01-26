import re
from bs4 import BeautifulSoup
from pelican import signals


exclude_tags = ['code', 'pre']


def should_skip(element):
    for tag in exclude_tags:
        if element.name == tag or element.find_parent(tag) is not None:
            return True
    return False


def replace_quotes(s):
    return ''.join(replace_quotes_iter(s))


def replace_quotes_iter(s):
    s = iter(s)
    state = 'blank'
    open_quote = None
    for c in s:
        if c == open_quote:
            if c == '"':
                yield '\u201d'
            elif c == "'":
                yield '\u2019'
            else:
                raise RuntimeError(c)
            open_quote = None
        elif c == '"' and state == 'blank':
            yield '\u201c'
            open_quote = c
        elif c == "'" and state == 'blank':
            yield '\u2018'
            open_quote = c
        elif c == '"' and state == 'word':
            yield '\u201d'
            open_quote = c
        elif c == "'" and state == 'word':
            yield '\u2019'
        else:
            yield c
        if c.isalnum():
            state = 'word'
        else:
            state = 'blank'


def rewrite_quotes(content):
    if content._content is None:
        return

    soup = BeautifulSoup(content._content, features='html.parser')
    for quoted_string in soup.find_all(string=re.compile('["\']')):
        if should_skip(quoted_string):
            continue
        replaced_string = replace_quotes(quoted_string.text)
        quoted_string.replace_with(replaced_string)
    content._content = str(soup)


def register():
    signals.content_object_init.connect(rewrite_quotes)
