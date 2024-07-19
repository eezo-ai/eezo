from setuptools import setup, find_packages


setup(
    name="eezo",
    version="0.4.1",
    description="Eezo helps you to build and supervise your AI agent workforce.",
    author="Daniel Schoenbohm",
    author_email="daniel@eezo.ai",
    packages=find_packages(),
    install_requires=[
        "annotated-types==0.6.0",
        "bidict==0.23.1",
        "certifi==2024.2.2",
        "charset-normalizer==3.3.2",
        "h11==0.14.0",
        "idna==3.7",
        "pydantic==2.7.1",
        "pydantic_core==2.18.2",
        "python-dotenv==1.0.1",
        "python-engineio==4.9.0",
        "python-socketio==5.11.2",
        "requests==2.31.0",
        "simple-websocket==1.0.0",
        "typing_extensions==4.11.0",
        "urllib3==2.2.1",
        "watchdog==4.0.0",
        "websocket-client==1.8.0",
        "wsproto==1.2.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
