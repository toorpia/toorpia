from setuptools import setup, find_packages

setup(
    name='toorpia',
    version='0.4.0',
    author='toor Inc.',
    author_email='takaeda@toor.jpn.com',
    description='A client library for accessing the toorPIA high-dimensional data analysis API',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/toorpia/api.git',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.0.0',
        'numpy>=1.18.0',
        'requests>=2.22.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.7',
)
