# Make this a module

import sys

import fakesmtplib

if sys.modules.has_key('smtplib'):
    del sys.modules['smtplib']
sys.modules['smtplib'] = fakesmtplib
