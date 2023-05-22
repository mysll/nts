from app.helper import DbHelper
from app.plugins.plugin_manager import PluginManager
from app.sync import Sync
from config import PT_TRANSFER_INTERVAL, Config
import log
from werkzeug.security import check_password_hash
from app.conf import ModuleConf
from app.torrentremover import TorrentRemover


class User:
    """
    用户
    """
    dbhelper = None
    admin_users = []

    def __init__(self, user=None):
        self.dbhelper = DbHelper()
        if user:
            self.id = user.get('id')
            self.username = user.get('name')
            self.password_hash = user.get('password')
            self.pris = user.get('pris')
            self.is_active = True
            self.is_authenticated = True
            self.level = 2
            self.admin = 1 if self.id == 0 else 0
        self.admin_users = [{
            "id": 0,
            "name": Config().get_config('app').get('login_user'),
            "password": Config().get_config('app').get('login_password')[6:],
            "pris": "我的媒体库,资源搜索,探索,站点管理,订阅管理,下载管理,媒体整理,服务,系统设置"
        }]

    def verify_password(self, password):
        """
        验证密码
        """
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def add_user(self, name, password, pris):
        self.dbhelper.insert_user(name, password, pris)
        return 1 if self.get_user(name) is not None else 0

    def delete_user(self, name):
        self.dbhelper.delete_user(name)
        return 1 if self.get_user(name) is None else 0

    def check_user(self, size, params):
        return True, ""

    def get_authsites(self):
        return {}

    def get_topmenus(self):
        return str(self.pris).split(",")

    def get_services(self):
        scheduler_cfg_list = {}
        pt = Config().get_config('pt')
        if pt:
            # RSS订阅
            pt_check_interval = pt.get('pt_check_interval')
            if str(pt_check_interval).isdigit():
                tim_rssdownload = str(
                    round(int(pt_check_interval) / 60)) + " 分钟"
                rss_state = 'ON'
            else:
                tim_rssdownload = ""
                rss_state = 'OFF'
            svg = '''
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-cloud-download" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path d="M19 18a3.5 3.5 0 0 0 0 -7h-1a5 4.5 0 0 0 -11 -2a4.6 4.4 0 0 0 -2.1 8.4"></path>
                    <line x1="12" y1="13" x2="12" y2="22"></line>
                    <polyline points="9 19 12 22 15 19"></polyline>
                </svg>
            '''

            scheduler_cfg_list['rssdownload'] = {'name': 'RSS订阅', 'time': tim_rssdownload, 'state': rss_state, 'id': 'rssdownload', 'svg': svg,
                                                 'color': "blue"}

            search_rss_interval = pt.get('search_rss_interval')
            if str(search_rss_interval).isdigit():
                if int(search_rss_interval) < 6:
                    search_rss_interval = 6
                tim_rsssearch = str(int(search_rss_interval)) + " 小时"
                rss_search_state = 'ON'
            else:
                tim_rsssearch = ""
                rss_search_state = 'OFF'

            svg = '''
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-search" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <circle cx="10" cy="10" r="7"></circle>
                    <line x1="21" y1="21" x2="15" y2="15"></line>
                </svg>
            '''

            scheduler_cfg_list['subscribe_search_all'] = {'name': '订阅搜索', 'time': tim_rsssearch, 'state': rss_search_state, 'id': 'subscribe_search_all',
                                                          'svg': svg, 'color': "blue"}

            # 下载文件转移
            pt_monitor = pt.get('pt_monitor')
            if pt_monitor:
                tim_pttransfer = str(round(PT_TRANSFER_INTERVAL / 60)) + " 分钟"
                sta_pttransfer = 'ON'
            else:
                tim_pttransfer = ""
                sta_pttransfer = 'OFF'
            svg = '''
            <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-replace" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                <rect x="3" y="3" width="6" height="6" rx="1"></rect>
                <rect x="15" y="15" width="6" height="6" rx="1"></rect>
                <path d="M21 11v-3a2 2 0 0 0 -2 -2h-6l3 3m0 -6l-3 3"></path>
                <path d="M3 13v3a2 2 0 0 0 2 2h6l-3 -3m0 6l3 -3"></path>
            </svg>
            '''
            scheduler_cfg_list['pttransfer'] = {'name': '下载文件转移', 'time': tim_pttransfer, 'state': sta_pttransfer, 'id': 'pttransfer', 'svg': svg,
                                                'color': "green"}

            # 删种
            torrent_remove_tasks = TorrentRemover().get_torrent_remove_tasks()
            if torrent_remove_tasks:
                sta_autoremovetorrents = 'ON'
                svg = '''
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <line x1="4" y1="7" x2="20" y2="7"></line>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                    <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path>
                    <path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path>
                </svg>
                '''
                scheduler_cfg_list['autoremovetorrents'] = {'name': '自动删种', 'state': sta_autoremovetorrents,
                                                            'id': 'autoremovetorrents', 'svg': svg, 'color': "twitter"}

            # 自动签到
            tim_ptsignin = pt.get('ptsignin_cron')
            if tim_ptsignin:
                if str(tim_ptsignin).find(':') == -1:
                    tim_ptsignin = "%s 小时" % tim_ptsignin
                sta_ptsignin = 'ON'
                svg = '''
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-user-check" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2"></path>
                    <path d="M16 11l2 2l4 -4"></path>
                </svg>
                '''
                scheduler_cfg_list['ptsignin'] = {'name': '站点签到', 'time': tim_ptsignin, 'state': sta_ptsignin, 'id': 'ptsignin', 'svg': svg,
                                                  'color': "facebook"}

        # 目录同步
        sync_paths = Sync().get_sync_path_conf()
        if sync_paths:
            sta_sync = 'ON'
            svg = '''
            <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-refresh" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4"></path>
                    <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"></path>
            </svg>
            '''
            scheduler_cfg_list['sync'] = {'name': '目录同步', 'time': '实时监控', 'state': sta_sync, 'id': 'sync', 'svg': svg,
                                                          'color': "orange"}

        # 清理文件整理缓存
        svg = '''
        <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-eraser" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
        <path d="M19 20h-10.5l-4.21 -4.3a1 1 0 0 1 0 -1.41l10 -10a1 1 0 0 1 1.41 0l5 5a1 1 0 0 1 0 1.41l-9.2 9.3"></path>
        <path d="M18 13.3l-6.3 -6.3"></path>
        </svg>
        '''
        scheduler_cfg_list['blacklist'] = {
            'name': '清理转移缓存', 'time': '手动', 'state': 'OFF', 'id': 'blacklist', 'svg': svg, 'color': 'red'}

        # 清理RSS缓存
        svg = '''
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-eraser" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                <path d="M19 20h-10.5l-4.21 -4.3a1 1 0 0 1 0 -1.41l10 -10a1 1 0 0 1 1.41 0l5 5a1 1 0 0 1 0 1.41l-9.2 9.3"></path>
                <path d="M18 13.3l-6.3 -6.3"></path>
                </svg>
                '''
        scheduler_cfg_list['rsshistory'] = {
            'name': '清理RSS缓存', 'time': '手动', 'state': 'OFF', 'id': 'rsshistory', 'svg': svg, 'color': 'purple'}

        # 名称识别测试
        svg = '''
        <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-alphabet-greek" width="40" height="40" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
        <path d="M10 10v7"></path>
        <rect x="5" y="10" width="5" height="7" rx="2"></rect>
        <path d="M14 20v-11a2 2 0 0 1 2 -2h1a2 2 0 0 1 2 2v1a2 2 0 0 1 -2 2a2 2 0 0 1 2 2v1a2 2 0 0 1 -2 2"></path>
        </svg>
        '''
        scheduler_cfg_list['nametest'] = {
            'name': '名称识别测试', 'time': '', 'state': 'OFF', 'id': 'nametest', 'svg': svg, 'color': 'lime'}

        # 过滤规则测试
        svg = '''
        <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-adjustments-horizontal" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
        <circle cx="14" cy="6" r="2"></circle>
        <line x1="4" y1="6" x2="12" y2="6"></line>
        <line x1="16" y1="6" x2="20" y2="6"></line>
        <circle cx="8" cy="12" r="2"></circle>
        <line x1="4" y1="12" x2="6" y2="12"></line>
        <line x1="10" y1="12" x2="20" y2="12"></line>
        <circle cx="17" cy="18" r="2"></circle>
        <line x1="4" y1="18" x2="15" y2="18"></line>
        <line x1="19" y1="18" x2="20" y2="18"></line>
        </svg>
        '''
        scheduler_cfg_list['ruletest'] = {
            'name': '过滤规则测试', 'time': '', 'state': 'OFF', 'id': 'ruletest', 'svg': svg, 'color': 'yellow'}

        # 网络连通性测试
        svg = '''
        <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-network" width="40" height="40" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
        <circle cx="12" cy="9" r="6"></circle>
        <path d="M12 3c1.333 .333 2 2.333 2 6s-.667 5.667 -2 6"></path>
        <path d="M12 3c-1.333 .333 -2 2.333 -2 6s.667 5.667 2 6"></path>
        <path d="M6 9h12"></path>
        <path d="M3 19h7"></path>
        <path d="M14 19h7"></path>
        <circle cx="12" cy="19" r="2"></circle>
        <path d="M12 15v2"></path>
        </svg>
        '''
        targets = ModuleConf.NETTEST_TARGETS
        scheduler_cfg_list['nettest'] = {'name': '网络连通性测试', 'time': '', 'state': 'OFF', 'id': 'nettest', 'svg': svg, 'color': 'cyan',
                                         "targets": targets}

        # 备份
        svg = '''
        <svg t="1660720525544" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1559" width="16" height="16">
        <path d="M646 1024H100A100 100 0 0 1 0 924V258a100 100 0 0 1 100-100h546a100 100 0 0 1 100 100v31a40 40 0 1 1-80 0v-31a20 20 0 0 0-20-20H100a20 20 0 0 0-20 20v666a20 20 0 0 0 20 20h546a20 20 0 0 0 20-20V713a40 40 0 0 1 80 0v211a100 100 0 0 1-100 100z" fill="#ffffff" p-id="1560"></path>
        <path d="M924 866H806a40 40 0 0 1 0-80h118a20 20 0 0 0 20-20V100a20 20 0 0 0-20-20H378a20 20 0 0 0-20 20v8a40 40 0 0 1-80 0v-8A100 100 0 0 1 378 0h546a100 100 0 0 1 100 100v666a100 100 0 0 1-100 100z" fill="#ffffff" p-id="1561"></path>
        <path d="M469 887a40 40 0 0 1-27-10L152 618a40 40 0 0 1 1-60l290-248a40 40 0 0 1 66 30v128a367 367 0 0 0 241-128l94-111a40 40 0 0 1 70 35l-26 109a430 430 0 0 1-379 332v142a40 40 0 0 1-40 40zM240 589l189 169v-91a40 40 0 0 1 40-40c144 0 269-85 323-214a447 447 0 0 1-323 137 40 40 0 0 1-40-40v-83z" fill="#ffffff" p-id="1562"></path>
        </svg>
        '''
        scheduler_cfg_list['backup'] = {
            'name': '备份&恢复', 'time': '', 'state': 'OFF', 'id': 'backup', 'svg': svg, 'color': 'green'}

        return scheduler_cfg_list

    def get_id(self):
        """
        获取用户ID
        """
        return self.id

    def get(self, user_id):
        """
        根据用户ID获取用户实体，为 login_user 方法提供支持
        """
        if user_id is None:
            return None
        for user in self.admin_users:
            if user.get('id') == user_id:
                return User(user)
        for user in self.dbhelper.get_users():
            if not user:
                continue
            if user.ID == user_id:
                return User({"id": user.ID, "name": user.NAME, "password": user.PASSWORD, "pris": user.PRIS})
        return None

    def get_user(self, user_name):
        """
        根据用户名获取用户对像
        """
        for user in self.admin_users:
            if user.get("name") == user_name:
                return User(user)
        for user in self.dbhelper.get_users():
            if user.NAME == user_name:
                return User({"id": user.ID, "name": user.NAME, "password": user.PASSWORD, "pris": user.PRIS})
        return None

    def get_users(self):
        res = []
        for user in self.dbhelper.get_users():
            res.append(User({"id": user.ID, "name": user.NAME,
                       "password": user.PASSWORD, "pris": user.PRIS}))
        return res
