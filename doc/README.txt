====================
CPSMailAccess README
====================

:Revision: $Id$

.. sectnum::    :depth: 4
.. contents::   :depth: 4


For more complete documentation, please refer to the CPS User Guide,
created by Steve Meaker here:
http://www.cps-project.org/sections/documentation/users/cps-manual-english-pdf/


Introduction
============

CPSMailAccess is a full featured webmail application for CPS3. It
provides a flexible web interface to browse and send mails.

Features of the CPSMailAccess include among others:

- AJAX based mail editor
- drag'n'drop for mails and folders
- incoming mails filtering
- private and public address books
- etc.


Architecture
============

CPSMailAccess is built on Five, thus making the Product easily
portable to Zope 3. Its architecture also facilitates integration
with any Zope-based platform as its dependencies to CPS3 are close
to none and taught to be easily overridden.


ZODB usage
----------

For each mailbox, CPSMailAccess creates a folder structure
equivalent to the structure found on the mail server. Each IMAP
folder is represented by a ZODB folder. Mails are not fully
retrieved, but for each one of them, a ZODB object is created,
holding the mail unique identifier and the useful headers.

90% percent of webmail user actions are based on viewing and
sorting folders, searching mail, etc. So the information kept on
ZODB side lets the application work on mails without calling back
and back again the IMAP server, as we will see in next parts of
this document.


Synchronization process
-----------------------

When the box is being fully synchronized, CPSMailAccess uses the
following order:

- The folder structure is compared and folders are created or
  suppressed.

- For each folder, the message list is compared and messages are
  deleted or created.


The "every day synchronization" which is used when the user
refreshes his or her box is similar but will just synchronize the
INBOX folder message list.


Mail caching
------------

When the user views a mail for the first time, the application
calls the server to get deeper information about the mail
structure and retrieves the mail body and the list of attached
parts. This data is kept in the ZODB side so the IMAP server won't
be called again when the user comes back to the message.

The administrator can reduce the size taken by the box by removing
information the user gathers through his or her work.


Mail indexing
-------------

CPSMailAccess uses one Zemantic catalog per box and indexes:

- Relations between mails, that are given by headers like
  Refferees, In-Reply-To,etc..

- Relations between a mail and its headers.

This indexation provides a very fast Zope-side mail search engine.


Address Books
-------------

Each user can have contacts in a private address book which is a
private directory and in a public address book which is e regular
directory.

When a user sends a mail to someone, the recipient is
automatically added into his or her address book. Each mail sent
gives to each address book entry a point. The address books view
will display contacts sorted with this criteria, so you can view
your preferred contacts first.


Installation
============

See INSTALLATION.txt.


Usage
=====

CPSMailAccess has been taught to be ergonomic. Its user interface
is very close to rich mail clients and some features such as
folder and mail drag'n'drop makes it intuitive.


Get involved!
=============

If you'd like to help with CPSMailAccess development or porting to
other platforms, please join the cps-devel mailing list at
http://lists.nuxeo.com/mailman/listinfo/cps-devel (a dedicated
list will be created if needed in the future).

We would be pleased to get some feedback!


.. Emacs
.. Local Variables:
.. mode: rst
.. End:
.. Vim
.. vim: set filetype=rst:

