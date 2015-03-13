# -*- coding: utf-8 -*-
############################################################################
#
# Copyright © 2015 OnlineGroups.net and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
############################################################################
from __future__ import absolute_import, unicode_literals
from email.header import Header
from email.parser import Parser
from email.utils import (parseaddr, formataddr)
import re
from zope.cachedescriptors.property import Lazy
from zope.component import createObject
from gs.dmarc import (lookup_receiver_policy, ReceiverPolicy)
from gs.profile.email.base import EmailUser
from gs.email import send_email
from gs.cache import cache
from .audit import RELAY_TO_USER_FROM_USER, RELAY_TO_USER_FROM_NONUSER, Auditor


RELAY_ADDRESS_PREFIX = 'p-'

class RelayMessage(object):
    relayAddrRe = re.compile('%s(.+)@(.+)' % RELAY_ADDRESS_PREFIX)
    actualPolicies = (ReceiverPolicy.quarantine, ReceiverPolicy.reject)

    def __init__(self, context):
        self.context = context

    @Lazy
    def siteInfo(self):
        '''Information about the current site.'''
        retval = createObject('groupserver.SiteInfo', self.context)
        return retval

    def userId_from_email(self, email):
        e = parseaddr(email)
        addr = e[1]
        if '@' not in addr:
            m = 'Not an email address: {0}'.format(email)
            raise ValueError(m)
        m = self.relayAddrRe.match(addr)
        if not m:
            m = 'Not an email address for relaying: {0}'.format(email)
            raise ValueError(m)
        retval = m.groups()[0]
        return retval

    def userInfo_from_obfuscated_email(self, o_email):
        'Get the userInfo object from the obfuscated email address'
        userId = self.userId_from_email(o_email)
        userInfo = createObject('groupserver.UserFromId', self.context,
                                userId)
        return userInfo

    def new_to(self, userInfo):
        'Get the new To address from the userInfo object'
        eu = EmailUser(self.context, userInfo)
        addrs = eu.get_verified_addresses()
        addrs = addrs if addrs else eu.get_unverified_addresses()  # Legit?
        assert addrs, 'No addresses for {0}'.format(userInfo.id)

        retval = addrs[0]
        return retval

    @staticmethod
    @cache('gs.group.list.sender.header.from.dmarc', lambda h: h, 7 * 60)
    def get_dmarc_policy_for_host(host):
        retval = lookup_receiver_policy(host)
        return retval

    def get_via_name(self, oldName):
        n = '{0} via {1}'.format(oldName, self.siteInfo.name)
        headerName = Header(n, 'utf-8')
        retval = headerName.encode()
        return retval

    def munge_for_dmarc(self, message):
        oldFrom = parseaddr(message['From'])
        message['Sender'] = message['From']
        if 'Reply-to' not in message:
            # Reply-to just contains the addr, not the fancy names
            message['Reply-to'] = oldFrom[1]
        viaName = self.get_via_name(oldFrom[0])
        message['From'] = formataddr((viaName,
                                      self.siteInfo.get_support_email()))

    def relay(self, messageString):
        parser = Parser()
        message = parser.parsestr(messageString)

        oldTo = message['To']
        message['x-original-to'] = oldTo
        rui = self.userInfo_from_obfuscated_email(oldTo)
        newTo = self.new_to(rui)
        message['To'] = newTo

        oldFrom = parseaddr(message['From'])
        try:
            origHost = oldFrom[1].split('@')[1]
        except IndexError as ie:
            m = 'Could not parse the From address\n{addr}\n{err}'
            msg = m.format(addr=oldFrom[1], err=ie)
            raise ValueError(msg)

        sui = createObject('groupserver.EmailUserFromEmailAddress',
                           self.context, oldFrom[1])
        sui = None if sui is None else sui.userInfo

        dmarcPolicy = self.get_dmarc_policy_for_host(origHost)
        if (dmarcPolicy in self.actualPolicies):
            self.munge_for_dmarc(message)

        auditor = self.get_auditor(rui, sui)
        oldToAddress = parseaddr(oldTo)[1]
        if sui is None:
            auditor.info(RELAY_TO_USER_FROM_NONUSER, oldToAddress, oldFrom[1])
        else:
            auditor.info(RELAY_TO_USER_FROM_USER, oldToAddress)

        mailString = message.as_string()
        send_email(self.siteInfo.get_support_email(), newTo, mailString)

    def get_auditor(self, receivingUserInfo, sendingUserInfo):
        auditor = Auditor(self.context, receivingUserInfo, sendingUserInfo,
                          self.siteInfo)
        return auditor
