# pyzilla.py is a Python wrapper for the xmlrpc interface of bugzilla
# Copyright (C) <2010>  <Noufal Ibrahim>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import xmlrpclib
import urllib2
import logging
import cookielib

def create_user_agent():
    ma, mi, rel = sys.version_info[:3]
    return "xmlrpclib - Python-%s.%s.%s"%(ma, mi, rel)

class CookieAuthXMLRPCTransport(xmlrpclib.SafeTransport):
    """
    xmlrpclib.Transport that caches authentication cookies in a
    local cookie jar and reuses them.

    Based off `this recipe
    <http://code.activestate.com/recipes/501148-xmlrpc-serverclient-which-does-cookie-handling-and/>`_

    """

    def __init__(self, cookiefile = False, user_agent = False):
        self.cookiefile = cookiefile or "cookies.txt"
        self.user_agent = user_agent or create_user_agent()
        xmlrpclib.SafeTransport.__init__(self)
        
    def send_cookie_auth(self, connection):
        """Include Cookie Authentication data in a header"""
        logging.debug("Sending cookie")
        cj = cookielib.LWPCookieJar()
        cj.load(self.cookiefile)
        for cookie in cj:
            connection.putheader("Cookie", "%s=%s" % (cookie.name,cookie.value))

    ## override the send_host hook to also send authentication info
    def send_host(self, connection, host):
        xmlrpclib.Transport.send_host(self, connection, host)
        if os.path.exists(self.cookiefile):
            logging.debug(" Sending back cookie header")
            self.send_cookie_auth(connection)

    def request(self, host, handler, request_body, verbose=0):
        # dummy request class for extracting cookies 
        class CookieRequest(urllib2.Request):
            pass
        # dummy response class for extracting cookies 
        class CookieResponse:
            def __init__(self, headers):
                self.headers = headers
            def info(self):
                return self.headers 
        crequest = CookieRequest('http://'+host+'/')
        # issue XML-RPC request
        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)
        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        self.send_user_agent(h)
        # creating a cookie jar for my cookies
        cj = cookielib.LWPCookieJar()
        self.send_content(h, request_body)
        errcode, errmsg, headers = h.getreply()
        cresponse = CookieResponse(headers)
        cj.extract_cookies(cresponse, crequest)
        if len(cj) >0 and not os.path.exists(self.cookiefile):
            logging.debug("Saving cookies in cookie jar")
            cj.save(self.cookiefile)
        if errcode != 200:
            raise xmlrpclib.ProtocolError(host + handler,
                                          errcode, errmsg,headers)
        self.verbose = verbose
        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None
        return self._parse_response(h.getfile(), sock)

class BugZilla(xmlrpclib.Server):
    def __init__(self, url, verbose = False):
        xmlrpclib.Server.__init__(self, url, CookieAuthXMLRPCTransport(),
                                  verbose = verbose)

    def login(self, username, password):
        self.User.login (dict(login=username,
                              password = password))
