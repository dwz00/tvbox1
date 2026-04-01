# -*- coding: utf-8 -*-
import os, asyncio, aiohttp, requests, json, hashlib, ssl, urllib3, commentjson
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GetSrc:
    def __init__(self, username, repo, token, url, target='tvbox.json'):
        self.username = username
        self.repo_name = repo
        self.token = token
        # 确保 url 是字符串且不为空
        self.url = str(url) if url else ""
        self.target = target
        self.base_path = Path(".").absolute()
        self.jar_path = self.base_path / "jar"
        self.api_path = self.base_path / "api" / "drpy2"
        self.jar_path.mkdir(parents=True, exist_ok=True)
        self.api_path.mkdir(parents=True, exist_ok=True)
        self.s = requests.Session()

    async def download_drpy2_files(self):
        """同步核心 JS 依赖"""
        files = ["drpy2.min.js", "jquery.min.js", "crypto-js.js", "spider.js"] # 简化列表测试
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            for f_name in files:
                target = self.api_path / f_name
                if target.exists(): continue
                # 直接用 GitHub 官方地址，Actions 访问很快
                raw_url = f"https://githubusercontent.com{f_name}"
                try:
                    async with session.get(raw_url, timeout=15) as res:
                        if res.status == 200:
                            with open(target, "wb") as f: f.write(await res.read())
                            print(f"已同步: {f_name}")
                except: print(f"同步失败: {f_name}")

    def run(self):
        if not self.url or "http" not in self.url:
            print(f"无效的 URL 地址: {self.url}")
            return

        all_sites = []
        # 分隔多个地址
        urls = [u.strip() for u in self.url.split(',') if u.strip()]
        
        last_spider = ""
        for u in urls:
            print(f"正在抓取: {u}")
            try:
                res = self.s.get(u, timeout=15, verify=False)
                # 使用 commentjson 解析
                data = commentjson.loads(res.text)
                
                # 简单站点去重
                sites = data.get('sites', [])
                for s in sites:
                    if s.get('api') and not any(x.get('api') == s.get('api') for x in all_sites):
                        all_sites.append(s)
                
                if data.get('spider'): last_spider = data.get('spider')
            except Exception as e:
                print(f"抓取失败 {u}: {e}")

        # 构造最终 JSON
        config = {
            "spider": last_spider,
            "sites": all_sites,
            "lives": [{"name": "直播", "type": 0, "url": "https://ghproxy.com"}]
        }

        # --- 核心：写入文件 ---
        with open(self.base_path / self.target, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
        with open(self.base_path / "all.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 成功生成文件！总计 {len(all_sites)} 个站点。")

if __name__ == "__main__":
    # 自动识别仓库信息
    full_repo = os.getenv('GITHUB_REPOSITORY', 'dwz00/tvbox1')
    u_name, r_name = full_repo.split('/')
    
    # 这里填入你的真实接口源（一定要是 .json 或 .txt 结尾的直连地址）
    my_api_url = "https://catvod.com" 

    tool = GetSrc(u_name, r_name, os.getenv('GITHUB_TOKEN'), my_api_url)
    
    # 运行
    asyncio.run(tool.download_drpy2_files())
    tool.run()
