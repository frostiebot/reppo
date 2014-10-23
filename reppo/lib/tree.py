# -*- coding: utf-8 -*-

from collections import namedtuple

from pygit2 import GIT_OBJ_TREE as TREE
from pygit2 import GIT_OBJ_BLOB as BLOB

from pygit2 import GIT_FILEMODE_LINK as SYMLINK

# from pygit2 import GIT_FILEMODE_BLOB as BLOB
# from pygit2 import GIT_FILEMODE_BLOB_EXECUTABLE as BLOB_EXECUTABLE
# from pygit2 import GIT_FILEMODE_COMMIT as COMMIT
# from pygit2 import GIT_FILEMODE_NEW as NEW
# from pygit2 import GIT_FILEMODE_TREE as TREE


# class TreeEntry(namedtuple('TreeEntry', 'sha filemode type_ target_ path commit')):
class TreeEntry(namedtuple('TreeEntry', 'sha filemode type_ target_ path')):
    __slots__ = ()

    @property
    def name(self):
        return self.path.rsplit('/', 1)[-1]

    @property
    def type(self):
        return {
            TREE: 'tree',
            BLOB: 'blob'
        }.get(self.type_, None)

    @property
    def is_symlink(self):
        return self.filemode == SYMLINK

    @property
    def target(self):
        if self.is_symlink:
            return self.target_
        return self.path


def get_tree_entry(repo, commit, entry, path):
    # TODO: if type is SYMLINK, we have to abspath (relatively, sigh) the target_ (ex. '../web_tabletcrs/crs', '/usr/tablet/web_tablethotels/pw')
    # TODO: last commit that touched this entry
    path = '/'.join(filter(None, [path, entry.name]))

    obj = repo.git[entry.id]

    target_ = None
    type_ = obj.type

    if entry.filemode == SYMLINK:
        target_ = obj.data
        # type_ = repo.git[commit.tree[target_].id].type

    # latest_commit = repo.commit(commit, path)
    return TreeEntry(
        entry.hex,
        entry.filemode,
        type_,
        target_,
        path
        # latest_commit
    )
