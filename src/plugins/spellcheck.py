import logging
import os
import re
import shlex
import subprocess
from pelican import signals


logger = logging.getLogger(__name__)


class SpellChecker:

    def __init__(self, words_file=None):
        if words_file is None:
            words_file = '/dev/null'
        self.words_file = os.path.abspath(words_file)
        self.misspelled_words = set()

    def check(self, path, content, **kwargs):
        content = self._filter_content(content)
        proc = self._run_aspell(content, **kwargs)
        self._process_aspell_output(path, proc)

    def _filter_content(self, content):
        strip = [
            r'\$\$[^\$]*\$\$',          # block math
            r'\$[^\$]*\$',              # inline math
            r'<pre>.*?</pre>',           # code blocks
            r'<code>.*?</code>',         # inline code
            r'\b(0x)?[0-9a-f]{6,}\b',   # hex numbers (lowercase)
            r'\b(0x)?[0-9A-F]{6,}\b',   # hex numbers (uppercase)
        ]
        for pattern in strip:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        return content

    def _run_aspell(self, content, mode='none'):
        args = [
            'aspell',
            'list',
            '--mode=' + mode,
            '--personal=' + self.words_file,
        ]
        logger.debug('Running: %s', ' '.join(shlex.quote(arg) for arg in args))
        return subprocess.run(
            args,
            input=content,
            capture_output=True,
            text=True,
        )

    def _process_aspell_output(self, path, proc):
        for line in proc.stderr.split('\n'):
            if line:
                logger.error('aspell: %s', line)
        for word in proc.stdout.split('\n'):
            if not word or word in self.misspelled_words:
                continue
            self.misspelled_words.add(word)
            logger.warn('%s: misspelled word: %s', path, word)


def spellcheck(generators):
    articles_generator, pages_generator, static_generator = generators
    spellchecker = SpellChecker(articles_generator.settings.get('SPELL_CHECKER_WORDS'))
    all_content = articles_generator.articles + pages_generator.pages

    for item in all_content:
        logger.info('Spell checking %s', item.source_path)
        spellchecker.check(item.source_path, item.title)
        spellchecker.check(item.source_path, item.summary, mode='html')
        spellchecker.check(item.source_path, item.content, mode='html')

def register():
    signals.all_generators_finalized.connect(spellcheck)
