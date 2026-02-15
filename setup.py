from setuptools import setup, find_packages

setup(
    name='toorpia',
    version='1.1.1',
    author='toor Inc.',
    author_email='takaeda@toor.jpn.com',
    description='API Frontend libraries of toorpia',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/toorpia/toorpia.git',
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
