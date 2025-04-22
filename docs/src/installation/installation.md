Installing MIND can be done via Docker or via a manual instal. Docker requires less setup and has better support, but if your OS/system does not support Docker, you can also instal MIND directly on your OS via a manual instal.

!!! success "Recommended Installation"
    The recommended way to instal MIND is using Docker.

For instructions on installing MIND using Docker, see the [Docker installation instructions](./docker.md). For instructions on installing Kapowarr via a manual instal, see the [manual installation instructions](./manual_instal.md).

The [Setup After Installation page](./setup_after_installation.md) contains the basic steps to take after installing MIND. It's advised to check it out.

Updating an installation can also be found on the installation pages of the respective installation method.

## Quick Instructions

If you already have experience with Docker, then below you can find some quick instructions to get MIND up and running fast. If you need some more guidance, follow the full guide for [Docker](./docker.md) or [a manual instal](./manual_instal.md).

Replace the timezone value (`TZ=`) with the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage). The database will be stored in a Docker volume. 

=== "Docker CLI"
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

=== "Docker Compose"

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
