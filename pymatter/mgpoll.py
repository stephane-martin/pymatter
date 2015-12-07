# -*- coding: utf-8 -*-

"""
Poll Mailgun for messages and forwards them to a Mattermost Incoming Webhook.
"""

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
from os.path import expanduser, abspath, exists

CONF_FILE = os.environ.get('MM_MAILGUN_CONF')
if CONF_FILE is None:
    CONF_FILE = abspath(expanduser('.pymatter/mailgun.conf'))
if not exists(CONF_FILE):
    sys.stderr.write(b"No configuration provided\n")
    sys.exit(-1)


