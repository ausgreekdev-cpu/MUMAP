from setuptools import setup, find_packages

setup(
    name="multi-agent-platform",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "rich>=13.0.0",
    ],
    author="Multi-Agent Platform",
    description="A beginner-friendly private multi-agent orchestration platform",
    python_requires=">=3.9",
)
