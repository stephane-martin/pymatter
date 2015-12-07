# -*- coding: utf-8 -*-

"""
Read stdin, send content to mattermost and write to stdout
"""

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import argparse
import platform
import sys
import getpass
import os
import datetime

import requests

from .base import IncomingMessage, AsyncPoster, Code, Attachment, Field, decode_text


def main():
    hostname = platform.uname()[1]
    local_username = getpass.getuser()

    parser = argparse.ArgumentParser(
        description="pymattertee copies standard input to standard output, making a copy to a mattermost instance"
    )
    parser.add_argument("-c", "--channel", help="Post input values to the specified channel")
    parser.add_argument("-i", "--iconurl", help="Icon URL")
    parser.add_argument("-l", "--language", help="Language for syntax highlighting")
    parser.add_argument("-m", "--mattermosturl", help="Post the message to the specified webhook URL")
    parser.add_argument("-n", "--nobuffer", action='store_true',
                        help="Post each line of stdin as a distinct message, no buffering")
    parser.add_argument("-p", "--plain", action='store_true', help="Don't surround the message with triple ticks")
    parser.add_argument("-u", "--username", default="pymattertee", help="Displayed username")
    args = parser.parse_args()

    channel = decode_text(args.channel if args.channel else os.environ.get("MM_CHANNEL"))
    icon_url = decode_text(args.iconurl if args.iconurl else os.environ.get("MM_ICONURL"))
    language = decode_text(args.language)
    url = decode_text(args.mattermosturl if args.mattermosturl else os.environ.get("MM_HOOK"))
    no_buffer = args.nobuffer
    plain = args.plain
    username = decode_text(args.username if args.username else os.environ.get("MM_USERNAME"))

    if not url:
        sys.stderr.write(b"No Mattermost URL was provided\n")
        sys.exit(-1)

    if no_buffer:
        poster = AsyncPoster(url)
        with poster:
            for line in sys.stdin:
                text = Code(line)
                sys.stdout.write(line)
                msg = IncomingMessage(username=username, icon_url=icon_url, channel=channel, text=text)
                poster.post(msg)
        if all([code == 200 for code in poster.answers_codes]):
            sys.stderr.write(b"Mattermost server answered OK\n")
        else:
            sys.stderr.write(b"One or more requests failed: {}\n".format(b" ".join([str(code) for code in poster.answers_codes])))
            sys.exit(-1)

    else:
        buf = sys.stdin.read()
        sys.stdout.write(buf)
        now = datetime.datetime.utcnow().strftime('%c')
        text = u"**{} on `{}` wrote:**\n".format(local_username, hostname)
        msg = IncomingMessage(username=username, icon_url=icon_url, channel=channel, text=text)
        att = Attachment(fallback='tee content', text=buf if plain else Code(buf, language))
        att.fields.append(Field('Date', now, True))
        att.fields.append(Field('Local user', local_username, True))
        att.fields.append(Field('Hostname', hostname, True))
        msg.attachments.append(att)

        try:
            resp = msg.post(url)
        except requests.RequestException as ex:
            sys.stderr.write(str(ex) + '\n')
            sys.exit(-1)
        else:
            sys.stderr.write(b"Mattermost server answered OK\n")

if __name__ == '__main__':
    main()
