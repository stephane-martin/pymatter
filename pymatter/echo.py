# -*- coding: utf-8 -*-

"""
Write arguments to mattermost
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

from . import IncomingMessage, Attachment, Field, decode_text


def main():
    hostname = platform.uname()[1]
    local_username = getpass.getuser()

    parser = argparse.ArgumentParser(
        description="Write arguments to a mattermost instance"
    )
    parser.add_argument("-c", "--channel", help="Post input values to the specified channel")
    parser.add_argument("-i", "--iconurl", help="Icon URL")
    parser.add_argument("-m", "--mattermosturl", help="Post the message to the specified webhook URL")
    parser.add_argument("-u", "--username", default="pymattertee", help="Displayed username")
    parser.add_argument("arguments", nargs="+", help="Arguments to print")
    args = parser.parse_args()

    channel = decode_text(args.channel if args.channel else os.environ.get("MM_CHANNEL"))
    icon_url = decode_text(args.iconurl if args.iconurl else os.environ.get("MM_ICONURL"))
    url = decode_text(args.mattermosturl if args.mattermosturl else os.environ.get("MM_HOOK"))
    username = decode_text(args.username if args.username else os.environ.get("MM_USERNAME"))

    if not url:
        sys.stderr.write(b"No Mattermost URL was provided\n")
        sys.exit(-1)

    buf = ' '.join(args.arguments)
    now = datetime.datetime.utcnow().strftime('%c')
    msg = IncomingMessage(username=username, icon_url=icon_url, channel=channel, text='')
    att = Attachment(fallback=buf, text=buf)
    att.fields.append(Field('Date', now, True))
    att.fields.append(Field('Local user', local_username, True))
    att.fields.append(Field('Hostname', hostname, True))
    msg.attachments.append(att)
    msg.post(url)


if __name__ == '__main__':
    main()
