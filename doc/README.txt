for a complete documentation, please refer to the CPS User Guide,
created by Steve Meaker here: http://www.cps-project.org/sections/documentation/users/cps-manual-english-pdf/

0) Intro
1) Architecture
2) Installation
3) Usage
4) Get involved

0) Intro

CPSMailAccess is a full featured webmail application for CPS3. It provides a flexible web interface to browse and send mails.

Features of the CPSMailAccess include among others:

    * AJAX based mail editor
    * drag'n'drop for mails and folders
    * incoming mails filtering
    * private and public address books
    * etc.

1) Architecture

CPSMailAccess is built on Five, thus making the Product easily portable to Zope 3. Its architecture also allows to integrate it to any Zope-based platform as its dependencies to CPS3 are close to none and thaught to be easily overriden.

a) ZODB Usage

For each mailbox, CPSMailAccess creates a folder structure equivalent to the structure found on the mail server. Each IMAP folder is represented by a ZODB folder. Mails are not fully retrieved, but for each one of them, a ZODB object is created, holding the mail unique identifier and the useful headers.

90% percent of webmail user actions are based on viewing and sorting folders, searching mail, etc. So the information kept on ZODB side let the application work on mails without calling back and back again the IMAP server like we will see in next parts of this document.

b) Synchronisation process

When the box is beeing fully synchronized, CPSMailAccess uses the following order:

    * the folder structure is compared and folders are created or suppressed
    * for each folder, the message list is compared and messages are deleted or created.


The "every day synchronisation" wich is used when the user refresh his or her box is similar but will just synchronize the INBOX folder message list.

c) Mail caching

When the user views a mail for the first time, the application calls the server to get deeper informations on mail structure and retrieves the mail body and the list of attached parts. This data is kept in the ZODB side so the IMAP server won't be called again when the user will come back to the message.

The administrator can reduce the size taken by the box by removing these informations the user gathers through his or her work.

d) Mail indexing

CPSMailAccess uses one Zemantic catalog per box and indexes:

    * Relations between mails, that are given by headers like Refferees, In-Reply-To,etc..
    * Relations between a mail and its headers

This indexation provides a  very fast Zope-side mail search engine.

e) Address Books

Each user can have contacts in a private address book wich is a private Directory and in a public address book wich is e regular directory.

When a user sends a mail to someone, the recipient is automatically added into his or her adress book. Each mail sent gives to each address book entry a point. The adress books view will display contacts sorted with this criteria, so you can view your prefered contacts first.


2) Installation

see INSTALLATION.txt


3) Usage

CPSMailAccess has been thaught to be ergonomic. Its user interface is very close to rich mail clients and some features such as folder and mail drag'n'drop makes it intuitive.

4) Get involved!

If you'd like to help with CPSMailAccess development or porting to other plateforms, please join the cps-devel mailing list at http://lists.nuxeo.com/mailman/listinfo/cps-devel (a dedicated list will be created if needed in the future).

We would be pleased to get some feedback!
