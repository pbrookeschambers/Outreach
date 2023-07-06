def main():
    tick = '\x1b[1;32m\u2713\x1b[0m'
    cross = '\x1b[1;31m\u2717\x1b[0m'
    # check current python version
    import sys
    success = True
    print(pad("Checking major python version", 50, char = "\x1b[0;90m\u2022\x1b[0m"), end = "", flush = True)
    major = sys.version_info.major
    if major < 3:
        print(cross)
        print('You are using Python {}. Please use Python 3'.format(major))
        success = False
        return
    print(tick)
    print(pad("Checking minor python version", 50, char = "\x1b[0;90m\u2022\x1b[0m"), end = "", flush = True)
    minor = sys.version_info.minor
    if minor < 10:
        print(cross)
        print('You are using Python {}.{}. Please update to Python 3.10.0 or newer'.format(major, minor))
        success = False
    else:
        print(tick)
    # check required packages
    packages = ['rich', 'munch']
    for package in packages:
        print(pad("Checking for package {}".format(package), 50, char = "\x1b[0;90m\u2022\x1b[0m"), end = "", flush = True)
        try:
            __import__(package)
            print(tick)
        except ImportError:
            print(cross)
            print(install_package_message(package))
            success = False

    # check for pdflatex
    print(pad("Checking for pdflatex", 50, char = "\x1b[0;90m\u2022\x1b[0m"), end = "", flush = True)
    import shutil
    if shutil.which('pdflatex') is None:
        print(cross)
        print('pdflatex could not be found. Please install it. If it is already installed, make sure it is available in your path.')
        success = False
    else:
        print(tick)

    if not success:
        return
    
    print("All requirements satisfied")

def pad(text, length, char = " "):
    return text + char * (length - len(text))

def install_package_message(package):
    return f"""You seem to be missing the package {package}. Please install it using the command
python -m pip install {package}
\tor
python3 -m pip install {package}"""

if __name__ == '__main__':
    main()