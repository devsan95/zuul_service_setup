#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright 2023 Nokia
# Copyright 2023 Santoshkumar Vagga
# Copyright 2023 BGL 5G SCM Team

"""
A module to do gerrit rest operation.
"""

import json
from urllib.parse import urljoin

import requests


class GerritRestClient:
    def __init__(self, url, user, pwd, auth=None):
        self.server_url = url
        if not self.server_url.endswith("/"):
            self.server_url = self.server_url + "/"
        self.user = user
        self.pwd = pwd
        self.auth = requests.auth.HTTPDigestAuth
        if auth == "basic":
            self.change_to_basic_auth()
        self.session = requests.Session()

    def change_to_basic_auth(self):
        self.auth = requests.auth.HTTPBasicAuth

    def get_auth(self):
        if self.user:
            return self.auth(self.user, self.pwd)
        return None

    def get_rest_url(self, path_):
        if path_.startswith("/"):
            path_ = path_[1:]
        if self.user:
            url_ = urljoin(self.server_url, "a/")
            url_ = urljoin(url_, path_)
        else:
            url_ = urljoin(self.server_url, path_)
        return url_

    @staticmethod
    def parse_rest_response(response):
        content = response.content
        content = content.split(b"\n", 1)[1]
        return json.loads(content)

    def add_ssh_key(self, account, pub_key):
        auth = self.get_auth()
        _url = f"accounts/{account}/sshkeys"
        rest_url = self.get_rest_url(_url)
        ret = self.session.post(rest_url, data=pub_key, auth=auth)
        if not ret.ok:
            raise Exception(
                 f"In add_ssh_key to account [{account}] failed.\n\
                  Status code is [{ret.status_code}], Content is [{ret.content}]")  # nopep8

    def list_ssh_key(self, account):
        auth = self.get_auth()
        _url = f"accounts/{account}/sshkeys"
        rest_url = self.get_rest_url(_url)
        ret = self.session.get(rest_url, auth=auth)
        if not ret.ok:
            raise Exception(
                f"In add_ssh_key to account [{account}] failed.\n\
                 Status code is [{ret.status_code}], Content is [{ret.content}]")  # nopep8
        result = self.parse_rest_response(ret)
        return result
