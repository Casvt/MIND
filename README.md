# MIND Reminders
A simple self hosted reminder platform that uses push to send notifications to your device. Set the reminder and forget about it! 📢

Mind is a simple self hosted application for creating reminders that get pushed to your device using the [Apprise](https://github.com/caronc/apprise) API. You can send messages to just about every platform, including scheduled emails!

## Screenshots
![mind-reminders-home](https://user-images.githubusercontent.com/57927413/213593220-495aeb86-2bf8-4c43-895d-c7cba38c3cee.png)

![mind-reminders-add-notification-services](https://user-images.githubusercontent.com/57927413/212755314-1104531e-7feb-4e59-af1d-927576e47152.png)

![mind-reminders-edit](https://user-images.githubusercontent.com/57927413/213594471-ecc99a72-cf0f-4570-8e78-92ffbf37e59d.png)

![mind-reminders-settings](https://user-images.githubusercontent.com/57927413/212755327-b45da53c-72f7-480c-9a77-eaad28803fbb.png)

## Core Features
* Basic auth
* Utilizes Apprise
* Create, edit and delete reminders
* Schedule reminders
* Recurring reminders
* Docker image
* Mobile friendly

## Planned Features
You can see our planned features in our [Project board](https://github.com/users/Casvt/projects/3).

## Installation
Replace the timezone value (`TZ=`) to the [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) of your timezone!
```bash
docker run -d \
	--name mind \
	-v mind-db:/app/db \
	-e TZ=Europe/Amsterdam \
	-p 8080:8080 \
	mrcas/mind:latest
```
## Getting Started
- Create a new account
- Click the bell icon on the left side to add an Apprise push option and save it (Here is an example using Pushover)

![mind-reminders-notification-service](https://user-images.githubusercontent.com/57927413/213593832-6c62307c-cf7c-4d11-b6ce-dea33676d477.png)


- Click the home icon and create a reminder!

You can see the [wiki](https://github.com/Casvt/MIND/wiki) for instructions on how to install MIND on other OS'es.
