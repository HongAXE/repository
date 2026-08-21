# 我的蓝奏云资源库

一个基于蓝奏云的资源库 APP（HTML + WebToApp 打包），通过 GitHub Actions 自动同步文件列表。

## 自动同步原理

- `scraper.py`：递归抓取指定蓝奏云文件夹（含子文件夹）中的所有文件。
- GitHub Actions（`sync.yml`）：每天自动运行爬虫，并将生成的 `files.json` 提交到仓库。
- `index.html`：读取 `files.json` 展示文件列表，点击跳转下载。

## 如何配置

1. 在 `scraper.py` 的 `FOLDERS` 字典中填入你的蓝奏云分享链接和密码。
2. 将仓库中的 `files.json` raw 链接填入 `index.html` 的 `DATA_URL`。
3. 手动触发一次 GitHub Actions，生成 `files.json`。
4. 用 WebToApp 将 `index.html` 打包成 APK。

## 文件结构

- `.github/workflows/sync.yml` — GitHub Actions 工作流
- `scraper.py` — 爬虫脚本
- `index.html` — APP 主页面
- `files.json` — 自动生成的文件索引（不要手动编辑）

## 授权

仅供个人学习参考，请勿用于商业用途。
