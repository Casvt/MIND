# Installation

The recommended way to install MIND is using Docker. After installing MIND, it is advised to read the [Setup After Installation page](setup_after_installation.md).

NOTE: Make sure to set all time related settings (time, date, timezone, etc.) correct on your computer, as MIND depends on it to work correctly.

## Docker

=== "Docker CLI"
	The command to get the docker container running can be found below. Replace the timezone value (`TZ=`) to the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) of your timezone.
	```bash
	docker run -d \
		--name mind \
		-v mind-db:/app/db \
		-e TZ=Europe/Amsterdam \
		-p 8080:8080 \
		mrcas/mind:latest
	```
=== "Docker Compose"
	The contents of the `docker-compose.yml` file would look like below. Replace the timezone value (`TZ=`) to the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) of your timezone.
	```yml
	version: '3.3'
	services:
		mind:
			container_name: mind
			volumes:
				- 'mind-db:/app/db'
			environment:
				- TZ=Europe/Amsterdam
			ports:
				- '8080:8080'
			image: 'mrcas/mind:latest'
	```

Information on how to change the port can be found on the [Setup After Installation page](setup_after_installation.md#port).

Using a named volume in docker requires you to create the volume before you can use it (see [Named Volumes](#named-volumes)).

### Named Volumes

=== "Docker CLI"
    ```bash
    docker volume create mind-db
    ```

=== "Portainer"
    - Open `Volumes`
    - Click `Add Volume`
    - Enter name matching the one you'll use in compose (`mind-db`, in the above provided command)
    - Click `Create the volume`
    - Open `Stacks`
    - Create the stack with the named volume in it.

Both of these options will create a named volume that you can then use in the command above.  
If you'd prefer to use a local folder on the host machine for storing config, Linux standards would suggest putting that in `/opt/application_name`, as the `/opt` directory is where program options should be stored. 
In this case, you'd create the desired folder with something like `mkdir /opt/MIND/db`, and replace 'mind-db:/app/db' with '/opt/MIND/db:/app/db'.

## Manual Install

See below for installation instructions for your OS if you want to install it manually.

=== "Linux / MacOS"
	```bash
	sudo apt-get install git python3-pip
	sudo git clone https://github.com/Casvt/MIND.git /opt/MIND
	cd /opt/MIND
	python3 -m pip install -r requirements.txt
	python3 MIND.py
	```
=== "Windows"
	1. Install python [in the Microsoft Store](https://www.microsoft.com/store/productId/9PJPW5LDXLZ5)
	2. Install pip [using these instructions](https://www.liquidweb.com/kb/install-pip-windows/)
	3. Download [the latest release](https://github.com/Casvt/MIND/zipball/master)
	4. Extract the ZIP file
	5. With the folder open, right click and select `Open in Terminal`
	6. Type the following command:
	```bash
	python3 -m pip install -r requirements.txt
	```
	7. Type the following command:
	```bash
	python3 MIND.py
	```
