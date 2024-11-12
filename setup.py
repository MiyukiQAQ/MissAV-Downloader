from setuptools import setup, find_packages

setup(
    name='miyuki',
    version='0.4.2',
    packages=find_packages(),
    install_requires=[
        'curl_cffi',
    ],
    entry_points={
        'console_scripts': [
            'miyuki=miyuki.miyuki:main',
        ],
    },
    author='MiyukiQAQ',
    author_email='teemovv@outlook.com',
    description='A tool for downloading videos from the "MissAV" website.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/MiyukiQAQ/MissAV-Downloader',
    project_urls={
        'Bug Tracker': 'https://github.com/MiyukiQAQ/MissAV-Downloader/issues',
        'Source Code': 'https://github.com/MiyukiQAQ/MissAV-Downloader',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
