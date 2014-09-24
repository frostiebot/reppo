# -*- coding: utf-8 -*-

import os

from flask import redirect
from flask import request
from flask import safe_join
from flask import send_from_directory
from flask import url_for


def reppo_avatar(name):
    from retricon import retricon

    return retricon(
        name.strip(),
        bg_color='f0f0f0',
        image_padding=38,
        tiles=10,
        tile_size=50,
        width=576
    )


def init_avatars(app):
    AVATAR_CACHE = app.config['AVATAR_CACHE']

    if not os.path.isdir(AVATAR_CACHE):
        os.mkdir(AVATAR_CACHE, 0755)

    def _normalize(s):
        return s.replace(u' ', u'').lower()

    def avatar(name):
        normal_name = _normalize(name)
        avatar_file = safe_join(AVATAR_CACHE, normal_name)

        if not avatar_file.endswith('.png'):
            avatar_file = u'.'.join((avatar_file, 'png'))

        if not os.path.exists(avatar_file):
            reppo_avatar(name).save(avatar_file, quality=100)

        if name != normal_name:
            return redirect(
                url_for(request.endpoint, name=normal_name), 301
            )

        return send_from_directory(*avatar_file.rsplit('/', 1))

    app.add_url_rule('/avatar/<name>.png', 'avatar', avatar)
