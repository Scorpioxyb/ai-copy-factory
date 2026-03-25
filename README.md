# 🏭 AI文案工厂 (AI Copy Factory)

> 一个命令，多平台批量出稿，直接发布赚钱。

**支持平台：** 闲鱼🐠 · 小红书📕 · 抖音🎵 · 公众号💬

## 为什么做这个

闲鱼TOP3交易品类 = PPT制作、游戏代练、文案服务。
小红书/抖音的内容需求更是无底洞。

AI生成文案 → 批量发布 → 边际成本趋近于零。

## 安装

```bash
pip install -r requirements.txt
```

或打包安装：

```bash
pip install .
# 之后可用 copy-factory 或 acf 命令
```

## 使用

### 1. 交互模式（最简单）

```bash
python ai_copy_factory.py
```

选择平台 → 输入信息 → 获得文案。

### 2. 快速生成

```bash
python ai_copy_factory.py quick -p xianyu --name "AirPods Pro 2" --price 899
python ai_copy_factory.py quick -p xiaohongshu --name "大学生宿舍好物" --desc "便宜实用"
python ai_copy_factory.py quick -p douyin --name "程序员的一天"
```

### 3. 批量生成（核心赚钱模式）

```bash
python ai_copy_factory.py batch examples/batch_example.json
```

JSON格式：

```json
[
    {
        "platform": "xianyu",
        "name": "商品名",
        "category": "数码",
        "condition": "9成新",
        "original_price": "999"
    },
    {
        "platform": "xiaohongshu",
        "topic": "笔记主题",
        "selling_points": "核心卖点",
        "style": "种草"
    }
]
```

### 4. API服务模式

```bash
python ai_copy_factory.py serve
# 启动在 http://127.0.0.1:8899
```

调用：

```bash
curl -X POST http://127.0.0.1:8899/generate \
  -H "Content-Type: application/json" \
  -d '{"platform": "xianyu", "params": {"name": "MacBook Air M2", "original_price": "8999"}}'
```

## API Key配置

```bash
# 推荐 DeepSeek（最便宜，新用户有免费额度）
set DEEPSEEK_API_KEY=your_key

# 或通义千问
set DASHSCOPE_API_KEY=your_key

# 或 OpenAI
set OPENAI_API_KEY=your_key
```

**DeepSeek注册:** https://platform.deepseek.com

## 赚钱路径

| 方式 | 收入预估 | 启动成本 |
|------|---------|---------|
| 闲鱼卖文案代写服务 | 500-3000/月 | 0元 |
| 小红书代运营 | 1000-5000/月 | 0元 |
| 批量闲鱼listing（自己卖货） | 看货品 | 看货品 |
| 打包卖这个工具 | 按定价 | PyPI发布免费 |

## License

MIT
