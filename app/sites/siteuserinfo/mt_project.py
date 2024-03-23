# -*- coding: utf-8 -*-
import json
import re

import log
from app.sites.siteuserinfo._base import _ISiteUserInfo, SITE_BASE_ORDER
from app.utils import StringUtils
from urllib.parse import urljoin, urlsplit
from app.utils.types import SiteSchema
from app.utils import RequestUtils
from config import Config


class MTeamSiteUserInfo(_ISiteUserInfo):
    schema = SiteSchema.MTeam
    order = SITE_BASE_ORDER + 60

    @classmethod
    def match(cls, html_text):
        return 'Powered by mTorrent' in html_text

    def parse(self):
        self._parse_favicon(self._index_html)
        if not self._parse_logged_in(""):
            return
        self._parse_site_page("")
        self._parse_user_base_info(self._get_page_content(urljoin(self._base_url, self._user_detail_page)))

        
    def _parse_site_page(self, html_text):
        self._user_detail_page = "api/member/profile"
        self._torrent_seeding_page = "api/member/getUserTorrentList"
        
    def _parse_logged_in(self, html_text):
        if self._site_cookie == "":
            log.warn(f"【Sites】{self.site_name} cookie is null")
            return False

        cookie_dic = RequestUtils.cookie_parse(self._site_cookie)
        if "token" not in cookie_dic or "user_id" not in cookie_dic:
            log.warn(f"【Sites】{self.site_name} token or user_id is null")
            return False

        self._site_cookie = cookie_dic["token"]
        self.userid = cookie_dic["user_id"]
        return True

    def _parse_user_base_info(self, html_text):
        user = json.load(html_text) or {}
        if user.get("message") != "SUCCESS":
            return

        data = user.get("data")
        self.username = data.get("username")
        member_count = data.get("memberCount")
        self.upload = member_count.get("uploaded")
        self.download = member_count.get("downloaded")
        self.ratio = member_count.get("shareRate")
        self.bonus = member_count.get("bonus")


    def _parse_user_detail_info(self, html_text):
        pass

    def _parse_message_unread_links(self, html_text, msg_links):
        return None

    def _parse_message_content(self, html_text):
        return None, None, None

    def _parse_user_torrent_seeding_info(self, html_text, multi_page=False):
        """
        解析用户的做种相关信息
        :param html_text:
        :param multi_page: 是否多页数据
        :return: 下页地址
        """
        # {"userid":"300094","type":"SEEDING","pageNumber":1,"pageSize":20}
        pass

    def _get_page_content(self, url, params=None, headers=None):
        #x-api-key
        req_headers = {}
        req_headers.update({
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-api-key": f"{self._site_cookie}"
                })
        proxies = Config().get_proxies() if self._proxy else None
        if headers or self._addition_headers:
            if headers:
                req_headers.update(headers)

            if self._addition_headers:
                req_headers.update(self._addition_headers)

        if params:
            res = RequestUtils(session=self._session,
                               timeout=60,
                               proxies=proxies,
                               headers=req_headers).post_res(url=url, data=params)
        else:
            res = RequestUtils(cookies=self._site_cookie,
                               session=self._session,
                               timeout=60,
                               proxies=proxies,
                               headers=req_headers).get_res(url=url)
        
        if res is not None and res.status_code in (200, 500, 403):
            if "charset=utf-8" in res.text or "charset=UTF-8" in res.text:
                res.encoding = "UTF-8"
            else:
                res.encoding = res.apparent_encoding
            return res.text

        return ""