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
from mock import patch
from unittest import TestCase
from gs.profile.email.relay.relayer import RelayMessage


test_email_for_relay = """\
From: "GroupServer Administrator" <admin@gstest>
Subject: Donkeys
To: p-userId1@gstest
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
Sender: "GroupServer Administrator" <admin@gstest>

Donkeys are great!

"""


class TestRelayMessage(TestCase):
    def test_userId_from_email(self):
        rm = RelayMessage(None)
        email = 'p-1a2b3c@groups.example.com'
        r = rm.userId_from_email(email)
        self.assertEqual('1a2b3c', r)

    def test_userId_from_email_not_relay(self):
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

        # --=mpj17=-- We do not need a full message, just a dict that looks
        # like the headers of an email message
        f = 'Me! <member@example.com>'
        m = {}
        m['From'] = f
        rm = RelayMessage(None)
        rm.munge_for_dmarc(m)

        self.assertIn('From', m)
        expected = 'Me! via Le site <{0}>'.format(supportEmail)
        self.assertEqual(expected, m['From'])
        self.assertIn('Sender', m)
        self.assertEqual(f, m['Sender'])
        self.assertIn('Reply-to', m)
        self.assertEqual('member@example.com', m['Reply-to'])

    @patch.object(RelayMessage, 'get_auditor')
    @patch.object(RelayMessage, 'get_dmarc_policy_for_host')
    @patch.object(RelayMessage, 'new_to')
    @patch('gs.profile.email.relay.relayer.send_email')
    @patch('gs.profile.email.relay.relayer.createObject')
    def test_relay(self, mockCreateObject, mock_send_email, mock_new_to,
                   mock_get_dmarc_policy_for_host, mock_get_auditor):
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'
        supportEmail = 'support@lists.example.com'
        mockSiteInfo.get_support_email.return_value = supportEmail
        mock_new_to.return_value = 'user@example.com'
        mock_get_dmarc_policy_for_host.return_value = 'pass'

        rm = RelayMessage(None)
        rm.relay(test_email_for_relay)
        self.assertEqual(1, mock_send_email.call_count)
        args, kw_args = mock_send_email.call_args
        # Make sure the To header is correctly set
        self.assertIn('To: user@example.com', args[2])
