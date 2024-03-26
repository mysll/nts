import json
from urllib.parse import urljoin
import log
from lxml import etree

from app.plugins.modules._autosignin._base import _ISiteSigninHandler
from app.utils import StringUtils, RequestUtils
from config import Config


class MTeam(_ISiteSigninHandler):
    """
    MTEAM签到
    """
    # 匹配的站点Url，每一个实现类都需要设置为自己的站点Url
    site_url = "m-team.io"

    @classmethod
    def match(cls, url):
        """
        根据站点Url判断是否匹配当前站点签到类，大部分情况使用默认实现即可
        :param url: 站点Url
        :return: 是否匹配，如匹配则会调用该类的signin方法
        """
        return True if StringUtils.site_equal(url, cls.site_url) else False

    def signin(self, site_info: dict):
        """
        执行签到操作
        :param site_info: 站点信息，含有站点Url、站点Cookie、UA等信息
        :return: 签到结果信息
        """
        site = site_info.get("name")
        site_cookie = site_info.get("cookie")
        ua = site_info.get("ua")
        if site_cookie == "":
            self.error(f"模拟登录失败，cookie 为空")
            return False, f'【{site}】模拟登录失败，cookie 为空'

        cookie_dic = RequestUtils.cookie_parse(site_cookie)
        if "token" not in cookie_dic:
            self.error(f"模拟登录失败，cookie 格式错误,cookie;token=xx")
            return False, f'【{site}】模拟登录失败，cookie 格式错误,cookie;token=xx'

        site_token = cookie_dic["token"]

        proxy = Config().get_proxies() if site_info.get("proxy") else None

        req_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-api-key": f"{site_token}",
            "User-Agent": f"{ua}"
        }

        res = RequestUtils(cookies=site_cookie,
                           headers=req_headers,
                           referer=site_info.get("signurl"),
                           proxies=proxy).post_res(url=urljoin(site_info.get("signurl"), "api/member/updateLastBrowse"))

        if res is not None and res.status_code == 200:
            ret = res.json()
            if ret.get("message") == "SUCCESS":
                return True, f'【{site}】模拟登录成功'

        return False, f'【{site}】模拟登录失败'
