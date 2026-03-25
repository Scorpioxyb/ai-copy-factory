#!/usr/bin/env python3
"""
AI文案工厂 v1.0.0 发布脚本
使用前需要：
  1. 安装 git
  2. 设置 GitHub token: set GITHUB_TOKEN=your_token
  3. 或者手动 git push
"""
import os, sys, subprocess, json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_NAME = "ai-copy-factory"

def run(cmd, cwd=PROJECT_DIR):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
        return None
    return result.stdout.strip()

def git_init_and_push():
    """初始化git仓库并推送到GitHub"""
    # 初始化
    run("git init")
    run("git add -A")
    run('git commit -m "v1.0.0: 首次发布 - 多平台AI文案生成器"')
    
    # 创建GitHub仓库（需要gh CLI或手动操作）
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        import requests
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        resp = requests.post("https://api.github.com/user/repos", 
                           headers=headers,
                           json={"name": REPO_NAME, "description": "多平台AI文案批量生成器 - 闲鱼/小红书/抖音/公众号", "auto_init": False})
        if resp.status_code == 201:
            print("  GitHub仓库创建成功!")
            repo_url = resp.json()["clone_url"]
            run(f"git remote add origin {repo_url}")
            run("git branch -M main")
            run("git push -u origin main")
            print(f"  推送完成: {repo_url}")
        else:
            print(f"  仓库创建失败: {resp.status_code} {resp.text}")
    else:
        print("  没有GITHUB_TOKEN，请手动:")
        print("  1. 在GitHub创建仓库 ai-copy-factory")
        print("  2. git remote add origin https://github.com/YOURNAME/ai-copy-factory.git")
        print("  3. git push -u origin main")

def pypi_publish():
    """发布到PyPI"""
    print("\n发布到PyPI:")
    print("  pip install twine")
    print("  twine upload dist/*")
    print("  需要PyPI账号和token")

if __name__ == "__main__":
    print("=" * 50)
    print("  AI文案工厂 v1.0.0 发布")
    print("=" * 50)
    
    print("\n[1/2] 推送到GitHub...")
    git_init_and_push()
    
    print("\n[2/2] 发布到PyPI...")
    pypi_publish()
    
    print("\n发布材料:")
    dist_dir = os.path.join(PROJECT_DIR, "dist")
    for f in os.listdir(dist_dir):
        size = os.path.getsize(os.path.join(dist_dir, f))
        print(f"  {f} ({size} bytes)")
