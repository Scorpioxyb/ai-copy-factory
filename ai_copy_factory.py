#!/usr/bin/env python3
"""
🏭 AI文案工厂 (AI Copy Factory)
多平台AI文案批量生成器 —— 闲鱼/小红书/抖音/公众号

一个命令，批量出稿，直接发布赚钱。

支持平台：
  xianyu    — 闲鱼商品listing
  xiaohongshu — 小红书种草笔记
  douyin    — 抖音短视频脚本
  wechat    — 公众号文章大纲+开头

用法：
  python ai_copy_factory.py interactive          # 交互模式
  python ai_copy_factory.py batch items.json      # 批量模式
  python ai_copy_factory.py serve                 # API服务模式（供前端调用）
"""

import os
import sys
import io

# 修复Windows终端UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# ========== 平台Prompt模板 ==========

PLATFORMS = {
    "xianyu": {
        "name": "闲鱼",
        "emoji": "🐠",
        "system_prompt": """你是闲鱼资深卖家，懂平台算法和用户心理。
根据商品信息生成高转化率listing。

输出格式（严格遵守）：
【标题】30字以内，带情绪词（急出/捡漏/亏本/白菜价/全新包邮）
【描述】200字以内，讲"为什么卖"的故事，接地气像真人
【关键词】15个逗号分隔的搜索关键词
【建议售价】X元
【定价理由】一句话""",
        "user_template": """商品：{name}
类别：{category}
新旧：{condition}
原价：{original_price}
入手时间：{purchase_time}
配件：{accessories}
说明：{extra}""",
    },
    "xiaohongshu": {
        "name": "小红书",
        "emoji": "📕",
        "system_prompt": """你是小红书爆款笔记作者，粉丝10万+。
根据主题生成种草/测评/教程笔记。

输出格式：
【标题】带emoji，20字以内，有悬念或数字
【正文】300字以内，口语化，分段，带emoji
【标签】10个#话题标签
【封面建议】一句话描述封面图风格""",
        "user_template": """主题：{topic}
品类：{category}
卖点：{selling_points}
目标人群：{target_audience}
风格：{style}""",
    },
    "douyin": {
        "name": "抖音",
        "emoji": "🎵",
        "system_prompt": """你是抖音百万粉博主的编导，精通短视频节奏。
根据主题生成15-60秒短视频脚本。

输出格式：
【标题】悬念/反差/数字，15字以内
【开头hook】前3秒的台词（决定完播率）
【脚本】分镜头：画面描述 + 台词/旁白
【结尾引导】关注/点赞/评论话术
【BGM建议】音乐风格""",
        "user_template": """主题：{topic}
视频类型：{video_type}
产品/服务：{product}
目标：{goal}
时长：{duration}""",
    },
    "wechat": {
        "name": "公众号",
        "emoji": "💬",
        "system_prompt": """你是公众号10万+爆文作者。
根据主题生成文章大纲和开头段落。

输出格式：
【标题】有信息增量，让人想点
【大纲】5-7个小标题
【开头段】200字，有故事感，制造悬念
【金句】3句适合做封面的金句
【配图建议】描述3张配图风格""",
        "user_template": """主题：{topic}
领域：{domain}
目标读者：{target_reader}
文章目的：{purpose}""",
    },
}

# ========== 核心引擎 ==========


def get_api_client():
    """获取可用的AI API客户端"""
    # 优先级：DeepSeek > 通义千问 > OpenAI
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    try:
        import openai
    except ImportError:
        print("❌ 需要openai库: pip install openai")
        sys.exit(1)

    if deepseek_key:
        return openai.OpenAI(
            api_key=deepseek_key, base_url="https://api.deepseek.com"
        ), "deepseek-chat"
    elif dashscope_key:
        return openai.OpenAI(
            api_key=dashscope_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        ), "qwen-plus"
    elif openai_key:
        return openai.OpenAI(api_key=openai_key), "gpt-4o-mini"
    else:
        print("❌ 请设置至少一个API Key:")
        print("   set DEEPSEEK_API_KEY=your_key    (推荐，最便宜)")
        print("   set DASHSCOPE_API_KEY=your_key   (通义千问)")
        print("   set OPENAI_API_KEY=your_key")
        print("\n💡 DeepSeek注册送免费额度: https://platform.deepseek.com")
        sys.exit(1)


def generate_content(platform: str, params: dict) -> str:
    """生成单条文案"""
    if platform not in PLATFORMS:
        raise ValueError(f"不支持的平台: {platform}，可选: {', '.join(PLATFORMS.keys())}")

    p = PLATFORMS[platform]
    client, model = get_api_client()

    user_msg = p["user_template"].format(**params)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": p["system_prompt"]},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.8,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()


def batch_generate(items_file: str):
    """批量生成 - 从JSON文件读取"""
    with open(items_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    results = []
    total = len(items)

    for i, item in enumerate(items):
        platform = item.get("platform", "xianyu")
        name = item.get("name", item.get("topic", "未知"))
        emoji = PLATFORMS.get(platform, {}).get("emoji", "📝")

        print(f"\n[{i+1}/{total}] {emoji} 生成{PLATFORMS.get(platform, {}).get('platform', platform)}文案: {name}...")

        try:
            content = generate_content(platform, item)
            results.append(
                {
                    "platform": platform,
                    "name": name,
                    "content": content,
                    "generated_at": datetime.now().isoformat(),
                }
            )
            print(content)
            print("-" * 50)
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            results.append({"platform": platform, "name": name, "error": str(e)})

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(items_file).parent / f"output_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 同时生成可读文本版
    txt_file = Path(items_file).parent / f"output_{timestamp}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        for r in results:
            if "error" in r:
                f.write(f"=== ❌ {r['name']} ===\n错误: {r['error']}\n\n")
            else:
                emoji = PLATFORMS.get(r["platform"], {}).get("emoji", "📝")
                f.write(f"=== {emoji} {r['name']} [{r['platform']}] ===\n")
                f.write(f"{r['content']}\n\n")

    print(f"\n✅ 批量生成完成!")
    print(f"   JSON: {output_file}")
    print(f"   文本: {txt_file}")
    return results


# ========== 交互模式 ==========


def interactive_mode():
    """交互式选择平台并生成"""
    print("=" * 55)
    print("  🏭 AI文案工厂 —— 多平台AI文案批量生成器")
    print("=" * 55)

    print("\n选择平台:")
    for key, p in PLATFORMS.items():
        print(f"  {p['emoji']} {key:15s} — {p['name']}")

    print(f"\n  📦 all — 全平台一键生成（同商品多平台文案）")

    choice = input("\n选择平台 [xianyu]: ").strip().lower() or "xianyu"

    if choice == "all":
        _interactive_all_platforms()
    elif choice in PLATFORMS:
        _interactive_single(choice)
    else:
        print(f"❌ 未知平台: {choice}")
        return


def _interactive_single(platform: str):
    """单平台交互"""
    p = PLATFORMS[platform]
    print(f"\n{p['emoji']} {p['name']}文案生成")
    print("-" * 30)

    # 根据平台收集不同参数
    params = {}
    if platform == "xianyu":
        params["name"] = input("📦 商品名称: ").strip()
        if not params["name"]:
            print("❌ 名称不能为空"); return
        params["category"] = input("📂 类别: ").strip()
        params["condition"] = input("✨ 新旧 [9成新]: ").strip() or "9成新"
        params["original_price"] = input("💰 原价: ").strip()
        params["purchase_time"] = input("📅 入手时间: ").strip()
        params["accessories"] = input("🔧 配件 [齐全]: ").strip() or "齐全"
        params["extra"] = input("📝 说明: ").strip()
    else:
        params["topic"] = input(f"📌 主题: ").strip()
        if not params["topic"]:
            print("❌ 主题不能为空"); return
        if platform == "xiaohongshu":
            params["category"] = input("📂 品类: ").strip()
            params["selling_points"] = input("⭐ 卖点: ").strip()
            params["target_audience"] = input("👥 目标人群: ").strip()
            params["style"] = input("🎨 风格 [干货/种草/测评]: ").strip() or "干货"
        elif platform == "douyin":
            params["video_type"] = input("🎬 视频类型 [口播/演示/vlog]: ").strip() or "口播"
            params["product"] = input("🏷️ 产品/服务: ").strip()
            params["goal"] = input("🎯 目标 [带货/涨粉/品牌]: ").strip() or "涨粉"
            params["duration"] = input("⏱️ 时长 [30秒]: ").strip() or "30秒"
        elif platform == "wechat":
            params["domain"] = input("📚 领域: ").strip()
            params["target_reader"] = input("👥 目标读者: ").strip()
            params["purpose"] = input("🎯 文章目的: ").strip()

    print(f"\n🤖 正在生成{p['name']}文案...")
    result = generate_content(platform, params)

    print("\n" + "=" * 55)
    print(f"  {p['emoji']} 生成的{p['name']}文案：")
    print("=" * 55)
    print(result)
    print("=" * 55)
    print("\n✅ 复制文案去发布吧！")


def _interactive_all_platforms():
    """全平台一键生成"""
    print("\n📦 全平台文案生成")
    print("-" * 30)

    name = input("📦 商品/主题名称: ").strip()
    if not name:
        print("❌ 名称不能为空"); return

    desc = input("📝 简单描述: ").strip()
    price = input("💰 价格（可选）: ").strip()

    base_params = {"name": name, "topic": name, "category": "", "selling_points": desc,
                   "target_audience": "", "style": "种草", "video_type": "口播",
                   "product": name, "goal": "带货", "duration": "30秒",
                   "domain": "", "target_reader": "", "purpose": "种草",
                   "condition": "全新", "original_price": price or "未知",
                   "purchase_time": "近期", "accessories": "齐全", "extra": desc}

    for key, p in PLATFORMS.items():
        print(f"\n{'='*55}")
        print(f"  {p['emoji']} {p['name']}文案：")
        print(f"{'='*55}")
        result = generate_content(key, base_params)
        print(result)


# ========== API服务模式 ==========


def serve_mode(host="127.0.0.1", port=8899):
    """HTTP API服务，供前端/其他程序调用"""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
    except ImportError:
        print("❌ http.server不可用")
        return

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
                platform = data.get("platform", "xianyu")
                params = data.get("params", {})

                result = generate_content(platform, params)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(
                    {"status": "ok", "platform": platform, "content": result},
                    ensure_ascii=False
                ).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))

        def do_GET(self):
            if self.path == "/platforms":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                info = {k: {"name": v["name"], "emoji": v["emoji"]} for k, v in PLATFORMS.items()}
                self.wfile.write(json.dumps(info, ensure_ascii=False).encode("utf-8"))
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"AI Copy Factory API - POST /generate with {platform, params}")

        def log_message(self, format, *args):
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

    server = HTTPServer((host, port), Handler)
    print(f"🏭 AI文案工厂 API服务已启动")
    print(f"   地址: http://{host}:{port}")
    print(f"   POST /generate  body: {{\"platform\": \"xianyu\", \"params\": {{...}}}}")
    print(f"   GET  /platforms  查看支持的平台")
    print(f"   Ctrl+C 停止\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")


# ========== CLI入口 ==========


def main():
    parser = argparse.ArgumentParser(
        description="AI Copy Factory - 多平台AI文案批量生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ai_copy_factory.py                     # 交互模式
  python ai_copy_factory.py -p xianyu           # 指定闲鱼平台
  python ai_copy_factory.py batch items.json    # 批量生成
  python ai_copy_factory.py serve               # 启动API服务
  python ai_copy_factory.py serve --port 9000   # 自定义端口
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # 交互模式（默认）
    subparsers.add_parser("interactive", aliases=["i"], help="交互模式")

    # 批量模式
    batch_parser = subparsers.add_parser("batch", aliases=["b"], help="批量生成")
    batch_parser.add_argument("file", help="JSON配置文件路径")

    # 服务模式
    serve_parser = subparsers.add_parser("serve", aliases=["s"], help="API服务模式")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8899)

    # 快速生成
    quick_parser = subparsers.add_parser("quick", aliases=["q"], help="快速生成单条")
    quick_parser.add_argument("-p", "--platform", default="xianyu", choices=list(PLATFORMS.keys()))
    quick_parser.add_argument("--name", required=True, help="商品/主题名称")
    quick_parser.add_argument("--desc", default="", help="描述/卖点")
    quick_parser.add_argument("--price", default="", help="价格")

    args = parser.parse_args()

    if args.command in ("interactive", "i") or args.command is None:
        interactive_mode()
    elif args.command in ("batch", "b"):
        batch_generate(args.file)
    elif args.command in ("serve", "s"):
        serve_mode(args.host, args.port)
    elif args.command in ("quick", "q"):
        params = {
            "name": args.name, "topic": args.name,
            "category": "", "condition": "9成新",
            "original_price": args.price or "未知",
            "purchase_time": "近期", "accessories": "齐全",
            "extra": args.desc, "selling_points": args.desc,
            "target_audience": "", "style": "种草",
            "video_type": "口播", "product": args.name,
            "goal": "涨粉", "duration": "30秒",
            "domain": "", "target_reader": "", "purpose": "种草",
        }
        print(f"\n🤖 正在生成{PLATFORMS[args.platform]['name']}文案...")
        result = generate_content(args.platform, params)
        print(result)


if __name__ == "__main__":
    main()
