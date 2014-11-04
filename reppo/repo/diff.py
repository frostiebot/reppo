# -*- coding: utf-8 -*-

from cgi import escape

from collections import namedtuple

from difflib import SequenceMatcher

from flask import Markup


class Diff(object):
    # TODO: I don't think I really need this. (wish I could recall what I meant)
    def __init__(self, diff):
        self._raw_patches = [patch for patch in diff]
        self._diff_stats_gen = _diff_stat([
            (patch.status, patch.additions, patch.deletions)
            for patch in self._raw_patches
        ])

        patches = []

        for patch in self._raw_patches:
            diffstat = self._diff_stats_gen.next()
            patches.append(_process_patch(patch, diffstat))

        self.patches = patches

    def __len__(self):
        return len(self._raw_patches)

    def __iter__(self):
        for patch in self.patches:
            yield patch


class Patch(namedtuple('Patch', 'additions deletions diffstat hunks is_binary new_file_path new_id old_file_path old_id similarity status_')):
    __slots__ = ()

    @property
    def file_path(self):
        if self.status_ == u'D':
            return self.old_file_path
        return self.new_file_path

    @property
    def total_changes(self):
        return self.additions + self.deletions

    @property
    def was_renamed(self):
        return self.status_ == u'R'

    @property
    def status(self):
        return {
            u'A': u'added',
            u'C': u'copied',
            u'D': u'deleted',
            u'M': u'modified',
            u'R': u'renamed',
            u'T': u'changed',
            u'U': u'unmerged',
            u'X': u'unknown',
            u'B': u'broken'
        }.get(self.status_)


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


class HunkLine(namedtuple('HunkLine', 'action_ old_lineno new_lineno raw_line')):
    __slots__ = ()

    @property
    def action(self):
        return {
            u' ': u'context',
            u'+': u'addition',
            u'-': u'deletion'
        }.get(self.action_)

    @property
    def line(self):
        return Markup(u' '.join((self.action_, self.raw_line.rstrip(u'\n'))))


def get_diff(diff):
    return Diff(diff)


def _process_patch(patch, diffstat=None):
    hunks = []
    for hunk in patch.hunks:
        hunks.append(_process_hunk(hunk))
    return Patch(
        patch.additions,
        patch.deletions,
        diffstat,
        hunks,
        patch.is_binary,
        patch.new_file_path,
        patch.new_id,
        patch.old_file_path,
        patch.old_id,
        patch.similarity,
        patch.status
    )


def _process_hunk(hunk):
    # TODO: Make this less naive/verbose
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

    return Hunk(
        hunk.old_start,
        hunk.old_lines,
        hunk.new_start,
        hunk.new_lines,
        lines
    )


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

        yield op, escape(line)


def _markup_line_diff(a, b):
    # TODO: make highlighting smarter - cover contiguous words rather than break
    markup = u'<span class="x">{}</span>'
    alines, blines = [], []

    for op, alo, ahi, blo, bhi in SequenceMatcher(None, a=a, b=b).get_opcodes():
        for xlines, x, xlo, xhi in ((alines, a, alo, ahi), (blines, b, blo, bhi)):
            xline = escape(x[xlo:xhi])
            if op != 'equal':
                xline = markup.format(xline)
            xlines.append(xline)

    return tuple(
        u''.join(xlines).replace(
            markup.format(u''), u''
        )
        for xlines in (alines, blines)
    )


def _diff_stat(stats, graph_width=5):
    ''' grokked wtf git is doing by looking over
        https://github.com/git/git/blob/master/diff.c

        # >>> stats = [(23, 37), (19, 25), (4, 4), (0, 55)]
        # >>> from reppo.lib import diff
        # >>> diff._diff_stat(stats)
        # <generator object _diff_stat at 0x8094b6f50>
        # >>> for ds in diff._diff_stat(stats):
        #         print ds
        #
        # ++---
        # ++-
        # +-
        # ----
        #

        However, this differs from github a little, where they appear to
        check if additions or deletions is zero, and if so, then the
        resulting diffstat pips are *all* the opposite type.

        eg.

        +0 -23 ==> '-----'
        +22 -0 ==> '+++++' (instead of '++++_')

        The only oddity I could find was a situation of 8 additions and
        1 removal resulting in '++++_'. Not sure how they came up with that.
    '''
    # TODO: Make Patch.diffstat into Patch.raw_diffstat and add a @property to emit the desired result
    def _diff_stat_sum(stats):
        max_total, total_adds, total_deletions = 0, 0, 0

        for _, adds, deletions in stats:
            max_total = max(max_total, adds + deletions)
            total_adds += adds
            total_deletions += deletions

        return max_total, total_adds, total_deletions

    def scale_linear(i):
        if not i:
            return 0
        return 1 + (i * (graph_width - 1) // max_total)

    max_total, total_adds, total_deletions = _diff_stat_sum(stats)

    for status, adds, deletions in stats:
        a, d = adds, deletions

        if graph_width <= max_total:
            total = scale_linear(adds + deletions)

            if total < 2 and adds and deletions:
                total = 2

            if adds < deletions:
                a = scale_linear(adds)
                d = total - a
            else:
                d = scale_linear(deletions)
                a = total - d

        if status == u'A':
            a, d = graph_width, 0
        elif status == u'D':
            a, d = 0, graph_width

        # yield '{}{}'.format('+' * a, '-' * d)
        yield list(
            i for s in
            (
                ['plus'] * a,
                ['minus'] * d,
                [''] * (graph_width - (a + d))
            )
            for i in s
        )
