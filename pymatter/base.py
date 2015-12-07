# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import json
import threading
from queue import Queue, Empty

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
        self.attachments = [] if not attachments else [Attachment.factory(a) for a in attachments]

    def to_dict(self):
        d = {}
        for attr in ['text', 'username', 'icon_url', 'channel']:
            if self.__getattribute__(attr):
                d[attr] = self.__getattribute__(attr)
        if self.attachments:
            d['attachments'] = [a.to_dict() for a in self.attachments]
        return d

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return u"IncomingMessage.loads('{}')".format(self.dumps())

    @classmethod
    def loads(cls, json_text):
        d = json.loads(json_text)
        return cls.factory(d)

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
        # noinspection PyTypeChecker
        return Poster(url).post(self)


class Attachment(object):
    def __init__(self, text=u'', fallback=u'', title=u'', color=None, pretext=u'', author_name=None, author_link=None,
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
        self.fields = [] if not fields else [Field.factory(f) for f in fields]

    @classmethod
    def factory(cls, d):
        if isinstance(d, Attachment):
            return d
        args = [d.get(attr) for attr in [
            'fallback', 'color', 'pretext', 'author_name', 'author_link', 'author_icon', 'title', 'title_link',
            'text', 'image_url', 'thumb_url', 'fields'
        ]]
        return cls(*args)

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return u"Attachment.loads('{}')".format(self.dumps())

    def to_dict(self):
        d = {}
        for attr in [
            'fallback', 'color', 'pretext', 'author_name', 'author_link', 'author_icon', 'title', 'title_link',
            'text', 'image_url', 'thumb_url'
        ]:
            if self.__getattribute__(attr):
                d[attr] = self.__getattribute__(attr)
        if self.fields:
            d['fields'] = [f.to_dict() for f in self.fields]
        return d

    def dumps(self):
        return json.dumps(self.to_dict())

    @classmethod
    def loads(cls, json_text):
        d = json.loads(json_text)
        return cls.factory(d)


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

    def __str__(self):
        return u"{}: {}".format(self.title, self.value)

    def __repr__(self):
        return u"Field('{}', '{}', {})".format(self.title, self.value, self.short)

    def to_dict(self):
        d = {}
        if self.title:
            d['title'] = self.title
        if self.value:
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
        return r

    def __repr__(self):
        return u"Poster('{}')".format(self.url)

    def __str__(self):
        return u"Poster('{}')".format(self.url)


class AsyncPoster(object):
    def __init__(self, incoming_webhook_url):
        self.url = incoming_webhook_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.thread = None
        self.queue = None
        self.answers_codes = None
        self.stopping = threading.Event()

    def __enter__(self):
        self.stopping.clear()
        self.queue = Queue()
        self.answers_codes = []
        self.thread = threading.Thread(target=self.posting_thread)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stopping.set()
        if self.thread is not None:
            self.thread.join()

    def posting_thread(self):
        while (not self.stopping.is_set()) or (not self.queue.empty()):
            try:
                msg = self.queue.get(True, 0.1)
            except Empty:
                pass
            else:
                try:
                    resp = self.session.post(self.url, json=msg.to_dict())
                except requests.RequestException as ex:
                    if ex.response:
                        self.answers_codes.append(ex.response.status_code)
                    else:
                        self.answers_codes.append(-1)
                else:
                    self.answers_codes.append(resp.status_code)

    def post(self, incoming_message):
        self.queue.put(IncomingMessage.factory(incoming_message))

    def __repr__(self):
        return u"AsyncPoster('{}')".format(self.url)

    def __str__(self):
        return u"AsyncPoster('{}')".format(self.url)


class Code(object):
    def __init__(self, code, language=u''):
        language = u'' if language is None else decode_text(language)
        self.language = language
        self.code = decode_text(code)

    def __str__(self):
        return u"\n``` {}\n{}```\n".format(self.language, self.code)

    def __add__(self, other):
        return str(self) + (u'' if other is None else decode_text(str(other)))

    def __radd__(self, other):
        return (u'' if other is None else decode_text(str(other))) + str(self)


class Emoji(object):
    def __init__(self, emoji_text):
        self.emoji_text = decode_text(emoji_text)

    def __str__(self):
        return u":" + self.emoji_text + u":"

    def __repr__(self):
        return u"Emoji('{}')".format(self.emoji_text)

    def __add__(self, other):
        return str(self) + (u'' if other is None else decode_text(str(other)))

    def __radd__(self, other):
        return (u'' if other is None else decode_text(str(other))) + str(self)
