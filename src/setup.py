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
    entry_points = {'console_scripts': ['atrtool=atrtools.__main__:main', 
                                        'atrimgcon=atrtools.imgconv.__main__:main',
                                        'atrsapcon=atrtools.sapconv.__main__:main'] },
    zip_safe=True
)