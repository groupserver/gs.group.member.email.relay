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
import base64
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from gs.auth.token import log_auth_error
from gs.content.form.base import SiteForm
from .relayer import RelayMessage
# from .audit import AddAuditor, ADD_EMAIL
from .interfaces import IRelayEmail


class RelayEmail(SiteForm):
    label = 'Relay an email'
    pageTemplateFileName = 'browser/templates/form.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IRelayEmail, render_context=False)

    def __init__(self, context, request):
        super(RelayEmail, self).__init__(context, request)

    @form.action(name="add", label='Add',
                 failure='handle_add_action_failure')
    def handle_add(self, action, data):
        try:
            msg = base64.b64decode(data['emailMessage'])
        except TypeError:
            # wasn't base64 encoded. Try and proceed anyway!
            msg = data['emailMessage']
        r = RelayMessage(self.context)
        r.relay(msg)
        # Because the text-version of the email message can mess with
        # the content type
        self.request.response.setHeader(b'Content-type', b'text/html')
        self.status = 'Done'

    def handle_add_action_failure(self, action, data, errors):
        log_auth_error(self.context, self.request, errors)
        if len(errors) == 1:
            self.status = '<p>There is an error:</p>'
        else:
            self.status = '<p>There are errors:</p>'
