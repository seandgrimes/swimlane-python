"""Core Swimlane driver/client class"""

import re

import requests
from pyuri import URI
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves.urllib.parse import urljoin

from swimlane.core.resources import SwimlaneResolver
from swimlane.core.resources.app import AppAdapter
from swimlane.core.resources.usergroup import GroupAdapter, UserAdapter
from swimlane.errors import SwimlaneHTTP400Error

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Swimlane(object):
    """Swimlane API client"""

    _api_root = '/api/'

    def __init__(self, host, username, password, verify_ssl=True):
        self.host = URI(host)
        self.host.scheme = self.host.scheme or 'https'
        self.host.path = None

        self.__settings = None
        self.__user = None

        self._session = requests.Session()
        self._session.verify = verify_ssl
        self._session.headers.update({
            'Content-Type': 'application/json'
        })
        self._session.auth = SwimlaneAuth(
            self,
            username,
            password
        )

        self.apps = AppAdapter(self)
        self.users = UserAdapter(self)
        self.groups = GroupAdapter(self)

    def __repr__(self):
        return '<{cls}: {username} @ {host}>'.format(
            cls=self.__class__.__name__,
            username=self._session.auth.username,
            host=self.host
        )

    def request(self, method, api_endpoint, **kwargs):
        """Shortcut helper for sending requests to API

        Handles generating full API URL, session reuse and auth, and response status code

        Raises HTTPError on 4xx/5xx HTTP responses, or Swimlane400Error on 400 responses with well-formatted additional
        context information about the exception
        """
        while api_endpoint.startswith('/'):
            api_endpoint = api_endpoint[1:]

        response = self._session.request(method, urljoin(str(self.host) + self._api_root, api_endpoint), **kwargs)

        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            if error.response.status_code == 400:
                raise SwimlaneHTTP400Error(error)
            else:
                raise error

        return response

    @property
    def settings(self):
        """Retrieve and cache settings from server"""
        if not self.__settings:
            self.__settings = self.request('get', 'settings').json()
        return self.__settings

    @property
    def version(self):
        """Returns server API version"""
        return self.settings['apiVersion']

    @property
    def user(self):
        """Returns User record for authenticated user"""
        if not self.__user:
            self.__user = self.users.get(username=self._session.auth.username)
        return self.__user

    def _compare_version(self, *version_sections):
        """Return direction of Swimlane version relative to provided version sections
        
        If Swimlane version is equal to provided version, return 0
        If Swimlane version is greater than provided version, return 1
        If Swimlane version is less than provided version, return -1
        
        e.g. with Swimlane version = 2.13.2-173414
            _compare_version(2) = 0
            _compare_version(1) = 1
            _compare_version(3) = -1
            
            _compare_version(2, 13) = 0
            _compare_version(2, 12) = 1
            _compare_version(2, 14) = -1
            
            _compare_version(2, 13, 3) = -1
            
            _compare_version(2, 13, 2, 173415) = -1
        """
        sections_provided = len(version_sections)

        versions = tuple(re.findall(r'\d+', self.version)[0:sections_provided])

        return (versions > version_sections) - (versions < version_sections)


class SwimlaneAuth(SwimlaneResolver):

    def __init__(self, swimlane, username, password):
        super(SwimlaneAuth, self).__init__(swimlane)
        self.username = username
        self.password = password

        self._login_headers = self.authenticate()

    def __call__(self, request):

        request.headers.update(self._login_headers)

        return request

    def authenticate(self):
        """Send login request and return login token"""
        # Explicitly provide verify argument, appears to not consistently be acknowledged across versions during
        # initial setup for auth
        resp = self._swimlane.request(
            'post',
            'user/login',
            json={
                'userName': self.username,
                'password': self.password,
                'domain': ''
            },
            verify=self._swimlane._session.verify
        )
        json_content = resp.json()

        # Check for token in response content
        token = json_content.get('token')

        if token is None:
            # Legacy cookie authentication (2.13-)
            headers = {'Cookie': ';'.join(
                ["%s=%s" % cookie for cookie in resp.cookies.items()]
            )}
        else:
            # JWT auth (2.14+)
            headers = {
                'Authorization': 'Bearer {}'.format(token)
            }

        return headers
