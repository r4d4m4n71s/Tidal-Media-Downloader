from setuptools import setup, find_packages
from tidal_dl.printf import VERSION

setup(
    name='tidal-dl',
    version=VERSION,
    license="Apache2",
    description="Tidal Music Downloader.",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    author='r4d4m4n71s',
    author_email="r4d4m4n71s@foxmail.com",

    packages=find_packages(exclude=['tidal_gui*']),
    include_package_data=False,
    platforms="any",
    install_requires=["aigpy>=2022.7.8.1", 
                      "requests>=2.22.0",
                      "pycryptodome", 
                      "pydub", 
                      "prettytable",
                      "lxml"],
    entry_points={'console_scripts': ['tidal-dl = tidal_dl:main', ]}
)
