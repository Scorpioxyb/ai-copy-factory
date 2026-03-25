from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ai-copy-factory",
    version="1.0.0",
    author="小金",
    author_email="xiaojin@example.com",
    description="多平台AI文案批量生成器 — 闲鱼/小红书/抖音/公众号",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourname/ai-copy-factory",
    py_modules=["ai_copy_factory"],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "copy-factory=ai_copy_factory:main",
            "acf=ai_copy_factory:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai copywriting xianyu xiaohongshu douyin automation 自动化 文案 闲鱼 小红书",
)
