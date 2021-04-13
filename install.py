# Import pip
import pip, os
# Packages neede for all OS types
_all_ = [
	"wheel==0.36.2",
	"beautifulsoup4==4.9.3",
	"bs4==0.0.1",
	"requests==2.25.1"
]
# Pacakges for Windows only
windows = []
# Pacakges for Linux only
linux = []
# Pacakges for Mac only
darwin = []
# Install packages
def install(packages):
	for package in packages:
		os.system("python -m pip install {}".format(package))
# Run script
if __name__ == '__main__':
	# Import platform to get OS type
	from sys import platform
	# Run install function for generic pacakges
	install(_all_) 
	# Run install function for corrospondig OS
	if platform == 'win32' or platform == "windows":
		install(windows)
	if platform.startswith('linux'):
		install(linux)
	if platform == 'darwin': # MacOS
		install(darwin)
