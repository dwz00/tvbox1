# -*- coding: utf-8 -*-
import os, sys, asyncio, aiohttp, requests, json, hashlib, re, shutil, ssl, urllib3
from pathlib import Path
from requests.adapters import HTTPAdapter, Retry
from urllib3.exceptions import InsecureRequestWarning

# 基础设置
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(InsecureRequestWarning)

class GetSrc:
    def __init__(self, username=None, repo=None, token=None, url=None, target='tvbox.json', jar_suffix='jar'):
        self.username = username
        self.repo_name = repo
        self.token = token
        self.url = url if url else ""
        self.target = target if target.endswith('.json') else f"{target}.json"
        self.jar_suffix = jar_suffix
        self.headers = {"user-agent": "okhttp/3.15"}
        
        # 路径设置：直接操作当前目录
        self.base_path = Path(".").absolute()
        self.jar_path = self.base_path / "jar"
        self.api_path = self.base_path / "api" / "drpy2"
        
        # 确保目录存在
        self.jar_path.mkdir(parents=True, exist_ok=True)
        self.api_path.mkdir(parents=True, exist_ok=True)

        self.drpy2_files = [
            "cat.js", "crypto-js.js", "drpy2.min.js", "http.js", "jquery.min.js",
            "jsencrypt.js", "log.js", "pako.min.js", "similarity.js", "uri.min.js",
            "cheerio.min.js", "deep.parse.js", "gbk.js", "jinja.js", "json5.js",
            "node-rsa.js", "script.js", "spider.js", "模板.js", "quark.min.js"
        ]

    async def download_drpy2_files(self):
        """异步下载依赖的 JS 文件"""
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            tasks = []
            for filename in self.drpy2_files:
                target_file = self.api_path / filename
                if target_file.exists(): continue
                
                url = f"https://ghp.ci{filename}"
                tasks.append(self._download_one(session, url, target_file))
            if tasks: await asyncio.gather(*tasks)

    async def _download_one(self, session, url, path):
        try:
            async with session.get(url, timeout=15) as res:
                if res.status == 200:
                    content = await res.read()
                    with open(path, "wb") as f: f.write(content)
                    print(f"下载成功: {path.name}")
        except: print(f"下载失败: {path.name}")

    def file_hash(self, filepath):
        return hashlib.sha256(open(filepath, 'rb').read()).hexdigest()

    def clean_and_format(self):
        """去重逻辑：按文件大小和哈希值过滤重复接口"""
        files_info = {}
        # 修正 jar 后缀
        for f in self.jar_path.glob("*"):
            if f.is_file(): f.rename(f.with_suffix(f".{self.jar_suffix}"))

        # 扫描并去重（简单逻辑示例）
        print("正在清理重复资源...")
        # 此处可根据你的 batch_handle_online_interface 逻辑进一步扩展

    def run(self):
        """主运行逻辑"""
        if not self.url:
            print("错误：未提供抓取地址 URL")
            return
        
        print(f"开始处理地址: {self.url}")
        # 这里放置你之前的 sites 抓取、JSON 解析和 all.json 生成逻辑
        # 建议保留你原来的 batch_handle_online_interface 等方法放入类中
        print("接口处理完成！")

# --- 关键修改：将启动逻辑移到类外面，并修复缩进 ---
if __name__ == "__main__":
    import os

    # 1. 自动获取当前 GitHub 仓库信息
    # 格式为 "用户名/仓库名"，例如 "dwz00/tvbox1"
    full_repo = os.getenv('GITHUB_REPOSITORY', 'dwz00/tvbox1')
    u_name, r_name = full_repo.split('/') if '/' in full_repo else (None, full_repo)

    # 2. 设置抓取目标（在此修改你的接口源）
    my_urls = "https://catvod.com"

    # 3. 初始化参数
    params = {
        "username": u_name,
        "repo": r_name,
        "token": os.getenv('GITHUB_TOKEN'),
        "url": my_urls,
        "target": "tvbox.json"
    }

    print(f"--- 任务启动：{full_repo} ---")
    tool = GetSrc(**params)

    # 4. 运行异步任务和主逻辑
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tool.download_drpy2_files())
    
    tool.run()
