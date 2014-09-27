# -*- coding: utf-8 -*-

from pygments import highlight

from pygments.lexers import guess_lexer
from pygments.lexers import get_lexer_for_filename

from pygments.lexers import TextLexer
from pygments.lexers import ClassNotFound

from pygments.formatters import HtmlFormatter

from flask import Markup


BLOB_CODE_TABLE_BODY_START = '''\
<table class="highlight diff-table">
    <tbody>
'''

BLOB_CODE_TABLE_BODY_END = '''\
    </tbody>
</table>
'''

BLOB_CODE_LINE = '''\
        <tr>
            <td class="blob-num blob-num-context" data-line-number="%d"></td>
            <td class="blob-code blob-code-context">%s</td>
        </tr>
'''


class BlobFormatter(HtmlFormatter):
    # def __init__(self):
    #     super(BlobFormatter, self).__init__(
    #         linenos=False
    #     )

    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def _wrap_code(self, inner):
        yield 0, BLOB_CODE_TABLE_BODY_START
        i = 0
        for t, value in inner:
            i += 1
            value = BLOB_CODE_LINE % (i, value)
            yield t, value
        yield 0, BLOB_CODE_TABLE_BODY_END

    # def _format_lines(self, tokensource):
    #     for ttype, value in super(BlobFormatter, self)._format_lines(tokensource):
    #         if ttype == 1:
    #             value = '<td class="blob-code">%s</td>' % value
    #         yield ttype, value


def pygmentize(data, filename=None):
    try:
        lexer = get_lexer_for_filename(filename, data)
    except ClassNotFound:
        try:
            lexer = guess_lexer(data)
        except ClassNotFound:
            lexer = TextLexer()

    return Markup(highlight(data, lexer, BlobFormatter()))
