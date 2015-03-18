==========================
``gs.profile.email.relay``
==========================
~~~~~~~~~~~~~~~~~~~~~~~~~
Relay messages to someone
~~~~~~~~~~~~~~~~~~~~~~~~~

:Author: `Michael JasonSmith`_
:Contact: Michael JasonSmith <mpj17@onlinegroups.net>
:Date: 2015-03-17
:Organization: `GroupServer.org`_
:Copyright: This document is licensed under a
  `Creative Commons Attribution-Share Alike 4.0 International License`_
  by `OnlineGroups.net`_.

..  _Creative Commons Attribution-Share Alike 4.0 International License:
    http://creativecommons.org/licenses/by-sa/4.0/

Introduction
============

This product is responsible for relaying email messages to group
members that use obfuscated email addresses.

Normally the address that appears in the ``From`` header of a
message is sent out as-is [#sender]_. However, some sites have
**DMARC policies** that require a modification the ``From``
header. GroupServer_ modifies the header by creating a new
``From`` address.

The new address is created from the profile-identifier (user-ID)
of the member who sent the message. This **obfuscated address**
works well for getting the message delivered. However, replies to
these messages come back to GroupServer, rather than the original
author. To overcome this problem these replies are detected and
the messages sent on the original address. It is this relaying of
messages that is carried out by this product.

The main thing defined by this product is a page_ that processes
the message. However, the configuration_ for the relay-addresses
is widely used in GroupServer.

Page
====

The page ``gs-profile-email-relay.html`` in the site context
provides a **web hook** that allows an email message to be
relayed by the incoming message processing script
[#smtp2gs]_. The form takes the email message as a base-64
encoded string, and the authentication token, and relays it on.

The user-identifier for a group member is extracted from the
``To`` address. The email message is then sent onto the preferred
email address of the member.

Configuration
=============

There are two parts to the configuration of this product: the
token_ and the prefix_.

Token
-----

The ``token`` in the ``webservice`` section is used to provide
the token to the script that processing incoming email for
GroupServer [#smtp2gs]_.

.. code-block:: ini

  [webservice-default]
  token = thisIsAToken

Prefix
------

Email messages that need to be relayed will have a ``To`` address
with a particular prefix. By default the prefix is ``p-`` (short
for *profile*, much like the ``/p/`` URLs). This prefix is
stripped off the front of the *mbox* part of the email address in
order to generate the user-identifier.

However, the default prefix can be changed by adding the
``relay-address-prefix`` option to the ``smtp`` configuration
section. For example, the following will change the prefix to
``human-resource-``

.. code-block:: ini

    [smtp-testing]
    hostname = localhost
    port = 25
    queuepath = /tmp/test-mail-queue
    xverp = True
    processorthread = False
    relay-address-prefix = human-resource-

This configuration option is used by

* The product that sends messages from a group [#sender]_,
* The email processing script [#smtp2gs]_, and
* This product.

Resources
=========

- Code repository:
  https://github.com/groupserver/gs.profile.email.relay
- Questions and comments to
  http://groupserver.org/groups/development
- Report bugs at https://redmine.iopen.net/projects/groupserver

.. [#sender] See the ``gs.group.list.sender`` product
             <https://github.com/groupserver/gs.group.list.sender>

.. [#smtp2gs] See the ``gs.group.messages.add.smtp2gs`` product
              <https://github.com/groupserver/gs.group.messages.add.smtp2gs>

.. _GroupServer: http://groupserver.org/
.. _GroupServer.org: http://groupserver.org/
.. _OnlineGroups.Net: https://onlinegroups.net
.. _Michael JasonSmith: http://groupserver.org/p/mpj17

..  LocalWords:  DMARC
