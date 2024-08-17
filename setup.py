from setuptools import setup, find_packages

setup(
    name='miyuki',
    version='0.1.2',
    packages=find_packages(),
    install_requires=[
        'curl_cffi',
    ],
    entry_points={
        'console_scripts': [
            'miyuki=pip_package.miyuki:main',  # 假设您在 miyuki.py 中定义了一个 main() 函数作为入口
        ],
    },
    author='MiyukiQAQ',
    author_email='***REMOVED***',
    description='A tool for downloading videos from the "MissAV" website.',
    long_description=open('readme.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/MiyukiQAQ/MissAV-Downloader',  # 您的项目主页
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
