# -*- coding: utf-8 -*-

import imghdr

from collections import namedtuple

from reppo.lib.highlight import highlight_blob


class Blob(namedtuple('Blob', 'data_ is_binary size path')):
    __slots__ = ()

    @property
    def is_image(self):
        return bool(imghdr.what('/dev/null', self.data_))

    @property
    def line_count(self):
        if self.is_binary:
            return None
        return len(self.data_.splitlines())

    @property
    def loc_count(self):
        # TODO: this is pretty bloody naive, but no useful lib exists to accurately calculate sloc
        if self.is_binary:
            return None
        return sum(1 for l in self.data_.splitlines() if len(l.strip()) > 0)

    @property
    def data(self):
        if self.is_binary:
            return None
        return highlight_blob(self.data_, self.path.rsplit('/', 1)[-1])


def get_blob(blob, path):
    return Blob(blob.data, blob.is_binary, blob.size, path)
