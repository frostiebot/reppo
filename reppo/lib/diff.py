# -*- coding: utf-8 -*-

from cgi import escape

from collections import namedtuple

from difflib import SequenceMatcher

from flask import Markup


class Patch(namedtuple('Patch', 'additions deletions hunks is_binary new_file_path new_id old_file_path old_id similarity current_status')):
    __slots__ = ()

    @property
    def file_path(self):
        return self.new_file_path

    @property
    def status(self):
        return {u'A': u'added', u'C': u'copied', u'D': u'deleted', u'M': u'modified', u'R': u'renamed', u'T': u'changed', u'U': u'unmerged', u'X': u'unknown', u'B': u'broken'}


class Hunk(namedtuple('Hunk', 'old_start old_lines new_start new_lines lines')):
    __slots__ = ()

    @property
    def context_line(self):
        return u'@@ -{},{} +{},{} @@'.format(
            self.old_start,
            self.old_lines,
            self.new_start,
            self.new_lines
        )


class HunkLine(namedtuple('HunkLine', 'op old_lineno new_lineno raw_line')):
    __slots__ = ()

    @property
    def action(self):
        return {u' ': u'context', u'+': u'addition', u'-': u'deletion'}.get(self.op)

    @property
    def line(self):
        return Markup(u' '.join((self.op, self.raw_line.rstrip(u'\n'))))


def process_diff(diff):
    return list(_process_patch(patch) for patch in diff)


def _process_patch(patch):
    hunks = []
    for hunk in patch.hunks:
        hunks.append(_process_hunk(hunk))
    return Patch(patch.additions, patch.deletions, hunks, patch.is_binary, patch.new_file_path, patch.new_id, patch.old_file_path, patch.old_id, patch.similarity, patch.status)


def _process_hunk(hunk):
    lines = []
    ol, nl = hunk.old_start, hunk.new_start

    for op, line in _process_hunk_lines(hunk):
        ''' return HunkLine(op, old_line_num, new_line_num, line) '''
        _ol, _nl = None, None

        if op == ' ':
            _ol, _nl = ol, nl
            ol += 1
            nl += 1

        if op == '-':
            _ol, _nl = ol, None
            ol += 1

        if op == '+':
            _ol, _nl = None, nl
            nl += 1

        lines.append(HunkLine(op, _ol, _nl, line))

    return Hunk(hunk.old_start, hunk.old_lines, hunk.new_start, hunk.new_lines, lines)


def _process_hunk_lines(hunk):
    lines = hunk.lines[:]
    lines.reverse()

    while lines:
        op, line = lines.pop()

        if op == u'-':
            if lines:
                _next = []

                while lines and len(_next) < 2:
                    _next.append(lines.pop())

                if _next[0][0] == u'+' and (len(_next) == 1 or _next[1][0] not in (u'+', u'-')):
                    _nop, _nline = _next.pop(0)
                    aline, bline = _markup_line_diff(line, _nline)

                    yield op, aline
                    yield _nop, bline

                    if _next:
                        lines.append(_next.pop())

                    continue

                lines.extend(reversed(_next))
        # elif op == u'+':
        #     yield op, line
        yield op, escape(line)


def _markup_line_diff(a, b):
    # TODO: make highlighting smarter - cover contiguous words rather than break
    alines = []
    blines = []

    markup = u'<span class="x">{}</span>'
    empty = markup.format(u'')

    for op, alo, ahi, blo, bhi in SequenceMatcher(None, a=a, b=b).get_opcodes():
        aline = a[alo:ahi]
        bline = b[blo:bhi]

        if op == 'equal':
            alines.append(escape(aline))
            blines.append(escape(bline))
            continue

        aline = markup.format(escape(aline))
        bline = markup.format(escape(bline))

        alines.append(aline)
        blines.append(bline)

    return u''.join(alines).replace(empty, u''), u''.join(blines).replace(empty, u'')
