from setuptools import setup, find_packages

setup(
    name="changestory",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "changestory = changestory_cli.main:cli_main",
        ],
    },
)
