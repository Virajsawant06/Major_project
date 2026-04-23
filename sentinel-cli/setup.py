from setuptools import setup, find_packages

setup(
    name="sentinel",
    version="0.2.0",
    packages=find_packages(),
    py_modules=["sentinel_cli"],
    install_requires=[
        "rich",
        "typer",
        "requests",
        "python-owasp-zap-v2.4",
        "python-dotenv",
        "openai",
        "prompt_toolkit",
        "beautifulsoup4",
        "sslyze",
    ],
    entry_points={
        "console_scripts": [
            "sentinel=sentinel_cli:main",
        ],
    },
)