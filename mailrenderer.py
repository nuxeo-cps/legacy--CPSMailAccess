from email.MIMEAudio import MIMEAudio
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email.MIMEMessage import MIMEMessage
from email.MIMEMultipart import MIMEMultipart
from email import Iterators, Message
from interfaces import IMailRenderer
from zope.interface import implements
from mimetools import decode
from email import Parser

class MailRenderer:
    """A tool to render MIME parts

    >>> f = MailRenderer()
    >>> IMailRenderer.providedBy(f)
    True
    """
    implements(IMailRenderer)

    def _extractBodies(self, mail):
        """ extracts the body
        """
        it = Iterators.body_line_iterator(mail)
        lines = list(it)
        return ''.join(lines)

    def renderBody(self, mail, part_index=0):
        """ renders the mail given body part
        """
        if mail is None:
            return ''
        part = mail.getPart(part_index)
        if part is None:
            body = ''
        else:
            body = self._extractBodies(part)
        return body
