# 教程待完善


import json
import requests
from github import Github

def get_ipv4():
    ipv4 = requests.get('https://api.ipify.org').text
    return ipv4

def get_ipv6():
    ipv6 = requests.get('https://api64.ipify.org').text
    return ipv6

def upload_file(content, access_token, owner, repo, path):
    g = Github(access_token)
    repo = g.get_user(owner).get_repo(repo)
    file = repo.get_contents(path)
    repo.update_file(file.path, "Auto update", content, file.sha)
    print("Uploaded successfully to", file.path)

ipv4 = get_ipv4()
ipv6 = get_ipv6()
data = ipv4+';'+ipv6
#json_data = json.dumps(data, indent=4)

access_token = "github_personal_access_token"
owner = "用户名"
repo = "用户名"
path = "路径"

upload_file(data, access_token, owner, repo, path)