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
        self._token = indexer.token
        self._domain = indexer.domain
        self._search_url = urljoin(self._domain, self._api_url)
        if indexer.proxy:
            self._proxy = Config().get_proxies()
        self.init_config()

    def init_config(self):
        session = requests.session()
        header = {
            "Content-Type": "application/json; charset=UTF-8"
        }
        self._req = RequestUtils(headers=header,
                                 proxies=self._proxy,
                                 session=session,
                                 timeout=10,
                                 api_key=self._token)

    def get_discount(self, discount):
        if discount == "PERCENT_50":
            return 1.0, 0.5
        elif discount == "NORMAL":
            return 1.0, 1.0
        elif discount == "PERCENT_70":
            return 1.0, 0.7
        elif discount == "FREE":
            return 1.0, 0.0
        elif discount == "_2X_FREE":
            return 2.0, 0.0
        elif discount == "_2X":
            return 2.0, 1.0
        elif discount == "_2X_PERCENT_50":
            return 2.0, 0.5

    def search(self, keyword, imdb_id=None, page=1):
        if not self._token:
            log.warn(f"【INDEXER】{self._indexer_name} 未获取到token，无法搜索")
            return True, []

        if page == 0:
            page = 1
        params = {
            "pageNumber": page,
            "pageSize": 100
        }
        if imdb_id:
            params["imdb"] = imdb_id
        elif keyword:
            params["keyword"] = keyword
        res = self._req.post_res(self._search_url, json=params)
        torrents = []
        if res and res.status_code == 200:
            data = res.json().get('data') or {}
            results = data.get('data') or []
            for result in results:
                status = result.get('status') or {}
                up_discount, down_discount = self.get_discount(status.get('discount'))
                torrent = {
                    'indexer': self._indexer_id,
                    'title': result.get('name'),
                    'description': result.get('smallDescr'),
                    'enclosure': self._download_url % result.get('id'),
                    'pubdate': StringUtils.timestamp_to_date(result.get('createdDate')),
                    'size': StringUtils.str_int(result.get('size')),
                    'seeders': status.get('seeders'),
                    'peers': status.get('leechers'),
                    'grabs': status.get("timesCompleted"),
                    'downloadvolumefactor': down_discount,
                    'uploadvolumefactor': up_discount,
                    'page_url': self._pageurl % (self._domain, result.get('id')),
                    'imdbid': (result.get('imdb') or "").replace("http://www.imdb.com/title/", "", -1)
                }
                torrents.append(torrent)
        elif res is not None:
            log.warn(f"【INDEXER】{self._indexer_name} 搜索失败，错误码：{res.status_code}")
            return True, []
        else:
            log.warn(f"【INDEXER】{self._indexer_name} 搜索失败，无法连接 {self._domain}")
            return True, []
        return False, torrents
