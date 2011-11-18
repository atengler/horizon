# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from mox import IsA, IgnoreArg
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import test
from horizon.dashboards.nova.floating_ips.forms import FloatingIpAssociate


FLOATING_IPS_INDEX = reverse('horizon:nova:floating_ips:index')


class FloatingIpViewTests(test.BaseViewTests):

    def setUp(self):
        super(FloatingIpViewTests, self).setUp()
        server = api.Server(None, self.request)
        server.id = 1
        server.name = 'serverName'
        self.server = server
        self.servers = (server, )

        floating_ip = api.FloatingIp(None)
        floating_ip.id = 1
        floating_ip.fixed_ip = '10.0.0.4'
        floating_ip.instance_id = 1
        floating_ip.ip = '58.58.58.58'

        self.floating_ip = floating_ip
        self.floating_ips = [floating_ip, ]

    def test_index(self):
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        api.tenant_floating_ip_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.floating_ips)
        self.mox.ReplayAll()

        res = self.client.get(FLOATING_IPS_INDEX)
        self.assertTemplateUsed(res, 'nova/floating_ips/index.html')
        self.assertItemsEqual(res.context['floating_ips'], self.floating_ips)

    def test_associate(self):
        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list = self.mox.CreateMockAnything()
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.tenant_floating_ip_get = self.mox.CreateMockAnything()
        api.tenant_floating_ip_get(IsA(http.HttpRequest), str(1)).\
                                    AndReturn(self.floating_ip)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:floating_ips:associate',
                                      args=[1]))
        self.assertTemplateUsed(res, 'nova/floating_ips/associate.html')

    def test_associate_post(self):
        server = self.server

        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list = self.mox.CreateMockAnything()
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        api.tenant_floating_ip_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.floating_ips)

        self.mox.StubOutWithMock(api, 'server_add_floating_ip')
        api.server_add_floating_ip = self.mox.CreateMockAnything()
        api.server_add_floating_ip(IsA(http.HttpRequest), IsA(unicode),
                                                          IsA(unicode)).\
                                                          AndReturn(None)
        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(unicode))

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.tenant_floating_ip_get = self.mox.CreateMockAnything()
        api.tenant_floating_ip_get(IsA(http.HttpRequest), str(1)).\
                                   AndReturn(self.floating_ip)
        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:floating_ips:associate',
                                      args=[1]),
                               {'instance_id': 1,
                                'floating_ip_id': self.floating_ip.id,
                                'floating_ip': self.floating_ip.ip,
                                'method': 'FloatingIpAssociate'})

        self.assertRedirects(res, FLOATING_IPS_INDEX)

    def test_associate_post_with_exception(self):
        server = self.server

        self.mox.StubOutWithMock(api, 'server_list')
        api.server_list = self.mox.CreateMockAnything()
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        api.tenant_floating_ip_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.floating_ips)

        self.mox.StubOutWithMock(api, 'server_add_floating_ip')
        api.server_add_floating_ip = self.mox.CreateMockAnything()
        exception = novaclient_exceptions.ClientException('ClientException',
                                                    message='clientException')
        api.server_add_floating_ip(IsA(http.HttpRequest), IsA(unicode),
                                                          IsA(unicode)).\
                                                          AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.tenant_floating_ip_get = self.mox.CreateMockAnything()
        api.tenant_floating_ip_get(IsA(http.HttpRequest), IsA(unicode)).\
                                   AndReturn(self.floating_ip)
        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:floating_ips:associate',
                                      args=[1]),
                               {'instance_id': 1,
                                'floating_ip_id': self.floating_ip.id,
                                'floating_ip': self.floating_ip.ip,
                                'method': 'FloatingIpAssociate'})
        self.assertRaises(novaclient_exceptions.ClientException)

        self.assertRedirects(res, FLOATING_IPS_INDEX)

    def test_disassociate(self):
        res = self.client.get(reverse('horizon:nova:floating_ips:disassociate',
                                      args=[1]))
        self.assertTemplateUsed(res, 'nova/floating_ips/associate.html')

    def test_disassociate_post(self):
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        api.tenant_floating_ip_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.floating_ips)

        self.mox.StubOutWithMock(api, 'server_remove_floating_ip')
        api.server_remove_floating_ip = self.mox.CreateMockAnything()
        api.server_remove_floating_ip(IsA(http.HttpRequest), IsA(int),
                                                             IsA(int)).\
                                                             AndReturn(None)
        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(unicode))

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.tenant_floating_ip_get = self.mox.CreateMockAnything()
        api.tenant_floating_ip_get(IsA(http.HttpRequest), IsA(unicode)).\
                                   AndReturn(self.floating_ip)
        self.mox.ReplayAll()
        res = self.client.post(
                 reverse('horizon:nova:floating_ips:disassociate', args=[1]),
                 {'floating_ip_id': self.floating_ip.id,
                  'method': 'FloatingIpDisassociate'})
        self.assertRedirects(res, FLOATING_IPS_INDEX)

    def test_disassociate_post_with_exception(self):
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        api.tenant_floating_ip_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.floating_ips)

        self.mox.StubOutWithMock(api, 'server_remove_floating_ip')
        exception = novaclient_exceptions.ClientException('ClientException',
                                                    message='clientException')
        api.server_remove_floating_ip(IsA(http.HttpRequest),
                                      IsA(int),
                                      IsA(int)).AndRaise(exception)
        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.tenant_floating_ip_get = self.mox.CreateMockAnything()
        api.tenant_floating_ip_get(IsA(http.HttpRequest), IsA(unicode)).\
                                   AndReturn(self.floating_ip)
        self.mox.ReplayAll()
        res = self.client.post(
                reverse('horizon:nova:floating_ips:disassociate', args=[1]),
                {'floating_ip_id': self.floating_ip.id,
                 'method': 'FloatingIpDisassociate'})
        self.assertRaises(novaclient_exceptions.ClientException)
        self.assertRedirects(res, FLOATING_IPS_INDEX)
