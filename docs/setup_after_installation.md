# Setup After Installation

After installing MIND, you should have access to the web-ui. MIND needs some configuration in order for it to work properly.

## Port

The first thing to do is decide if you want to leave MIND running on the default port of `8080`. If you _do_, you can go to the next step. If you want to _change_ the port, continue reading.

=== "Docker CLI"
	Alter the command to run the container and replace `-p 8080:8080` with `-p {PORT}:8080`, where `{PORT}` is the desired port (e.g. `-p 8009:8080`). Then run the container with the new version of the command.

=== "Docker Compose"
	Alter the file to run the container and replace `- 8080:8080` with `- {PORT}:8080`, where `{PORT}` is the desired port (e.g. `- 8009:8080`). Then run the container with the new version of the file.

=== "Manual Install"
	Inside the `MIND.py` file at the top, you can set the port via the `PORT` variable. Change it from `PORT = '8080'` to `PORT = '{PORT}'`, where `{PORT}` is the desired port (e.g. `PORT = '8009'`). Then restart the application.

## Creating an account

When accessing the web-ui, you'll be prompted to log in. Click on `Or create an account`, enter the desired username and password for the account and click `Create`. The account is created and can now be logged in with. The complete authentication process is local and no data is shared with any other service.

## Add a notification service

A notification service is a way of sending a notification. For example an e-mail to a group of people or a PushBullet notification to a specific device. What the actual content of the notification is, is decided by the title and text of the reminder. The notification service only specifies in which way the title and text is sent. You set it up once, and then you can select it when creating a reminder. A notification service consists of a title (name) and an Apprise URL. See the [Apprise URL documentation](https://github.com/caronc/apprise#supported-notifications) to learn how to make a valid Apprise URL.
