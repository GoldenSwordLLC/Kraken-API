Upon installing Python, ensure you customize your installation and have tcl/tk installed:
https://stackoverflow.com/a/63032937/9614384
Also make sure you click to install pip as well.

Once the installation is finished, go into a command prompt and type the following, making sure it installs:
pip install requests

Once tcl/tk and requests have installed, you can run the program. It comes with three different files.
start.py, config.py, and bots.json.

---

start.py is the main program. You can run it using:
python start.py

or if you aren't in the same directory as the program, here's an example if the program was on the desktop:
python C:\\Users\\David\\Desktop\\start.py

config.py can be edited by hand to change:
- api key/secret
- api url
- account type
- If you want to be asked whether you actually want to close the program on shutdown
