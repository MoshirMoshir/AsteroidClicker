import subprocess
import sys

def install_packages():
    try:
        import pip
    except ImportError:
        print("Pip not found. Installing pip...")
        subprocess.check_call([sys.executable, '-m', 'ensurepip'])
        import pip

    try:
        import pkg_resources
    except ImportError:
        print("Setuptools not found. Installing setuptools...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'setuptools'])
        import pkg_resources

    with open('requirements.txt', 'r') as f:
        requirements = f.readlines()

    for package in requirements:
        try:
            pkg_resources.require(package)
        except pkg_resources.DistributionNotFound:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except pkg_resources.VersionConflict as vc:
            print(f"Version conflict found: {vc}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package.split('=')[0]])

if __name__ == "__main__":
    install_packages()
