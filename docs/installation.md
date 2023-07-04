# Installation

The recommended way to install MIND is using Docker. After installing MIND, it is advised to read the [Setup After Installation page](setup_after_installation.md).

NOTE: Make sure to set all time related settings (time, date, timezone, etc.) correct on your computer, as MIND depends on it to work correctly.

## Docker

### Database location

We first need to create a named volume, or a folder, to store the database file of MIND in.

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
	
=== "Folder"
	Linux standards suggest to put the database in `/opt/application_name`, as the `/opt` directory is where program options should be stored. In this case, you'd create the desired folder using the following command:
	```bash
	mkdir /opt/MIND/db
	```

### Run the container

Now that we can store the database somewhere, we can get the container running.

=== "Docker CLI"
	The command to get the docker container running can be found below. Replace the timezone value (`TZ=`) with the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).
	```bash
	docker run -d \
		--name mind \
		-v mind-db:/app/db \
		-e TZ=Europe/Amsterdam \
		-p 8080:8080 \
		mrcas/mind:latest
	```

=== "Docker Compose"
	The contents of the `docker-compose.yml` file would look like below. Replace the timezone value (`TZ=`) with the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).
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
	Now run the compose by running the following command in the root folder:
	```bash
	docker compose up -d
	```

If you didn't name your docker volume `mind-db` (see [Database location](#database-location)), replace `mind-db` in the command with the name of your volume. If you created a folder, replace `mind-db` with `/opt/MIND/db` or the folder you want.

Information on how to change the port can be found on the [Setup After Installation page](setup_after_installation.md#port).

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
	python -m pip install -r requirements.txt
	```
	7. Type the following command:
	```bash
	python MIND.py
	```
