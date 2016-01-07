from setuptools import setup, find_packages

setup(
    name="swimlane",
    author="Swimlane LLC",
    author_email="info@swimlane.com",
    version="0.0.1",
    url="https://github.com/Swimlane/sw-python-client",
    packages=find_packages(),
    description="A Python driver for Swimlane.",
    install_requires=[
        "requests==2.8.1",
        "ordereddict==1.1",
        "combomethod==1.0.6"
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ]
)