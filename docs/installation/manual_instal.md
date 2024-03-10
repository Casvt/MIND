On this page, you can find instructions on how to manually instal MIND (directly on the host) and on how to update your manual installation.

## Installation

### Time settings

Make sure to set all time related settings (time, date, timezone, etc.) correct on your computer, as MIND depends on it to work correctly.

### Installing MIND

!!! warning
	These instructions are still under construction.

=== "Windows"
    On Windows, there are a couple of extra steps involved.  

    1. [Download and instal Python](https://www.python.org/downloads/). This is the framework MIND runs on top of.  
       _Make sure you select to add Python to PATH when prompted. This will make installing requirements much easier._
    2. Download (or clone) the [latest MIND release](https://github.com/Casvt/MIND/releases/latest).  
    3. Extract the zip file to a folder on your machine.  
       We suggest something straightforward - `C:\apps\MIND` is what we'll use as an example.
    4. Instal the required python modules (found in `requirements.txt`).
       This can be done from a command prompt, by changing to the folder you've extracted MIND to and running a python command.
       ```powershell
       cd C:\apps\MIND
       python -m pip install -r requirements.txt
       ```
    5. Run MIND with the command `python C:\apps\MIND\mind.py`.
    6. Access MIND with the IP of the host machine and port 8080.  
       If it's the machine you're using, try [http://localhost:8080](http://localhost:8080)
    
    If you want MIND to run in the background, without you having to start it each time your machine restarts, a tool called [nssm](https://nssm.cc/download) will allow you to configure MIND to run as a system service. It is recommended that you set it up as above before doing this, as it will allow you to see any errors you may encounter on screen (instead of having nssm intercept them).

=== "Ubuntu"
	```bash
	sudo apt-get install git python3-pip
	sudo git clone https://github.com/Casvt/MIND.git /opt/MIND
	cd /opt/MIND
	python3 -m pip install -r requirements.txt
	python3 MIND.py
	```

=== "macOS"
    Use docker.  
    Permissions on macOS (and GateKeeper) make this needlessly complex.  

## Updating instal

Coming Soon.