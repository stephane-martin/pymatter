# -*- coding: utf-8 -*-

"""
Send content of files to mattermost
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
from os.path import exists, basename

from . import IncomingMessage, Poster, Code, Attachment, Field, decode_text

ext_to_language = {
    'md': 'markdown',
    'js': 'javascript',
    'css': 'css',
    'py': 'python',
    'pl': 'perl',
    'sh': 'bash',
    'php': 'php',
    'cpp': 'cpp',
    'c': 'cpp',
    'h': 'cpp',
    'sql': 'sql',
    'go': 'go',
    'rb': 'ruby',
    'java': 'java',
    'ini': 'ini'
}

def main():
    hostname = platform.uname()[1]
    local_username = getpass.getuser()

    parser = argparse.ArgumentParser(
        description="concatenate and print files to a mattermost instance"
    )
    parser.add_argument("-c", "--channel", help="Post input values to the specified channel")
    parser.add_argument("-i", "--iconurl", help="Icon URL")
    parser.add_argument("-l", "--language", default="detect", help="Language for syntax highlighting")
    parser.add_argument("-m", "--mattermosturl", help="Post the message to the specified webhook URL")
    parser.add_argument("-p", "--plain", action='store_true', help="Don't surround the message with triple ticks")
    parser.add_argument("-u", "--username", default="pymattertee", help="Displayed username")
    parser.add_argument("files", nargs="+", help="Files to print")
    args = parser.parse_args()

    channel = decode_text(args.channel if args.channel else os.environ.get("MM_CHANNEL"))
    icon_url = decode_text(args.iconurl if args.iconurl else os.environ.get("MM_ICONURL"))
    language = decode_text(args.language)
    url = decode_text(args.mattermosturl if args.mattermosturl else os.environ.get("MM_HOOK"))
    plain = args.plain
    username = decode_text(args.username if args.username else os.environ.get("MM_USERNAME"))

    if not url:
        sys.stderr.write(b"No Mattermost URL was provided\n")
        sys.exit(-1)

    for f in args.files:
        if not exists(f):
            sys.stderr.write(b"'{}' does not exist\n".format(f))
            sys.exit(-1)

    poster = Poster(url)
    now = datetime.datetime.utcnow().strftime('%c')
    text = u"**{} on `{}` wrote:**\n".format(local_username, hostname)
    msg = IncomingMessage(username=username, icon_url=icon_url, channel=channel, text=text)

    for f in args.files:
        with open(f) as handle:
            buf = handle.read()
        base = basename(f)
        if language == "detect":
            try:
                ext = decode_text(base.rsplit('.', 1)[1])
                language = ext_to_language[ext]
            except (IndexError, KeyError):
                pass
        att = Attachment(fallback=base, text=buf if plain else Code(buf, language), title=base)
        att.fields.append(Field('Date', now, True))
        att.fields.append(Field('Local user', local_username, True))
        att.fields.append(Field('Hostname', hostname, True))
        att.fields.append(Field('File name', base, True))
        msg.attachments.append(att)

    poster.post(msg)

if __name__ == '__main__':
    main()
