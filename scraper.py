import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===== 配置 =====
FOLDERS = {
    "APP": {
        "url": "https://wwamp.lanzouu.com/b00zyvo2cf",
        "pwd": "hong"
    },
    "Malody": {"url": "", "pwd": ""},
    "Phira": {"url": "", "pwd": ""},
    "osu!": {"url": "", "pwd": ""}
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

def get_page_html(url, pwd):
    """访问页面，处理密码提交"""
    resp = session.get(url, timeout=10)
    html = resp.text

    if '请输入密码' in html or '输入密码' in html:
        sign_match = re.search(r"var sign = '([a-f0-9]+)'", html)
        if sign_match:
            sign = sign_match.group(1)
            post_data = {'action': 'filelist', 'pwd': pwd, 'sign': sign}
            ajax_url = 'https://wwamp.lanzouu.com/ajaxm.php'
            resp = session.post(ajax_url, data=post_data, headers={'Referer': url})
            html = resp.text
    return html

def parse_files_and_folders(html, base_url):
    """解析HTML，提取文件列表和子文件夹链接"""
    soup = BeautifulSoup(html, 'html.parser')
    files = []
    subfolders = []

    rows = soup.select('tr.file') or soup.select('tr') or soup.select('.file-item')
    for row in rows:
        link_tag = row.find('a')
        if not link_tag:
            continue

        href = link_tag.get('href', '')
        name = link_tag.get_text(strip=True)
        if not name:
            continue

        full_url = urljoin(base_url, href) if href else ''

        if 'folder' in href or name.endswith('/'):
            subfolders.append({"name": name.rstrip('/'), "url": full_url})
        else:
            size_td = row.find('td', class_='file_size') or row.find('span', class_='size')
            size = size_td.get_text(strip=True) if size_td else ''
            files.append({"name": name, "size": size, "url": full_url})

    # 正则兜底
    if not files and not subfolders:
        trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
        for tr in trs:
            a_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', tr)
            if a_match:
                href = a_match.group(1)
                name = a_match.group(2).strip()
                full_url = urljoin(base_url, href)
                if 'folder' in href or name.endswith('/'):
                    subfolders.append({"name": name.rstrip('/'), "url": full_url})
                else:
                    size_match = re.search(r'<td[^>]*class="file_size"[^>]*>(.*?)</td>', tr)
                    size = size_match.group(1).strip() if size_match else ''
                    files.append({"name": name, "size": size, "url": full_url})

    return files, subfolders

def fetch_recursive(url, pwd, visited=None):
    """递归抓取文件夹及其所有子文件夹（即使当前文件夹没有文件）"""
    if visited is None:
        visited = set()
    if not url or url in visited:
        return []
    visited.add(url)

    print(f"  正在抓取: {url}")
    try:
        html = get_page_html(url, pwd)
        files, subfolders = parse_files_and_folders(html, url)

        print(f"    当前文件夹: {len(files)} 个文件, {len(subfolders)} 个子文件夹")
        
        # 递归抓取所有子文件夹
        for sub in subfolders:
            sub_files = fetch_recursive(sub['url'], pwd, visited)
            files.extend(sub_files)

        time.sleep(1)
        return files
    except Exception as e:
        print(f"  抓取失败: {e}")
        return []

def main():
    result = {}
    for name, config in FOLDERS.items():
        url = config.get('url')
        pwd = config.get('pwd', '')
        if not url:
            print(f'⚠️ 跳过 {name}：未配置链接')
            result[name] = []
            continue
        print(f'📁 正在递归抓取分类: {name}')
        files = fetch_recursive(url, pwd)
        print(f'   ✅ 抓取完成，共 {len(files)} 个文件')
        result[name] = files

    with open('files.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('✅ 已生成 files.json')

if __name__ == '__main__':
    main()