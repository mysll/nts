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
        return 'M-Team' in html_text

    def parse(self):
        self._parse_favicon(self._index_html)
        if not self._parse_logged_in(""):
            return
        self._parse_site_page("")
        self._parse_user_base_info(
            self._get_page_content(urljoin(self._base_url, self._user_detail_page), params={"uid": self.userid}))
        self._parse_seeding_pages()
        self.seeding_info = json.dumps(self.seeding_info)

    def _parse_site_page(self, html_text):
        self._user_detail_page = "api/member/profile"
        self._torrent_seeding_page = "api/member/getUserTorrentList"

    def _parse_seeding_pages(self):
        header = {"Content-Type": "application/json; charset=UTF-8"}
        req = {"userid": self.userid, "type": "SEEDING", "pageSize": 100, "pageNumber": 1}

        # 第一页
        next_page = self._parse_user_torrent_seeding_info(
            self._get_page_content(urljoin(self._base_url, self._torrent_seeding_page),
                                   params=json.dumps(req),
                                   headers=header))

        while next_page:
            req["pageNumber"] = next_page
            next_page = self._parse_user_torrent_seeding_info(
                self._get_page_content(urljoin(urljoin(self._base_url, self._torrent_seeding_page), next_page),
                                       self._torrent_seeding_params,
                                       self._torrent_seeding_headers),
                multi_page=True)

    def _parse_logged_in(self, html_text):
        if self._site_cookie == "":
            log.warn(f"【Sites】{self.site_name} cookie is null")
            return False

        cookie_dic = RequestUtils.cookie_parse(self._site_cookie)
        if "token" not in cookie_dic or "user_id" not in cookie_dic:
            log.warn(f"【Sites】{self.site_name} token or user_id is null")
            return False

        self._token = cookie_dic["token"]
        self.userid = cookie_dic["user_id"]
        return True

    def _parse_user_base_info(self, html_text):
        user = json.loads(html_text) or {}
        if user.get("message") != "SUCCESS":
            return

        lvl = {"0": "Peasant",
               "1": "User",
               "2": "Power User",
               "3": "Elite User",
               "4": "Crazy User",
               "5": "Insane User",
               "6": "Veteran User",
               "7": "Extreme User",
               "8": "Ultimate User",
               "9": "Nexus Master"}
        data = user.get("data")
        self.username = data.get("username")
        self.user_level = lvl.get(data.get("role")) or "unknown"
        self.join_at = StringUtils.unify_datetime_str(data.get("createdDate"))
        member_count = data.get("memberCount")
        self.upload = member_count.get("uploaded")
        self.download = member_count.get("downloaded")
        self.ratio = member_count.get("shareRate")
        self.bonus = member_count.get("bonus")

    def _parse_user_traffic_info(self, html_text):
        pass

    def _parse_user_detail_info(self, html_text):
        return None

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
        if not multi_page:
            self.seeding_info = []
            self.seeding_size = 0
        res = json.loads(html_text) or {}
        if res.get("message") != "SUCCESS":
            return None
        data = res.get("data") or {}
        next_page = None
        if data.get("totalPages") != "1":
            next_page = StringUtils.str_int(res.get("pageNumber") or 1) + 1

        self.seeding = StringUtils.str_int(data.get("total") or 0)

        torrents = data.get("data") or []
        page_seeding_info = []
        seeding_size = 0
        for torrent in torrents:
            obj = torrent.get("torrent") or {}
            size = StringUtils.str_int(obj.get("size") or 0)
            seeders = StringUtils.str_int((obj.get("status") or {}).get("seeders"))
            page_seeding_info.append([seeders, size])
            seeding_size += size

        self.seeding_info.extend(page_seeding_info)
        self.seeding_size += seeding_size
        return next_page

    def _get_page_content(self, url, params=None, headers=None):
        # x-api-key
        req_headers = {}
        req_headers.update({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-api-key": f"{self._token}"
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
            res = RequestUtils(session=self._session,
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
