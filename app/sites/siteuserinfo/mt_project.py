# -*- coding: utf-8 -*-
import json
import re

from app.sites.siteuserinfo._base import _ISiteUserInfo, SITE_BASE_ORDER
from app.utils import StringUtils
from app.utils.types import SiteSchema


class MTeamSiteUserInfo(_ISiteUserInfo):
    schema = SiteSchema.MTeam
    order = SITE_BASE_ORDER + 60

    @classmethod
    def match(cls, html_text):
        return 'Powered by mTorrent' in html_text

    def _parse_site_page(self, html_text):
        html_text = self._prepare_html_text(html_text)

        user_detail = re.search(r"/profile/detail/(\d+)", html_text)
        if user_detail and user_detail.group().strip():
            self._user_detail_page = user_detail.group().strip().lstrip('/')
            self.userid = user_detail.group(1)
            self._torrent_seeding_page = "api/member/getUserTorrentList"

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
