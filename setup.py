"""
Python setup file for the Rag-Timesheet package
"""
from setuptools import setup, find_packages

setup(
    name="rag-timesheet",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "fastapi[all]",
        "uvicorn",
        "sqlalchemy",
        "pymysql",
        "cryptography",
        "sentence-transformers",
        "transformers",
        "elasticsearch",
        "python-dotenv",
        "torch",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "rag-timesheet=src.api.app:start",
        ],
    },
)
