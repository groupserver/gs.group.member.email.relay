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
from __future__ import absolute_import, unicode_literals, print_function
from email.parser import Parser
from mock import patch
from unittest import TestCase
from gs.profile.email.relay.relayer import RelayMessage


test_email_for_relay = """\
From: "GroupServer Administrator" <admin@example.com>
Subject: Donkeys
To: p-userId1@example.com
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Donkeys are great!

"""


class TestRelayMessage(TestCase):
    @patch.object(RelayMessage, 'config')
    def test_userId_from_email(self, configMock):
        configMock.get.return_value = {}

        rm = RelayMessage(None)
        email = 'p-1a2b3c@groups.example.com'
        r = rm.userId_from_email(email)
        self.assertEqual('1a2b3c', r)

    @patch.object(RelayMessage, 'config')
    def test_userId_from_email_not_relay(self, configMock):
        configMock.get.return_value = {}

        rm = RelayMessage(None)
        email = 'should.fail@groups.example.com'
        with self.assertRaises(ValueError):
            rm.userId_from_email(email)

    def test_userId_from_email_not_addr(self):
        rm = RelayMessage(None)
        email = 'should.fail'
        with self.assertRaises(ValueError):
            rm.userId_from_email(email)

    @patch('gs.profile.email.relay.relayer.createObject')
    def test_get_via_name(self, mockCreateObject):
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'

        rm = RelayMessage(None)
        leNom = 'Ça va'
        r = rm.get_via_name(leNom)
        expected = b'=?utf-8?q?=C3=87a_va_via_Le_site?='
        self.assertEqual(expected, r)

    @patch('gs.profile.email.relay.relayer.createObject')
    def test_munge_for_dmarc(self, mockCreateObject):
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'
        supportEmail = 'support@lists.example.com'
        mockSiteInfo.get_support_email.return_value = supportEmail

        m = Parser().parsestr(test_email_for_relay)
        f = m['From']

        rm = RelayMessage(None)
        rm.munge_for_dmarc(m)

        self.assertIn('From', m)
        e = 'GroupServer Administrator via Le site <{0}>'
        expected = e.format(supportEmail)
        self.assertEqual(expected, m['From'])
        self.assertIn('Sender', m)
        self.assertEqual(f, m['Sender'])
        self.assertIn('Reply-to', m)
        self.assertEqual('admin@example.com', m['Reply-to'])

        # Check that we only have one From header. This happend.
        fs = m.get_all('From')
        self.assertEqual(1, len(fs))

    @patch('gs.profile.email.relay.relayer.createObject')
    def test_munge_for_dmarc_sender(self, mockCreateObject):
        'Test that we replace the sender'
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'
        supportEmail = 'support@lists.example.com'
        mockSiteInfo.get_support_email.return_value = supportEmail

        m = Parser().parsestr(test_email_for_relay)
        p = 'Person <person@people.example.com>'
        m.add_header('Sender', p)
        f = m['From']

        rm = RelayMessage(None)
        rm.munge_for_dmarc(m)

        self.assertIn('Sender', m)
        self.assertEqual(f, m['Sender'])
        self.assertIn('x-gs-relay-sender', m)
        self.assertEqual(p, m['x-gs-relay-sender'])

    @patch('gs.profile.email.relay.relayer.createObject')
    def test_munge_for_dmarc_replyto(self, mockCreateObject):
        'Test that we leave the Reply-to header unchanged'
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'
        supportEmail = 'support@lists.example.com'
        mockSiteInfo.get_support_email.return_value = supportEmail

        m = Parser().parsestr(test_email_for_relay)
        p = 'Person <person@people.example.com>'
        m['Reply-to'] = p
        rm = RelayMessage(None)
        rm.munge_for_dmarc(m)

        self.assertIn('Reply-to', m)
        self.assertEqual(p, m['Reply-to'])
        # Check that we only have one Reply-to header.
        replyTos = m.get_all('Reply-to')
        self.assertEqual(1, len(replyTos))

    @patch.object(RelayMessage, 'config')
    @patch.object(RelayMessage, 'get_auditor')
    @patch.object(RelayMessage, 'get_dmarc_policy_for_host')
    @patch.object(RelayMessage, 'new_to')
    @patch('gs.profile.email.relay.relayer.send_email')
    @patch('gs.profile.email.relay.relayer.createObject')
    def test_relay(self, mockCreateObject, mock_send_email, mock_new_to,
                   mock_get_dmarc_policy_for_host, mock_get_auditor,
                   configMock):
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'
        supportEmail = 'support@lists.example.com'
        mockSiteInfo.get_support_email.return_value = supportEmail
        mock_new_to.return_value = 'user@example.com'
        mock_get_dmarc_policy_for_host.return_value = 'pass'
        configMock.get.return_value = {}

        rm = RelayMessage(None)
        rm.relay(test_email_for_relay)
        self.assertEqual(1, mock_send_email.call_count)
        args, kw_args = mock_send_email.call_args
        # Make sure the To header is correctly set
        self.assertIn('To: user@example.com', args[2])

    @patch.object(RelayMessage, 'config')
    def test_get_relay_address_prefix_from_config(self, configMock):
        'Test that we get the relay-address prefix from the config'
        prefix = 'hamster-'
        schema = {'relay-address-prefix': prefix}
        configMock.get.return_value = schema

        rm = RelayMessage(None)
        r = rm.relayAddressPrefix
        self.assertEqual(prefix, r)

    @patch.object(RelayMessage, 'config')
    def test_get_relay_address_prefix_from_config_missing(self, configMock):
        'Test that we get "p-" when the prefix is missing'
        schema = {}
        configMock.get.return_value = schema

        rm = RelayMessage(None)
        r = rm.relayAddressPrefix
        self.assertEqual('p-', r)
