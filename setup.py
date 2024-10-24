from setuptools import setup, find_packages


with open("README.md", "r") as fd:
    readme = fd.read()


setup(
    name="photoshnaya",
    version="1.0.0",
    author="Artemii Kulikov",
    author_email="workerco@student.21-school.ru",
    description="Telegram-based application for photo-contests in group chats",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/vlle/Photoshnaya",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        # No license classifier
    ],
    python_requires=">=3.11",
    install_requires=[
        "aiogram",
        "sqlalchemy",
    ],
    extras_require={
        "dev": [
            "pytest"
        ]
    }
)
