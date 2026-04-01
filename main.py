# -*- coding: utf-8 -*-
import os, asyncio, aiohttp, requests, json, hashlib, ssl, urllib3, commentjson
from pathlib import Path
# 在 GetSrc 类的 __init__ 中修改：
self.base_path = Path(os.getcwd()) # 强制获取当前执行路径
self.jar_path = self.base_path / "jar"
self.api_path = self.base_path / "api" / "drpy2"

# 确保文件夹真的创建了
os.makedirs(self.jar_path, exist_ok=True)
os.makedirs(self.api_path, exist_ok=True)

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
        urls = [u.strip() for u in self.url.split(',') if u.strip()]
        last_spider_name = ""

        for u in urls:
            print(f"正在抓取: {u}")
            try:
                res = self.s.get(u, timeout=15, verify=False)
                data = commentjson.loads(res.text)
                
                # --- 1. 处理并本地化 Spider (Jar) ---
                remote_spider = data.get('spider', '')
                if remote_spider and remote_spider.startswith('http'):
                    jar_hash = hashlib.md5(remote_spider.encode()).hexdigest()
                    jar_name = f"{jar_hash}.{self.jar_suffix}"
                    local_jar_file = self.jar_path / jar_name
                    
                    if not local_jar_file.exists():
                        print(f"正在下载远程 Jar: {remote_spider}")
                        try:
                            jar_res = self.s.get(remote_spider, timeout=20, verify=False)
                            with open(local_jar_file, 'wb') as f:
                                f.write(jar_res.content)
                            last_spider_name = jar_name
                        except:
                            print(f"Jar 下载失败: {remote_spider}")
                    else:
                        last_spider_name = jar_name

                # --- 2. 站点去重 ---
                sites = data.get('sites', [])
                for s in sites:
                    if s.get('api') and not any(x.get('api') == s.get('api') for x in all_sites):
                        all_sites.append(s)
            except Exception as e:
                print(f"抓取失败 {u}: {e}")

        # --- 3. 生成指向本仓库的私有化地址 (修复了 raw 链接格式) ---
        if last_spider_name:
            my_spider_url = f"https://githubusercontent.com{self.username}/{self.repo_name}/main/jar/{last_spider_name}"
        else:
            my_spider_url = ""

        # --- 4. 构造最终配置 (合并直播源) ---
        config = {
            "spider": my_spider_url,
            "sites": all_sites,
            "lives": [{"name": "直播", "type": 0, "url": "https://githubusercontent.comssili126/tv/main/itvlist.txt"}]
        }

        # --- 5. 统一写入文件 ---
        for filename in [self.target, "all.json"]:
            with open(self.base_path / filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 处理成功！")
        print(f"新的 Spider 地址: {my_spider_url}")
        print(f"总计去重站点: {len(all_sites)}")

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
        # --- 写入文件部分 ---
        output_files = [self.target, "all.json"]
        for filename in output_files:
            file_path = self.base_path / filename
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                print(f"核心检查：[写入成功] -> {file_path}") 
            except Exception as e:
                print(f"核心检查：[写入失败] -> {e}")

        # 检查目录下到底有没有文件（调试用）
        print(f"当前目录下所有文件: {os.listdir(self.base_path)}")

    tool = GetSrc(u_name, r_name, os.getenv('GITHUB_TOKEN'), my_api_url)
    
    # 运行
    asyncio.run(tool.download_drpy2_files())
    tool.run()
