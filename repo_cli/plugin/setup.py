from setuptools import setup

setup(
    name="repo-cli",
    version="1.0.25",
    description="Command line interface for Anaconda Server",
    python_requires=">=3.7",
    install_requires=["conda", "sympy"],
    py_modules=["ascii_graph"],
    entry_points={"conda": ["ascii-graph = ascii_graph"]},
)
