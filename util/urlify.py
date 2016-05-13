"""
URLify Extension for Python-Markdown
=====================================

Converts URLs in the markdown text to clickable links.
"""

import re
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension

urlfinder = re.compile(r'((([A-Za-z]{3,9}:(?:\/\/)?)(?:[\-;:&=\+\$,\w]+@)?[A-Za-z0-9\.\-]+(:[0-9]+)?|'
                       r'(?:www\.|[\-;:&=\+\$,\w]+@)[A-Za-z0-9\.\-]+)((?:/[\+~%/\.\w\-_]*)?\??'
                       r'(?:[\-\+=&;%@\.\w_]*)#?(?:[\.!/\\\w]*))?)')


class URLify(Preprocessor):
    def run(self, lines):
        return [urlfinder.sub(r'<\1>', line) for line in lines]


class URLifyExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('urlify', URLify(md), '_end')
