import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ========== 配置 ==========
# 请将下面 Malody / Phira / osu! 的 url 和 pwd 替换为你的实际分享链接和密码
FOLDERS = {
    "APP": {
        "url": "https://wwamp.lanzouu.com/b00zyvo2cf",
        "pwd": "hong"
    },
    "Malody": {
        "url": "",   # 请替换为你的 Malody 文件夹分享链接
        "pwd": ""
    },
    "Phira": {
        "url": "",   # 请替换为你的 Phira 文件夹分享链接
        "pwd": ""
    },
    "osu!": {
        "url": "",   # 请替换为你的 osu! 文件夹分享链接
        "pwd": ""
    }
}

# ========== 全局会话 ==========
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# ========== 核心函数 ==========
def get_page_html(url, pwd):
    """访问分享链接，如果遇到密码则自动提交"""
    resp = session.get(url, timeout=10)
    html = resp.text

    # 检测是否需要密码
    if '请输入密码' in html or '输入密码' in html:
        sign_match = re.search(r"var sign = '([a-f0-9]+)'", html)
        if sign_match:
            sign = sign_match.group(1)
            post_data = {
                'action': 'filelist',
                'pwd': pwd,
                'sign': sign
            }
            ajax_url = 'https://wwamp.lanzouu.com/ajaxm.php'
            resp = session.post(ajax_url, data=post_data)
            html = resp.text

    return html

def parse_files_and_folders(html, base_url):
    """解析页面，提取文件列表和子文件夹列表"""
    soup = BeautifulSoup(html, 'html.parser')
    files = []
    subfolders = []

    # 方法1：BeautifulSoup 解析（优先）
    rows = soup.select('tr.file')
    if not rows:
        rows = soup.select('tr')

    for row in rows:
        link_tag = row.find('a')
        if not link_tag:
            continue

        href = link_tag.get('href', '')
        name = link_tag.get_text(strip=True)
        if not name:
            continue

        # 补齐完整链接
        full_url = urljoin(base_url, href) if href else ''

        # 判断是否为文件夹（蓝奏云文件夹链接通常包含 "folder"）
        if 'folder' in href or name.endswith('/'):
            subfolders.append({
                "name": name.rstrip('/'),
                "url": full_url
            })
        else:
            # 提取文件大小
            size_td = row.find('td', class_='file_size')
            size = size_td.get_text(strip=True) if size_td else ''
            files.append({
                "name": name,
                "size": size,
                "url": full_url
            })

    # 方法2：正则兜底（如果 BeautifulSoup 没抓到任何内容）
    if not files and not subfolders:
        trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
        for tr in trs:
            name_match = re.search(r'<a[^>]*>(.*?)</a>', tr)
            link_match = re.search(r'href="([^"]+)"', tr)
            size_match = re.search(r'<td[^>]*class="file_size"[^>]*>(.*?)</td>', tr)
            if name_match and link_match:
                name = name_match.group(1).strip()
                href = link_match.group(1).strip()
                full_url = urljoin(base_url, href)
                if 'folder' in href or name.endswith('/'):
                    subfolders.append({"name": name.rstrip('/'), "url": full_url})
                else:
                    size = size_match.group(1).strip() if size_match else ''
                    files.append({"name": name, "size": size, "url": full_url})

    return files, subfolders

def fetch_recursive(url, pwd, visited=None):
    """递归抓取文件夹及其所有子文件夹"""
    if visited is None:
        visited = set()
    if not url or url in visited:
        return []
    visited.add(url)

    print(f"  正在抓取: {url}")
    html = get_page_html(url, pwd)
    files, subfolders = parse_files_and_folders(html, url)

    # 递归抓取子文件夹
    for sub in subfolders:
        sub_files = fetch_recursive(sub['url'], pwd, visited)
        files.extend(sub_files)

    # 稍微延迟，避免请求过快
    time.sleep(0.5)
    return files

# ========== 主流程 ==========
def main():
    result = {}
    for folder_name, config in FOLDERS.items():
        url = config.get('url')
        pwd = config.get('pwd', '')

        if not url:
            print(f'⚠️ 跳过 {folder_name}：未配置链接')
            result[folder_name] = []
            continue

        print(f'📁 正在递归抓取分类: {folder_name}')
        try:
            all_files = fetch_recursive(url, pwd)
            print(f'   ✅ 抓取完成，共 {len(all_files)} 个文件（含子文件夹）')
            result[folder_name] = all_files
        except Exception as e:
            print(f'   ❌ 失败：{e}')
            result[folder_name] = []

    # 写入 JSON
    with open('files.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print('✅ 已生成 files.json')

if __name__ == '__main__':
    main()