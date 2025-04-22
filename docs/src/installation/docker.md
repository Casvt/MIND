On this page, you can find instructions on how to instal MIND using Docker and how to update a Docker installation.

## Installation

### Time settings

Make sure to set all time related settings (time, date, timezone, etc.) correct on your computer, as MIND depends on it to work correctly.

### Instal Docker

The first step is to instal Docker, if you don't have it installed already. The official Docker documentation hub offers great instructions on [how to instal docker CLI and Docker Desktop](https://docs.docker.com/engine/install/). Take notice of if you installed the 'Docker CLI' (the Docker documentation also calls this 'Docker CE') or if you installed 'Docker Desktop', for future instructions.

### Create Docker volume or folder

MIND needs a permanent place to put the database file, which contains all the user data and configs. This can be a [Docker volume](https://docs.docker.com/storage/volumes/), or a folder on the host machine.

=== "Docker Volume"
	=== "Docker CLI"

		```bash
		docker volume create mind-db
		```

	=== "Docker Compose"

		```bash
		docker volume create mind-db
		```

	=== "Docker Desktop"
		- Open `Volumes`
		- Click `Create`
		- Enter `mind-db` for the name and click `Create`

=== "Local Folder"
	=== "Linux"
		Linux standards would suggest putting the folder in `/opt/application_name`, as the `/opt` directory is where program options should be stored. This is not mandatory however; you are allowed to create a folder anywhere you like. If we apply the standard to MIND, the folder would be `/opt/MIND/db`.

		Create the desired folder using the UI (if your distro offers this) or with the following shell command (replace `/path/to/directory` with desired path):

		```bash
		mkdir "/path/to/directory"
		```

		!!! info "Permissions and ownership"
			The permissions on this folder need to allow the container to read, write, and execute inside it. It also needs to have proper ownership. More documentation on this subject coming.

	=== "MacOS"
		MacOS standards would suggest putting the folder in `/Applications/application_name`. This is not mandatory however; you are allowed to create a folder anywhere you like. If we apply the standard to MIND, the folder would be `/Applications/MIND/db`.

		Create the desired folder using the UI or with the following shell command (replace `/path/to/directory` with desired path):

		```bash
		mkdir "/path/to/directory"
		```

		!!! info "Permissions and ownership"
			The permissions on this folder need to allow the container to read, write, and execute inside it. It also needs to have proper ownership. More documentation on this subject coming.

	=== "Windows"
		There is no defined standard for Windows on where to put such a folder. We suggest a path like `C:\apps\application_name`, so that it can be managed easily. This is not mandatory however; you are allowed to create a folder anywhere you like. If we apply this suggestion to MIND, the folder would be `C:\apps\MIND\db`.
		
		Create the desired folder either using the Windows Explorer, or using the following Powershell command:

		```powershell
		mkdir "C:\apps\MIND\db"
		```

		!!! info "Permissions and ownership"
			The permissions on this folder need to allow the container to read, write, and execute inside it. It also needs to have proper ownership. More documentation on this subject coming.

### Launch container

Now we can launch the container.

=== "Docker CLI"
	The command to get the Docker container running can be found below. But before you copy, paste and run it, read the notes below!

	=== "Linux"

		```bash
		docker run -d \
			--name mind \
			-v "mind-db:/app/db" \
			-e TZ=Europe/Amsterdam \
			-p 8080:8080 \
			mrcas/mind:latest
		```

	=== "MacOS"

		```bash
		docker run -d \
			--name mind \
			-v "mind-db:/app/db" \
			-e TZ=Europe/Amsterdam \
			-p 8080:8080 \
			mrcas/mind:latest
		```

	=== "Windows"

		```powershell
		docker run -d --name mind -v "mind-db:/app/db" -e TZ=Europe/Amsterdam -p 8080:8080 mrcas/mind:latest
		```

	A few notes about this command:

	1. If you're using a folder on the host machine instead of a docker volume to store the database file ([reference](#create-docker-volume-or-folder)), replace `mind-db` with the path to the host folder.  
	E.g. `"/opt/MIND/db:/app/db"`.  
	E.g. `"C:\apps\MIND\db:/app/db"`.

	2. Replace the timezone value (`TZ=`) with the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).

	3. Information on how to change the port can be found on the [Setup After Installation page](./setup_after_installation.md#port).

=== "Docker Compose"
	The contents of the `docker-compose.yml` file are below. The source file can also be found [on GitHub](https://github.com/Casvt/MIND/blob/Development/docker-compose.yml). But before you copy, paste and run it, read the notes below!

	```yml
	version: "3.3"
	services:
	  mind:
	    container_name: mind
	      image: mrcas/mind:latest
	      volumes:
	        - "mind-db:/app/db"
	      environment:
	        - TZ=Europe/Amsterdam
	      ports:
	        - 8080:8080

	volumes:
	  mind-db:	
	```
	
	Then run the following command to start the container. Run this command from within the directory where the `docker-compose.yml` file is located.

	```bash
	docker-compose up -d
	```	

	A few notes about the `docker-compose.yml` file:

	1. If you're using a folder on the host machine instead of a docker volume to store the database file ([reference](#create-docker-volume-or-folder)), replace `mind-db` with the path to the host folder.  
	E.g. `"/opt/MIND/db:/app/db"`.  
	E.g. `"C:\apps\MIND\db:/app/db"`.

	2. Replace the timezone value (`TZ=`) with the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).

	3. Information on how to change the port can be found on the [Setup After Installation page](./setup_after_installation.md#port).

=== "Docker Desktop"
	1. Click the search bar at the top and search for `mrcas/mind`.
	2. Click `Run` on the entry saying `mrcas/mind`.
	3. Open `Images`, and on the right, under `Actions` click the play/run button for `mrcas/mind`.
	4. Expand the 'Optional settings'.
	5. For the `Container name`, set the value to `mind`.
	6. For the `Host port`, set the value to `8080`. Information on how to change the port can be found on the [Setup After Installation page](./setup_after_installation.md#port).
	7. For the `Host path`, set the value to `mind-db` if you are using a Docker volume for the database. Otherwise, set it to the folder where you want to store the database, [that you created earlier](#create-docker-volume-or-folder). Set the accompanying `Container path` to `/app/db`.
	8. For the `Variable`, set the value to `TZ`. Set the accompanying `Value` to the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage). E.g. `Europe/Amsterdam`.


## Update instal

Below you can find instructions on how to update an instal.

=== "Docker CLI"
	If needed, run these commands with `sudo`. It is assumed that the name of the container is `mind` (which is set using the `--name` option in the command).

	1. `docker container stop mind`
	2. `docker container rm mind`
	3. `docker image rm mrcas/mind:latest`
	4. Run the command you previously used to start the container.

=== "Docker Compose"
	If needed, run these commands with `sudo`. You need to be in the same directory as the `docker-compose.yml` file when running these commands.
	
	1. `docker-compose down`
	2. `docker-compose pull`
	3. `docker-compose up -d`
	4. `docker image prune -f`

=== "Docker Desktop"
	1. Open `Containers` and locate the `mind` container in the list.
	2. Click the stop button on the right, then the delete button.
	3. Open `Images` and locate the `mrcas/mind` image in the list.
	4. Click the delete button on the right.
	5. Repeat the steps of [launching the container](#launch-container).
