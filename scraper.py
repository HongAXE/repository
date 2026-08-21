import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===== 配置 =====
FOLDERS = {
    "APP": {
        "url": "https://wwamp.lanzouu.com/b00zyvo2cf",
        "pwd": "hong"
    },
    "Malody": {
        "url": "你的Malody分享链接",
        "pwd": ""
    },
    "Phira": {
        "url": "你的Phira分享链接",
        "pwd": ""
    },
    "osu!": {
        "url": "你的osu!分享链接",
        "pwd": ""
    }
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def get_page_html(url, pwd):
    """访问页面，如果遇到密码则自动提交"""
    resp = session.get(url, timeout=10)
    html = resp.text
    
    if '请输入密码' in html or '输入密码' in html:
        sign_match = re.search(r"var sign = '([a-f0-9]+)'", html)
        if sign_match:
            sign = sign_match.group(1)
            post_data = {'action': 'filelist', 'pwd': pwd, 'sign': sign}
            ajax_url = urljoin(url, '/ajaxm.php')
            resp = session.post(ajax_url, data=post_data)
            html = resp.text
    return html

def parse_files_and_folders(html, base_url):
    """解析页面，返回文件列表和子文件夹列表"""
    soup = BeautifulSoup(html, 'html.parser')
    files = []
    subfolders = []
    
    # 方法1：BeautifulSoup 选择器
    for row in soup.select('tr.file'):
        name_elem = row.select_one('td.file_name')
        link_elem = row.select_one('td.file_name a')
        size_elem = row.select_one('td.file_size')
        
        if name_elem and link_elem:
            name = name_elem.get_text(strip=True)
            link = link_elem.get('href', '')
            size = size_elem.get_text(strip=True) if size_elem else ''
            
            # 判断是否为文件夹（蓝奏云文件夹通常名称后带“/”或链接含“folder”）
            is_folder = link and ('/folder' in link or name.endswith('/'))
            full_link = urljoin(base_url, link) if link else ''
            
            if is_folder:
                subfolders.append({
                    "name": name.rstrip('/'),
                    "url": full_link
                })
            else:
                files.append({
                    "name": name,
                    "size": size,
                    "url": full_link
                })
    
    # 方法2：正则兜底（如果 BeautifulSoup 没抓到）
    if not files and not subfolders:
        trs = re.findall(r'<tr class="file">(.*?)</tr>', html, re.DOTALL)
        for tr in trs:
            name_match = re.search(r'<td class="file_name">(.*?)</td>', tr)
            link_match = re.search(r'href="([^"]+)"', tr)
            size_match = re.search(r'<td class="file_size">(.*?)</td>', tr)
            if name_match and link_match:
                name = name_match.group(1).strip()
                link = link_match.group(1).strip()
                full_link = urljoin(base_url, link)
                size = size_match.group(1).strip() if size_match else ''
                is_folder = '/folder' in link or name.endswith('/')
                if is_folder:
                    subfolders.append({"name": name.rstrip('/'), "url": full_link})
                else:
                    files.append({"name": name, "size": size, "url": full_link})
    
    return files, subfolders

def fetch_recursive(url, pwd, visited=None):
    """递归抓取文件夹及其所有子文件夹"""
    if visited is None:
        visited = set()
    if url in visited:
        return []
    visited.add(url)
    
    html = get_page_html(url, pwd)
    files, subfolders = parse_files_and_containers(html, url)
    
    # 递归抓取子文件夹
    for sub in subfolders:
        sub_files = fetch_recursive(sub['url'], pwd, visited)
        files.extend(sub_files)
    
    return files

def main():
    result = {}
    for folder_name, config in FOLDERS.items():
        url = config.get('url')
        pwd = config.get('pwd', '')
        if not url:
            print(f'⚠️ 跳过 {folder_name}：未配置链接')
            result[folder_name] = []
            continue
        
        print(f'📁 正在递归抓取 {folder_name}...')
        try:
            all_files = fetch_recursive(url, pwd)
            print(f'   ✅ 抓取到 {len(all_files)} 个文件（含所有子文件夹）')
            result[folder_name] = all_files
        except Exception as e:
            print(f'   ❌ 失败：{e}')
            result[folder_name] = []
    
    with open('files.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print('✅ 已生成 files.json')

if __name__ == '__main__':
    main()
