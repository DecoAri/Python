import os
import time
import requests
import json
import logging
from datetime import datetime

# 配置日志输出到 stdout，显示在 docker logs 中
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # 输出到 stdout
)

# 存储版本记录的文件（容器内部路径）
RELEASE_RECORDS = "/app/release_records.json"
PRERELEASE_RECORDS = "/app/prerelease_records.json"

# 获取环境变量
watch_time = int(os.getenv("watch-time", 3600))  # 默认 1 小时
repos = []
for i in range(1000):  # 支持无限添加，假设最多 1000 个
    bark_api = os.getenv(f"bark-api{i}")  # 直接获取完整的 Bark API URL
    repo = os.getenv(f"repo{i}")
    group = os.getenv(f"group{i}", "Github")
    icon = os.getenv(f"icon{i}")
    if bark_api and repo:
        repos.append({
            "bark_api": bark_api,  # 替换原来的 bark_host 和 bark_key
            "repo": repo,
            "group": group,
            "icon": icon
        })
    else:
        break

def load_records(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_records(file, data):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w") as f:
        json.dump(data, f)

def bark_notify(bark_api, title, body, group, icon=None):
    # 直接使用完整的 bark_api 作为 URL
    url = bark_api
    payload = {"title": title, "body": body, "group": group}
    if icon:
        payload["icon"] = icon
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"通知发送成功: {title} - {body}")
    except requests.RequestException as e:
        logging.error(f"通知发送失败: {title} - {body}, 错误: {e}")

def fetch_url(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logging.info(f"成功获取 {url}")
            return response
        except (requests.RequestException, requests.Timeout) as e:
            logging.warning(f"请求 {url} 失败: {e}，尝试重试 {attempt+1}/{retries}")
            if attempt < retries - 1:
                time.sleep(delay)
    logging.error(f"请求 {url} 失败，已达最大重试次数")
    return None

def check_updates(repo_info):
    repo = repo_info["repo"]
    bark_api = repo_info["bark_api"]
    group = repo_info["group"]
    icon = repo_info["icon"]

    logging.info(f"开始检查项目: {repo}")
    # GitHub API 获取所有 releases
    releases_url = f"https://api.github.com/repos/{repo}/releases"

    # 获取所有 releases 数据
    response = fetch_url(releases_url)
    if response and response.status_code == 200:
        releases = response.json()

        # 检查最新的 Release（非 Pre-release）
        release_records = load_records(RELEASE_RECORDS)
        for r in releases:
            if not r.get("prerelease"):  # 只取正式版 Release
                version = r["tag_name"]
                pub_time = r["published_at"]
                if release_records.get(repo) != version:
                    title = f"Github项目{repo}已更新"
                    body = f"Release: {version}, 更新时间: {pub_time}"
                    bark_notify(bark_api, title, body, group, icon)
                    release_records[repo] = version
                    save_records(RELEASE_RECORDS, release_records)
                else:
                    logging.info(f"{repo} Release 未更新: {version}")
                break  # 只取最新的 Release
        else:
            logging.info(f"{repo} 无正式 Release")

        # 检查最新的 Pre-release
        prerelease_records = load_records(PRERELEASE_RECORDS)
        for r in releases:
            if r.get("prerelease"):  # 只取预发布版
                version = r["tag_name"]
                pub_time = r["published_at"]
                if prerelease_records.get(repo) != version:
                    title = f"Github项目{repo}已更新"
                    body = f"Pre-release: {version}, 更新时间: {pub_time}"
                    bark_notify(bark_api, title, body, group, icon)
                    prerelease_records[repo] = version
                    save_records(PRERELEASE_RECORDS, prerelease_records)
                else:
                    logging.info(f"{repo} Pre-release 未更新: {version}")
                break  # 只取最新的 Pre-release
        else:
            logging.info(f"{repo} 无 Pre-release")

while True:
    logging.info("开始新一轮检查")
    for repo_info in repos:
        check_updates(repo_info)
    logging.info(f"检查完成，等待 {watch_time} 秒")
    time.sleep(watch_time)