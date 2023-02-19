Upon installing Python, ensure you customize your installation and have tcl/tk installed:
https://stackoverflow.com/a/63032937/9614384
Also make sure you click to install pip as well.

---

Once the installation is finished..

if using Windows: go into a command prompt and type the following to install requests: ``pip install requests``

if using Linux: create a virtual enviroment ( virtualenv -p python3 /home/user/venv ) and install requests: ``~/venv/bin/pip install requests``

---

Once tcl/tk and requests have installed, you can run the program.
It comes with two different files: ``start.py`` and ``config.py``.

start.py is the main program. 

if you aren't in the same directory as the program, here's an example if the program was on the desktop:

if using Windows: ``python C:\\Users\\David\\Desktop\\start.py``

if using Linux: ``~/venv/bin/python ~/Desktop/start.py``

---

config.py can be edited by hand to change:
- api key/secret
- api url
- account type
- If you want to be asked whether you actually want to close the program on shutdown
