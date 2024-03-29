# -*- coding: utf-8 -*-

from math import ceil


class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, le=2, lc=2, rc=5, re=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= le or (num > self.page - lc - 1 and num < self.page + rc) or num > self.pages - re:
                if last + 1 != num:
                    yield None
                yield num
                last = num
