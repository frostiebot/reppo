# -*- coding: utf-8 -*-

from itertools import groupby

from yaml import safe_load

with open('/home/chris/hosted/reppo/reppo/lib/languages.yaml') as f:
    LANGUAGES = safe_load(f)


def _get_language_extensions():
    extensions = dict()
    for l, s in LANGUAGES.iteritems():
        for e in s.get('extensions'):
            extensions.setdefault(e.lstrip('.'), l)
    return extensions


def get_language_stats(repo, commit):
    # TODO: No need to use groupby if using language_extensions
    # TODO: When returning percentage, template needs a threshold percent to group items into 'Other' (max three items - ie. 'Python 50%, Javascript 45%, Other 5%')
    files = set()
    trees = [(commit.tree, '')]

    extensions = _get_language_extensions()

    def _extensions_grouper(f):
        e = ''
        _f = f.rsplit('/', 1)[-1].rsplit('.', 1)
        if len(_f) > 1 and _f[0]:
            e = _f[-1].lower()
        return extensions.get(e, '_discard')

    while trees:
        tree, path = trees.pop(0)

        for entry in tree:
            name = '/'.join(filter(None, (path, entry.name)))
            obj = repo.git[entry.id]

            if obj.type == TREE:
                trees.append((obj, name))
            elif obj.type == BLOB:
                files.add(name)

    langs_and_files = dict()
    files = sorted(files, key=_extensions_grouper)

    for key, group in groupby(files, _extensions_grouper):
        if key != '_discard':
            langs_and_files.setdefault(key, list(group))

    total = {k: len(langs_and_files.get(k)) for k in langs_and_files.iterkeys()}
    gtotal = sum(v for v in total.itervalues())

    for l, t in total.iteritems():
        pct = ((float(t) / float(gtotal)) * 100)
        print '{:<20} | {:.2f}%'.format(l, pct)

    return langs_and_files


# NOTE: If we want to revert back to grouping purely by extension
# def get_language_stats(repo, commit):
#     files = set()
#     trees = [(commit.tree, '')]

#     def _key_extension(f):
#         e = 'other'
#         _f = f.rsplit('/', 1)[-1].rsplit('.', 1)
#         if len(_f) > 1 and _f[0]:
#             e = _f[-1].lower()
#         return e

#     while trees:
#         tree, path = trees.pop(0)

#         for entry in tree:
#             name = '/'.join(filter(None, (path, entry.name)))
#             obj = repo.git[entry.id]

#             if obj.type == TREE:
#                 trees.append((obj, name))
#             elif obj.type == BLOB:
#                 files.add(name)

#     langs_and_files = dict()
#     files = sorted(files, key=_key_extension)

#     for key, group in groupby(files, _key_extension):
#         langs_and_files.setdefault(key, list(group))

#     repo.files = langs_and_files
