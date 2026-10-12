On this page, you can find instructions on how to install MIND using Docker and how to update a Docker installation.

## Installation

### Time settings

Make sure to set all time related settings (time, date, timezone, etc.) correct on your computer, as MIND depends on it to work correctly.

### Install Docker

The first step is to install Docker if you don't have it installed already. The official Docker documentation hub offers great instructions on [how to install docker CLI and Docker Desktop](https://docs.docker.com/engine/install/). Take notice of whether you installed the 'Docker CLI' (the Docker documentation also calls this 'Docker CE') or 'Docker Desktop', for future instructions.

??? info "Quick introduction to Docker"
	Docker allows you to create little virtual computers, called 'containers'. You can run an application inside these containers. This is useful because you decide how much resources these containers can use, and what access these applications get to "the outside". It makes it safer and installation easier. It makes it safer because the application only has access to folders on the computer that you explicitly give it access to, and makes installation easier because you don't have to make sure that everything is set up properly, as the developer will ensure that.
	
	Allowing folders and network connections through the container is done using 'mapping'. For example, you can map the folder `D:\MIND_db` on the host to the folder `/app/db` inside the container. Then everything in the host folder is visible to the application via the folder mapped inside the container. Mapping network ports works in a similar manner.
	
	When you turn off a container, all changes to files and folders inside the container are lost (e.g. the database). This is so that the environment inside the container is always the same when starting up. In order to save a file/folder permanently, it has to be stored on the host and then mapped to somewhere inside the container.

### Create place for the database

MIND needs a permanent place to put the database file. This can be a [Docker volume](https://docs.docker.com/storage/volumes/) or a folder on the host machine.

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
		Following the Linux standards, we suggest the folder `/opt/MIND/db`. This is not mandatory however. You are allowed to create a folder anywhere you like.

		If your Linux distro offers it, create the desired folder using the UI. Otherwise, create it with the following shell command (replace `/path/to/directory` with the desired path):

		```bash
		mkdir "/path/to/directory"
		```

		The user that the container runs as will need read, write and execution permissions. You can change the user that the container runs as using the PUID (user) and PGID (group) environment variables when launching the container later. The folder also needs to either be owned by that user, be owned by a group that the user is a part of, or have sufficient permissions so that _any_ user can use the folder.

	=== "MacOS"
		Following MacOS standards, we suggest the folder `/Applications/MIND/db`. This is not mandatory however. You are allowed to create a folder anywhere you like.

		Create the desired folder using the UI or with the following shell command (replace `/path/to/directory` with desired path):

		```bash
		mkdir "/path/to/directory"
		```

		The user that the container runs as will need read, write and execution permissions. You can change the user that the container runs as using the PUID and PGID (for the group) environment variables when launching the container later. The folder also needs to either be owned by that user, be owned by a group that the user is a part of, or have sufficient permissions so that _any_ user can use the folder.

	=== "Windows"
		There is no defined standard for Windows on where to put such a folder. We suggest a path like `C:\apps\MIND\db` or `D:\MIND\db`. This is not mandatory however. You are allowed to create a folder anywhere you like.

		Create the desired folder either using the Windows Explorer or using the following Powershell command:

		```powershell
		mkdir "C:\path\to\directory"
		```

### Launch container

Now we can launch the container.

=== "Docker CLI"
	The command to get the Docker container running can be found below. But before you copy, paste and run it, read the notes below!

	=== "Linux"

		```bash
		docker run -d \
			--name mind \
			--restart unless-stopped \
			-v "mind-db:/app/db" \
			-p 8080:8080 \
			-e TZ=Etc/UTC \
			-e PUID=0 \
			-e PGID=0 \
			mrcas/mind:latest
		```

	=== "MacOS"

		```bash
		docker run -d \
			--name mind \
			--restart unless-stopped \
			-v "mind-db:/app/db" \
			-p 8080:8080 \
			-e TZ=Etc/UTC \
			-e PUID=0 \
			-e PGID=0 \
			mrcas/mind:latest
		```

	=== "Windows"

		```powershell
		docker run -d --name mind --restart unless-stopped -v "mind-db:/app/db" -p 8080:8080 -e TZ=Etc/UTC -e PUID=0 -e PGID=0 mrcas/mind:latest
		```

	A few notes about this command:

	1. If you're using a folder on the host machine instead of a docker volume to store the database file, replace `mind-db` with the path to the host folder. It's mapped to `/app/db` inside the container.

	!!! example "Examples"
		- `-v "/opt/MIND/db:/app/db"`
		- `-v "C:\apps\MIND\db:/app/db"`

	2. If you want to run MIND on a different port, you can do that by replacing the left `8080` with the desired port.
	
	!!! example "Examples"
		- `-p 8009:8080` to be available on `8009`
		- `-p 443:8080` to be available on `443`
		- `-p 8080:8080` to be available on `8080`

	3. You can change the user and group that the application inside the container runs as using the PUID (user) and PGID (group) environment variables.
	
	4. Set the `TZ` environment variable to the [timezone database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).

=== "Docker Compose"
	The contents of the `docker-compose.yml` file are below. The source file can also be found [on GitHub](https://github.com/Casvt/MIND/blob/Main/docker-compose.yml). But before you copy, paste and run it, read the notes below!

	```yml
	services:
		mind:
			container_name: mind
			image: mrcas/mind:latest
			restart: unless-stopped
			environment:
				- PUID=0
				- PGID=0
				- TZ=Etc/UTC
			volumes:
				- "mind-db:/app/db"
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

	1.  If you're using a folder on the host machine instead of a docker volume to store the database file, replace `mind-db` with the path to the host folder. It's mapped to `/app/db` inside the container.

	!!! example "Examples"
		- `- "/opt/MIND/db:/app/db"`
		- `- "C:\apps\MIND\db:/app/db"`

	2. If you want to run MIND on a different port, you can do that by replacing the left `5656` with the desired port.
	
	!!! example "Examples"
		- `- 8009:8080` to be available on `8009`
		- `- 443:8080` to be available on `443`
		- `- 8080:8080` to be available on `8080`

	3. You can change the user and group that the application inside the container runs as using the PUID (user) and PGID (group) environment variables.
	
	4. Set the `TZ` environment variable to the [timezone database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).

=== "Docker Desktop"
	1. Click the search bar at the top and search for `mrcas/mind`.
	
	2. Click `Run` on the entry saying `mrcas/mind`.
	
	3. Open `Images` and on the right, under `Actions`, click the play/run button for `mrcas/mind`.
	
	4. Expand the 'Optional settings'.
	
	5. For the `Container name`, set the value to `mind`.
	
	6. For the `Host port`, set the value to `8080`. Set it to a different value if you want to run MIND on a different port.
	
	7. For the `Host path`, set the value to `mind-db` if you are using a Docker volume for the database. Otherwise, set it to the path to the folder on the host. Set the accompanying `Container path` to `/app/db`.
	
	8. Under `Environment Variables`, set the `Variable` field to `TZ` and the `Value` field to the [timezone database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage).
	
	9. You can change the user and group that the application inside the container runs as using the PUID (user) and PGID (group) environment variables. If so, add another environment variable using the plus button on the right. Set the `Variable` field to `PUID` and the `Value` field to the ID of the desired user. Add yet another environment variable using the plus button on the right. Set the `Variable` field to `PGID` and the `Value` field to the ID of the desired group.

### Check Setup After Installation

Now that the container is up and running, you can access it at [http://localhost:8080](http://localhost:8080). Check out the [Setup After Installation](./setup_after_installation.md) page for instructions on how to configure MIND so that it works properly.

## Updating

Below you can find instructions on how to update an install.

=== "Docker CLI"
	If needed, run these commands with `sudo`. It is assumed that the name of the container is `mind` (which is set using the `--name` option in the command).

	1. `docker container stop mind`
	2. `docker container rm mind`
	3. `docker image rm mrcas/mind:latest`
	4. Repeat the steps of [launching the container](#launch-container).

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
