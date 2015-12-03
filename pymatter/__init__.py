# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import json

import requests
from builtins import str as t
from builtins import bytes as b


def decode_text(text):
    if text is None:
        return None
    if isinstance(text, Code) or isinstance(text, Emoji):
        text = str(text)
    if not isinstance(text, t) and not isinstance(text, b):
        text = str(text)
    if not isinstance(text, t):
        text = text.decode('utf-8')
    return text


class IncomingMessage(object):
    def __init__(self, text=u'', username=u'pymatter', icon_url=None, channel=None, attachments=None):
        self.text = decode_text(text)
        self.username = decode_text(username)
        self.icon_url = decode_text(icon_url)
        self.channel = decode_text(channel)
        self.attachments = None if attachments is None else [Attachment.factory(a) for a in attachments]

    def to_dict(self):
        d = {}
        for attr in ['text', 'username', 'icon_url', 'channel']:
            if self.__getattribute__(attr) is not None:
                d[attr] = self.__getattribute__(attr)
        if self.attachments is not None:
            d['attachments'] = [a.to_dict() for a in self.attachments]
        return d

    def dumps(self):
        return json.dumps(self.to_dict())

    @classmethod
    def factory(cls, msg):
        if isinstance(msg, IncomingMessage):
            return msg
        return cls(
            msg.get('text'), msg.get('username'), msg.get('icon_url'), msg.get('channel'), msg.get('attachments')
        )

    def post(self, url):
        Poster(url).post(self)


class Attachment(object):
    def __init__(self, text, fallback, title=u'', color=None, pretext=None, author_name=None, author_link=None,
                 author_icon=None, title_link=None, image_url=None, thumb_url=None, fields=None):
        self.fallback = decode_text(fallback)
        self.title = decode_text(title)
        self.text = decode_text(text)
        self.color = decode_text(color)
        self.pretext = decode_text(pretext)
        self.author_name = decode_text(author_name)
        self.author_link = decode_text(author_link)
        self.author_icon = decode_text(author_icon)
        self.title_link = decode_text(title_link)
        self.image_url = decode_text(image_url)
        self.thumb_url = decode_text(thumb_url)
        self.fields = None if fields is None else [Field.factory(f) for f in fields]

    @classmethod
    def factory(cls, d):
        if isinstance(d, Attachment):
            return d
        return cls(
            d.get('fallback'),
            d.get('color'),
            d.get('pretext'),
            d.get('author_name'),
            d.get('author_link'),
            d.get('author_icon'),
            d.get('title'),
            d.get('title_link'),
            d.get('text'),
            d.get('image_url'),
            d.get('thumb_url'),
            d.get('fields')
        )

    def to_dict(self):
        d = {}
        for attr in [
            'fallback', 'color', 'pretext', 'author_name', 'author_link', 'author_icon', 'title', 'title_link',
            'text', 'image_url', 'thumb_url'
        ]:
            if self.__getattribute__(attr) is not None:
                d[attr] = self.__getattribute__(attr)
        if self.fields is not None:
            d['fields'] = [f.to_dict() for f in self.fields]
        return d

    def dumps(self):
        return json.dumps(self.to_dict())



class Field(object):
    def __init__(self, title, value, short=False):
        self.title = decode_text(title)
        self.value = decode_text(value)
        self.short = bool(short)

    @classmethod
    def factory(cls, f):
        if isinstance(f, Field):
            return f
        return cls(
            f.get('title'),
            f.get('value'),
            f.get('short', False)
        )

    def to_dict(self):
        d = {}
        if self.title is not None:
            d['title'] = self.title
        if self.value is not None:
            d['value'] = self.value
        d['short'] = self.short
        return d

    def dumps(self):
        return json.dumps(self.to_dict())


class Poster(object):
    def __init__(self, incoming_webhook_url):
        self.url = incoming_webhook_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def post(self, incoming_message):
        incoming_message = IncomingMessage.factory(incoming_message)
        r = self.session.post(self.url, json=incoming_message.to_dict())
        if r.status_code != requests.codes.ok:
            r.raise_for_status()


class Code(object):
    def __init__(self, code, language=u''):
        self.language = decode_text(language)
        self.code = decode_text(code)

    def __str__(self):
        return u"\n``` " + self.language + u"\n" + self.code + u"```\n"

    def __add__(self, other):
        return str(self) + (u'' if other is None else decode_text(str(other)))

    def __radd__(self, other):
        return (u'' if other is None else decode_text(str(other))) + str(self)


class Emoji(object):
    def __init__(self, emoji_text):
        self.emoji_text = decode_text(emoji_text)

    def __str__(self):
        return u":" + self.emoji_text + u":"

    def __add__(self, other):
        return str(self) + (u'' if other is None else decode_text(str(other)))

    def __radd__(self, other):
        return (u'' if other is None else decode_text(str(other))) + str(self)
