from setuptools import find_packages, setup
from glob import glob
import os


package_name = 'voice_ppv'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        (os.path.join('share', package_name, 'resource'), glob('resource/*') + ['resource/.env']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='eycho',
    maintainer_email='eycho96@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'get_kw = voice_ppv.get_keyword:main',
            'get_kwf = voice_ppv.get_keyword_f:main',
            'get_keyword_screw = voice_ppv.get_keyword_screw:main',
        ],
    },
)
