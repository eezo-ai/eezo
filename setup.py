from setuptools import setup, find_packages

setup(
    name="eezo",
    version="0.1.4",
    description="Eezo's Dashboard streamlines the management of AI agents via its API, offering a user-friendly interface that requires minimal coding. It enables easy access for all team members, fostering agent interaction and collaboration. The platform also features real-time data sharing with interactive charts, making it an ideal solution for developers and companies looking to centralize their AI tools and processes.",
    author="Daniel Schoenbohm",
    author_email="daniel@eezo.ai",
    packages=find_packages(),
    install_requires=[
        "aiohttp==3.9.3",
        "aiosignal==1.3.1",
        "async-timeout==4.0.3",
        "attrs==23.2.0",
        "bidict==0.23.1",
        "certifi==2024.2.2",
        "charset-normalizer==3.3.2",
        "frozenlist==1.4.1",
        "h11==0.14.0",
        "idna==3.6",
        "multidict==6.0.5",
        "python-engineio==4.9.0",
        "python-socketio==5.11.1",
        "requests==2.31.0",
        "simple-websocket==1.0.0",
        "urllib3==2.2.1",
        "watchdog==4.0.0",
        "wsproto==1.2.0",
        "yarl==1.9.4",
        "websocket-client==1.7.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",  # Alpha status
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
