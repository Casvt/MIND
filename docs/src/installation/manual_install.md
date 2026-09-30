On this page, you can find instructions on how to manually install MIND (directly on the host) and on how to update your manual installation. Go to the section that is for your OS.

## Installation

!!! note "Ensure correct time"
    Make sure to set all time related settings (time, date, timezone, etc.) correct on your computer, as MIND depends on it to work correctly.

=== "Linux"
    ### Linux

    1. Install Python 3.8 or higher if you don't have it already.

    ```bash
    sudo apt-get install python3
    ```

    2. Install Python PIP if you don't have it already.

    ```bash
    sudo apt-get install python3-pip
    ```

    3. Download the latest MIND release.

    ```bash
    wget https://github.com/Casvt/MIND/releases/latest/download/MIND-release.zip
    ```

    4. Create the MIND application folder. We recommend `/opt/MIND` but you can also put it somewhere else. If you put it somewhere else, replace `/opt/MIND` with the actual location in all commands below.

    ```bash
    sudo mkdir /opt/MIND
    ```

    5. We recommend that you run the application as a different user than root. To do that, the application folder needs to be owned by the user that MIND will run as. Replace `{user}` and `{group}` with the username or ID. If you want to run MIND as root, skip this command. All commands after this one need to be run as the user that MIND will run as. That means either running them as the current user, prepending `sudo` to all commands if you want to run it as root, or logging in as the intended user.

    ```bash
    sudo chown -R {user}:{group} /opt/MIND
    ```

    6. Extract the content of the zipped release into the application folder.

    ```bash
    unzip MIND-release.zip -d /opt/MIND
    ```

    7. Move into the folder.

    ```bash
    cd /opt/MIND
    ```

    8. Install the Python requirements.

    ```bash
    python3 -m pip install -r requirements.txt
    ```

    9. You can now start MIND.

    ```bash
    python3 MIND.py
    ```

=== "macOS"
    ### macOS

    Make sure you are logged in to your macOS device as an admin user.

    1. Install Python 3.8 or higher if you don't have it already. You can install Python 3.14 from [this link](https://www.python.org/ftp/python/3.14.3/python-3.14.3-macos11.pkg).

    2. Download the latest MIND release from [this link](https://github.com/Casvt/MIND/releases/latest/download/MIND-release.zip) and expand the downloaded .zip file.

    3. Rename the resulting `MIND-release` folder to `MIND`.

    4. Place the `MIND` folder in your `/Applications` folder.

    5. Open Terminal and change directory to `/Applications/MIND`.

    ```bash
    cd /Applications/MIND
    ```

    6. Install the Python requirements.

    ```bash
    python3 -m pip install -r requirements.txt
    ```

    7. You can now start MIND.

    ```bash
    python3 MIND.py
    ```

=== "Windows"
    ### Windows

    1. Install Python 3.8 or higher if you don't have it already. You can download the Windows Python installer using [this link](https://www.python.org/ftp/python/pymanager/python-manager-26.0.msix). Make sure to check the box to add Python to PATH when prompted.

    2. Download the latest MIND release from [this link](https://github.com/Casvt/MIND/releases/latest/download/MIND-release.zip).

    3. Extract the zip file to a folder on your machine. We recommend `C:\apps\MIND` but you can also put it somewhere else.

    4. Open up PowerShell and navigate to the application folder.

    ```powershell
    cd C:\apps\MIND
    ```

    5. Install the Python requirements.

    ```powershell
    python -m pip install -r requirements.txt
    ```

    6. You can now start MIND.

    ```powershell
    python MIND.py
    ```

??? info "Command line options"
    If you want to change hosting, database or logging settings on startup, start MIND with the `-h` flag to see the command line options. The reason you might want to change those settings on startup, even though the web-UI offers an interface to change these settings, is that MIND might not be able to start up or be reachable with the default settings (e.g. port 8080 is already in use, so MIND can't start up but you need it started up and reachable to change the port).

Open your browser and access it at [http://localhost:8080/](http://localhost:8080/). See the section below on how to automatically run MIND as a service in the background. Check out the [Setup After Installation](./setup_after_installation.md) page for instructions on how to configure MIND so that it works properly.

## Running as service

The installation instructions have shown you how to start MIND from the terminal, but it's more ideal to run MIND as a service. That means that it can automatically start running when the computer starts up, stay running in the background, and gracefully shut down when the computer powers down.

=== "Linux"
    ### Linux

    We're going to use _systemd_ to run MIND as a service.

    1. Create the service file and open it. In this case we'll use 'nano' to edit the file.

    ```bash
    sudo nano /etc/systemd/system/mind.service
    ```

    2. Now that the file editor is opened, fill it with the following text. It assumes you have MIND installed at `/opt/MIND`. If not, replace the paths with the actual location. Replace `{user}` and `{group}` with the username or ID that the application should be run as. Once you're done, press Ctrl-S and Ctrl-X to save and exit nano.

    ```toml
    [Unit]
    Description=MIND Daemon
    After=syslog.target network.target

    [Service]
    WorkingDirectory=/opt/MIND/
    User={user}
    Group={group}
    UMask=0002
    Restart=on-failure
    RestartSec=5
    Type=simple
    ExecStart=/usr/bin/python3 /opt/MIND/MIND.py
    KillSignal=SIGINT
    TimeoutStopSec=20
    SyslogIdentifier=mind

    [Install]
    WantedBy=multi-user.target
    ```

    3. Reload systemd so that it finds the new service.

    ```bash
    sudo systemctl daemon-reload
    ```

    4. Start the service.

    ```bash
    sudo systemctl start mind
    ```

    Enabling the service will automatically start MIND once the computer starts up.

    ```bash
    sudo systemctl enable mind
    ```

=== "macOS"
    ### macOS

    We're going to use _LaunchAgent_ to run MIND as a service.

    1. Create the service file and open it. In this case we'll use 'nano' to edit the file. Replace `{user_name}` with the name of the user that the application should run as.

    ```bash
    sudo nano /Users/{user_name}/Library/LaunchAgents/com.github.casvt.mind.plist
    ```

    2. Now that the file editor is opened, fill it with the following text. It assumes you have MIND installed at `/Application/MIND`. If not, replace the paths with the actual location. Once you're done, press Ctrl-S and Ctrl-X to save and exit nano.

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.github.casvt.mind</string>

            <key>ProgramArguments</key>
            <array>
            <string>/usr/bin/python3</string>
            <string>/Applications/MIND/MIND.py</string>
            </array>

            <key>WorkingDirectory</key>
            <string>/Applications/MIND</string>

            <key>RunAtLoad</key>
            <true/>

            <key>KeepAlive</key>
            <true/>

            <key>StandardOutPath</key>
            <string>/usr/local/var/log/mind.log</string>

            <key>StandardErrorPath</key>
            <string>/usr/local/var/log/mind.log</string>
        </dict>
    </plist>
    ```

    3. Load the service, start it and enable it so that it automatically starts when the computer starts up.

    ```bash
    launchctl load /Users/{user_name}/Library/LaunchAgents/com.github.casvt.mind.plist
    ```

=== "Windows"
    ### Windows

    We're going to use _nssm_ to run MIND as a service.

    1. Download the latest NSSM release from [this link](https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip).

    2. Extract either the 64 bit or 32 bit executable from the zip file, based on your OS bitness. Place the executable in `C:\Windows\System32`, or add it to your PATH.

    3. Run CMD as an Administrator and use the command `nssm install mind`.

    4. An interface should pop up. Use the following configuration:
        - Path: Should be the path to your Python executable.
        - Startup Directory: Should be the path to your Python installation directory, where the Python executable is in.
        - Arguments: Should be the location of the MIND file. E.g. `C:\apps\MIND\MIND.py`

    5. Under `Process Tab`, make sure to uncheck `Console Windows`.

    6. Click the `Install Service` button.

    7. Use the terminal command `nssm start mind` to start mind and to automatically make it start when the computer starts up.

## Updating

=== "Linux"
    ### Linux

    The commands will assume that the application folder of MIND is at `/opt/MIND`. If MIND is installed somewhere else, then replace the paths in the commands with the actual location.

    1. Shut down MIND. If you're running MIND from a terminal, press Ctrl-C to stop it. If you're running it as a systemd service, you can stop it with the following command:

    ```bash
    sudo systemctl stop mind
    ```

    You can check whether MIND is shut down by trying to access the web-UI. If it can't connect anymore, then MIND is shut down.

    2. The default location of the database file of MIND is at `db/MIND.db` in the application folder. So by default it will be at `/opt/MIND/db/MIND.db`. Temporarily secure this file by completely moving it out of the application folder. You could for example put it in your home directory for the moment. We'll be deleting the application folder so we need to move the database file out of it so that we don't delete the database. If your database file is at a custom location (using the `--DatabaseFolder` command line flag) that is outside of the application folder, then it can remain there and you don't have to move it. If there is also a `MIND.db-shm` file and `MIND.db-wal` file in the database folder, then MIND is still running or was shut down improperly.

    3. Delete the application folder.

    ```bash
    sudo rm -r "/opt/MIND"
    ```

    4. Download the latest MIND release.

    ```bash
    wget https://github.com/Casvt/MIND/releases/latest/download/MIND-release.zip
    ```

    5. Recreate the MIND application folder at the location that it previously was.

    ```bash
    sudo mkdir /opt/MIND
    ```

    6. Change the ownership of the created application folder so that it's owned by the user that ran MIND. Only run this if it wasn't run by root. All commands after this one need to be run as the user that MIND will run as. That means either running them as the current user, prepending `sudo` to all commands if you want to run it as root, or logging in as the intended user.

    ```bash
    sudo chown -R {user}:{group} /opt/MIND
    ```

    7. Extract the content of the new zipped release into the application folder.

    ```bash
    unzip MIND-release.zip -d /opt/MIND
    ```

    8. Move into the folder.

    ```bash
    cd /opt/MIND
    ```

    9. Install the Python requirements. This is needed because it might be the case that requirements have been changed or added.

    ```bash
    python3 -m pip install -r requirements.txt
    ```

    10. Move the database file back into the application folder in the `db/` subfolder. If that folder doesn't exist already, you can create it and put the file in there, exactly like it was in the old installation. If you have your database file at a custom location outside of the application folder, then you can leave it there.

    11. Start MIND back up. If you were running it in a terminal, then run the following command (with the `--DatabaseFolder` flag if your database is at a custom location).

    ```bash
    python3 MIND.py
    ```

    If you were running it as a systemd service, then run this command:

    ```bash
    sudo systemctl start mind
    ```

=== "macOS"
    ### macOS

    Make sure you are logged in to your macOS device as an admin user.

    The commands will assume that the application folder of MIND is at `/Applications/MIND`. If MIND is installed somewhere else, then replace the paths in the commands with the actual location.

    1. Shut down MIND. If you're running MIND from a terminal, press Ctrl-C to stop it. If you're running it as a LaunchAgent service, you can stop it with the following command. Replace {user_name} with the name of the user that the application runs as.

    ```bash
    launchctl unload /Users/{user_name}/Library/LaunchAgents/com.github.casvt.mind.plist
    ```

    You can check whether MIND is shut down by trying to access the web-UI. If it can't connect anymore, then MIND is shut down.

    2. The default location of the database file of MIND is at `db/MIND.db` in the application folder. So by default it will be at `/Applications/MIND/db/MIND.db`. Temporarily secure this file by completely moving it out of the application folder. You could for example put it on your desktop for the moment. We'll be deleting the application folder so we need to move the database file out of it so that we don't delete the database. If your database file is at a custom location (using the `--DatabaseFolder` command line flag) that is outside of the application folder, then it can remain there and you don't have to move it. If there is also a `MIND.db-shm` file and `MIND.db-wal` file in the database folder, then MIND is still running or was shut down improperly.

    3. Delete the application folder at `/Applications/MIND`.

    ```bash
    rm -r "/Applications/MIND"
    ```

    4. Download the latest MIND release from [this link](https://github.com/Casvt/MIND/releases/latest/download/MIND-release.zip) and expand the downloaded .zip file.

    5. Rename the resulting `MIND-release` folder to `MIND`.

    6. Place the `MIND` folder in your `/Applications` folder.

    7. Open Terminal and change directory to `/Applications/MIND`.

    ```bash
    cd /Applications/MIND
    ```

    8. Install the Python requirements. This is needed because it might be the case that requirements have been changed or added.

    ```bash
    python3 -m pip install -r requirements.txt
    ```

    9. Move the database file back into the application folder in the `db/` subfolder. If that folder doesn't exist already, you can create it and put the file in there, exactly like it was in the old installation. If you have your database file at a custom location outside of the application folder, then you can leave it there.

    10. Start MIND back up. If you were running it in a terminal, then run the following command (with the `--DatabaseFolder` flag if your database is at a custom location).

    ```bash
    python3 MIND.py
    ```

    If you were running it as a LaunchAgent service, then run the following command. Replace {user_name} with the name of the user that the application ran as.

    ```bash
    launchctl load /Users/{user_name}/Library/LaunchAgents/com.github.casvt.mind.plist
    ```

=== "Windows"
    ### Windows

    The commands will assume that the application folder of MIND is at `C:\apps\MIND`. If MIND is installed somewhere else, then replace the paths in the commands with the actual location.

    1. Shut down MIND. If you're running MIND from a terminal, press Ctrl-C to stop it. If you're running it as a nssm service, you can stop it with the following command:

    ```powershell
    nssm stop mind
    ```

    You can check whether MIND is shut down by trying to access the web-UI. If it can't connect anymore, then MIND is shut down.

    2. The default location of the database file of MIND is at `db\MIND.db` in the application folder. So by default it will be at `C:\apps\MIND\db\MIND.db`. Temporarily secure this file by completely moving it out of the application folder. You could for example put it on your desktop for the moment. We'll be deleting the application folder so we need to move the database file out of it so that we don't delete the database. If your database file is at a custom location (using the `--DatabaseFolder` command line flag) that is outside of the application folder, then it can remain there and you don't have to move it. If there is also a `MIND.db-shm` file and `MIND.db-wal` file in the database folder, then MIND is still running or was shut down improperly.

    3. Delete the application folder at `C:\apps\MIND`.

    4. Download the latest MIND release from [this link](https://github.com/Casvt/MIND/releases/latest/download/MIND-release.zip).

    5. Extract the zip file to the same folder as where the application folder previously was (`C:\apps\MIND`).

    6. Open up PowerShell and navigate to the application folder.

    ```powershell
    cd C:\apps\MIND
    ```

    7. Install the Python requirements. This is needed because it might be the case that requirements have been changed or added.

    ```powershell
    python -m pip install -r requirements.txt
    ```

    8. Move the database file back into the application folder in the `db\` subfolder. If that folder doesn't exist already, you can create it and put the file in there, exactly like it was in the old installation. If you have your database file at a custom location outside of the application folder, then you can leave it there.

    9. Start MIND back up. If you were running it in a terminal, then run the following command (with the `--DatabaseFolder` flag if your database is at a custom location).

    ```powershell
    python MIND.py
    ```

    If you were running it as a nssm service, then run this command:

    ```powershell
    nssm start mind
    ```

After updating, it might take a little longer for MIND to start up in the sense of the web-UI becoming available. That is because MIND is moving things around inside the database to support the new features. It's a one-time event that happens after updating. It can take from a few seconds for small libraries to a few minutes for massive libraries.
