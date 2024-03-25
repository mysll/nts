from urllib.parse import urljoin

import requests

import log
from app.utils import RequestUtils, StringUtils
from config import Config


class MTeam:
    _domain = None
    _indexer_id = None
    _indexer_name = None
    _req = None
    _token = None
    _proxy = None
    _cookie = None
    _api_url = "api/torrent/search"
    _pageurl = "%sdetail/%s"
    _search_url = ""
    _download_url = "/mteam-download?tid=%s"

    def __init__(self, indexer):
        self._indexer_id = indexer.id
        self._indexer_name = indexer.name
        self._cookie = indexer.cookie
        self._domain = indexer.domain
        self._search_url = urljoin(self._domain, self._api_url)
        if indexer.proxy:
            self._proxy = Config().get_proxies()
        self._cookie = indexer.cookie
        self.init_config()

    def init_config(self):
        self.__get_token()
        session = requests.session()
        header = {
            "Content-Type": "application/json; charset=UTF-8",
            "x-api-key": f"{self._token}"
        }
        self._req = RequestUtils(headers=header,
                                 proxies=self._proxy,
                                 session=session,
                                 timeout=10)

    def __get_token(self):
        cookie_dic = RequestUtils.cookie_parse(self._cookie)
        if "token" not in cookie_dic:
            log.warn(f"【INDEXER】{self._indexer_name} 未获取到token")
            return

        self._token = cookie_dic["token"]

    def search(self, keyword, imdb_id=None, page=1):
        if not self._token:
            log.warn(f"【INDEXER】{self._indexer_name} 未获取到token，无法搜索")
            return True, []

        params = {
            "pageNumber": page,
            "pageSize": 100
        }
        if imdb_id:
            params["imdb"] = imdb_id
        else:
            params["keyword"] = keyword

        discount = {"PERCENT_50": 0.5,
                    "FREE": 0.0,
                    "NORMAL": 1.0
                    }
        status = {"NORMAL": 1.0
                  }
        res = self._req.post_res(self._search_url, json=params)
        torrents = []
        if res and res.status_code == 200:
            data = res.json().get('data') or {}
            results = data.get('data') or []
            for result in results:
                status = result.get('status') or {}
                torrent = {
                    'indexer': self._indexer_id,
                    'title': result.get('name'),
                    'description': result.get('smallDescr'),
                    'enclosure': self._download_url % result.get('id'),
                    'pubdate': StringUtils.timestamp_to_date(result.get('createdDate')),
                    'size': StringUtils.str_int(result.get('size')),
                    'seeders': status.get('seeders'),
                    'peers': status.get('leechers'),
                    'downloadvolumefactor': discount.get(status.get('discount'), 1.0),
                    'uploadvolumefactor': status.get(status.get('status'), 1.0),
                    'page_url': self._pageurl % (self._domain, result.get('id')),
                    'imdbid': result.get('imdb')
                }
                torrents.append(torrent)
        elif res is not None:
            log.warn(f"【INDEXER】{self._name} 搜索失败，错误码：{res.status_code}")
            return True, []
        else:
            log.warn(f"【INDEXER】{self._name} 搜索失败，无法连接 {self._domain}")
            return True, []
        return False, torrents
