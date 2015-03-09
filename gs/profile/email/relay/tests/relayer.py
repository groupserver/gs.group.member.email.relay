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
import gs.profile.email.relay.relayer


class TestRelayMessage(TestCase):
    def test_userId_from_email(self):
        rm = RelayMessage(None)
        email = 'member-1a2b3c@groups.example.com'
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
    def test_via_name(self, mockCreateObject):
        mockSiteInfo = mockCreateObject.return_value
        mockSiteInfo.name = 'Le site'

        rm = RelayMessage(None)
        leNom = 'Ça va'
        r = rm.get_via_name(leNom)
        expected = b'=?utf-8?q?=C3=87a_va_via_Le_site?='
        self.assertEqual(expected, r)
