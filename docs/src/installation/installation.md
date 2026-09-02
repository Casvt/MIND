# Installation and Updating

## Installation Method

MIND supports multiple installation methods. The two most common methods are using Docker and directly on your computer. The recommended method is Docker. Choose an installation method:

<div class="button-container">
	<a href="../docker">Docker</a>
	<a href="../manual_install">Manual Install</a>
</div>

After installing MIND, there is some configuration needed so that it can start working and act to your preferences. It's advised to visit the [Setup After Installation page](./setup_after_installation.md) after installation for more information.

Instructions on how to update an installation can be found on the pages of the respective installation method.

## Quick Instructions

If you already have experience with Docker, then below you can find some quick instructions to get MIND up and running fast. If you need some more guidance, follow the full guide for [Docker](./docker.md) or [a manual install](./manual_install.md).

Replace the timezone value (`TZ=`) with the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) of your timezone (value of `TZ identifier` on webpage). The database will be stored in a Docker volume. 

=== "Docker CLI"
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

=== "Docker Compose"

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
