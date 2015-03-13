from __future__ import absolute_import, unicode_literals
from Products.CustomUserFolder.userinfo import userInfo_to_anchor
from Products.GSAuditTrail import (IAuditEvent, BasicAuditEvent, AuditQuery)
from gs.core import to_id, to_unicode_or_bust, curr_time as now
from random import SystemRandom
from zope.component.interfaces import IFactory
from zope.interface import implementedBy, implementer

from logging import getLogger
SUBSYSTEM = 'gs.profile.email.relay'
log = getLogger(SUBSYSTEM)

UNKNOWN = '0'
RELAY_TO_USER_FROM_USER = '1'
RELAY_TO_USER_FROM_NONUSER = '2'


@implementer(IFactory)
class AuditEventFactory(object):
    title = 'Profile Email Relay Audit-Event Factory'
    description = 'Creates a GroupServer audit event for message relays'

    def __call__(self, context, event_id, code, date, userInfo,
                 instanceUserInfo, siteInfo, groupInfo=None, instanceDatum='',
                 supplementaryDatum='', subsystem=''):

        if (code == RELAY_TO_USER_FROM_USER):
            event = RelayToUserFromUserEvent(
                context, event_id, date, userInfo, instanceUserInfo, siteInfo,
                groupInfo, instanceDatum, supplementaryDatum)
        elif (code == RELAY_TO_USER_FROM_NONUSER):
            event = RelayToUserFromNonUserEvent(
                context, event_id, date, userInfo, instanceUserInfo, siteInfo,
                groupInfo, instanceDatum, supplementaryDatum)
        else:
            event = BasicAuditEvent(
                context, event_id, UNKNOWN, date, userInfo, instanceUserInfo,
                siteInfo, groupInfo, instanceDatum, supplementaryDatum,
                SUBSYSTEM)
        assert event
        return event

    def getInterfaces(self):
        return implementedBy(BasicAuditEvent)


@implementer(IAuditEvent)
class RelayToUserFromUserEvent(BasicAuditEvent):
    ''' An audit-trail event representing a message from one GroupServer User
        to another GroupServer user, being relayed to the receiving user's
        actual email address via their GroupServer obfuscated address'''

    def __init__(self, context, event_id, date, receiverUserInfo,
                 senderUserInfo, siteInfo, groupInfo, obfuscatedAddress,
                 realAddress):
        super(RelayToUserFromUserEvent, self).__init__(
            context, event_id, RELAY_TO_USER_FROM_USER, date, receiverUserInfo,
            senderUserInfo, siteInfo, groupInfo, obfuscatedAddress,
            realAddress, SUBSYSTEM)

    def __unicode__(self):
        retval = 'A message from %s (%s) to obfuscated address %s has been '\
                 'relayed to %s (%s)' %\
            (self.instanceUserInfo.name, self.instanceUserInfo.id,
             self.instanceDatum, self.userInfo.name, self.userInfo.id)
        return retval

    @property
    def xhtml(self):
        cssClass = 'audit-event gs-profile-email-relay-%s' % self.code
        m = '<span class="{cssClass}">A message from {sendingUser} to '\
            'obfuscated address {{obfuscatedAddress}} has been relayed to '\
            '{{receivingUser}}'
        retval = m.format(
            cssClass=cssClass,
            sendingUser=userInfo_to_anchor(self.instanceUserInfo),
            obfuscatedAddress=self.instanceDatum,
            receivingUser=userInfo_to_anchor(self.userInfo))
        return retval


@implementer(IAuditEvent)
class RelayToUserFromNonUserEvent(BasicAuditEvent):
    ''' An audit-trail event representing a message from a non GroupServer User
        to a GroupServer user, being relayed to the receiving user's actual
        email address via their GroupServer obfuscated address'''

    def __init__(self, context, event_id, date, receiverUserInfo,
                 senderUserInfo, siteInfo, groupInfo, obfuscatedAddress,
                 realAddress):
        super(RelayToUserFromNonUserEvent, self).__init__(
            context, event_id, RELAY_TO_USER_FROM_NONUSER, date,
            receiverUserInfo, senderUserInfo, siteInfo, groupInfo,
            obfuscatedAddress, realAddress, SUBSYSTEM)

    def __unicode__(self):
        retval = 'A message from a non-user with address %s to obfuscated '\
                 'address %s has been relayed to %s (%s)' %\
            (self.supplementaryDatum, self.instanceDatum, self.userInfo.name,
             self.userInfo.id)
        return retval

    @property
    def xhtml(self):
        cssClass = 'audit-event gs-profile-email-relay-%s' % self.code
        m = '<span class="{cssClass}">A message from a non-user with address '\
            ' {sendingAddress} to obfuscated address {{obfuscatedAddress}} '\
            'has been relayed to {{receivingUser}}'
        retval = m.format(
            cssClass=cssClass,
            sendingAddress=self.supplementaryDatum,
            obfuscatedAddress=self.instanceDatum,
            receivingUser=userInfo_to_anchor(self.userInfo))
        return retval


class Auditor(object):
    def __init__(self, context, receivingUserInfo, sendingUserInfo, siteInfo):
        self.context = context
        self.userInfo = receivingUserInfo
        self.instanceUserInfo = sendingUserInfo
        self.siteInfo = siteInfo
        self.queries = AuditQuery()
        self.factory = AuditEventFactory()

    def info(self, code, instanceDatum='', supplementaryDatum=''):
        date = now()
        event_id = to_id(to_unicode_or_bust(self.userInfo.id)
                         + unicode(date)
                         + unicode(SystemRandom().randint(0, 1024))
                         + to_unicode_or_bust(self.siteInfo.id)
                         + to_unicode_or_bust(self.siteInfo.name)
                         + to_unicode_or_bust(code)
                         + to_unicode_or_bust(instanceDatum)
                         + to_unicode_or_bust(supplementaryDatum))

        e = self.factory(
            self.context, event_id, code, date, self.userInfo,
            self.instanceUserInfo, self.siteInfo, None,
            instanceDatum=instanceDatum, supplementaryDatum=supplementaryDatum,
            subsystem=SUBSYSTEM)
        self.queries.store(e)
        log.info(e)
