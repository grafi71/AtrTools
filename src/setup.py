from setuptools import setup, find_packages

setup(
    name = 'atrtools',
    version='0.1.0',
    description = 'Atari conversion tools',
    author = 'Gandalf',
    author_email = 'grafi71@o2.pl',
    license = 'MIT',
    packages = find_packages(),
    install_requires = ['pillow'],
    entry_points = {'console_scripts': ['atrtools=atrtools.__main__:main', 
                                        'imgconv=atrtools.imgconv:main',
                                        'sapconv=atrtools.sapconv:main'] },
    zip_safe=True
)