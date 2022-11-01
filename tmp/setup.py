from setuptools import setup

setup(
    name="repo-cli",
    version="1.0.25",
    description="Command line interface for Anaconda Server",
    python_requires=">=3.7",
    install_requires=["conda"],
    py_modules=["repo"],
    entry_points={"conda": ["repo = repo"]},
)
