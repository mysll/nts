import json
import time
from urllib.parse import urljoin
import log
from lxml import etree

from app.helper import ChromeHelper
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

        if site_cookie == "":
            self.error(f"模拟登录失败，cookie 为空")
            return False, f'【{site}】模拟登录失败，cookie 为空'

        cookie_dic = RequestUtils.cookie_parse(site_cookie)
        if "token" not in cookie_dic:
            self.error(f"模拟登录失败，cookie 格式错误,cookie;token=xx")
            return False, f'【{site}】模拟登录失败，cookie 格式错误,cookie;token=xx'

        site_token = cookie_dic["token"]
        ua = site_info.get("ua")
        proxy = Config().get_proxies() if site_info.get("proxy") else None

        req_headers = {}
        req_headers.update({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-api-key": f"{site_token}"
        })

        res = RequestUtils(headers=req_headers,
                           proxies=proxy).post_res(url=urljoin(site_info.get("signurl"), "api/member/profile"))

        user_id = None
        if res is not None and res.status_code == 200:
            ret = res.json()
            user_id = int(ret.get("data", {}).get("id", 0))

        if not user_id:
            return False, f"【{site}】仿真登录失败，无法获取用户ID！"
        # https://xp.m-team.io/profile/detail/300094
        # 首页
        chrome = ChromeHelper()
        if chrome.get_status():
            self.info(f"{site} 开始仿真签到")
            if not chrome.visit(url=urljoin(site_info.get("signurl"), "profile/detail/%d" % user_id),
                                ua=ua,
                                cookie=site_cookie,
                                proxy=proxy):
                self.warn("%s 无法打开网站" % site)
                return False, f"【{site}】仿真登录失败，无法打开网站！"
            time.sleep(10)
            # 获取html
            html_text = chrome.get_html()
            if not html_text:
                self.warn("%s 获取站点源码失败" % site)
                return False, f"【{site}】仿真登录失败，获取站点源码失败！"
            html = etree.HTML(html_text)
            if html:
                last_update = html.xpath('//*[@id="app-content"]/div/div[3]/div/div/div/table/tbody/tr[5]/td[2]')
                if last_update:
                    return True, f'【{site}】仿真登录成功,最近登录时间:{last_update}'

        return False, f'【{site}】模拟登录失败'
