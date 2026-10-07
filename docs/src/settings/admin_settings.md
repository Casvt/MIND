Here you can find documentation on the admin settings, which are the settings available in the admin panel.

## Authentication

### Allow New Accounts

Whether people that access the web-ui have the option to create an account. When disabled, it is not possible for them to create new accounts. The admin has to do it from the admin panel.

### Login Time

How long users stay logged in before they have to authenticate again.

### Login Time Trigger

Whether to reset the login timer (a.k.a. the authentication timeout) when using MIND. If the value is set to `After Login`, the timer will start counting after the user has logged in and will force the user the authenticate again once it has run out. If the value is set to `After Last Use`, the timer will start counting after the last time the user used MIND. So if the timeout is long enough that the user will consistently use MIND more regularly than the timeout duration, the user wouldn't need to authenticate ever again (until they don't use MIND for long enough that the timer runs out).

## Hosting

This section defines how MIND hosts the web-UI. Changing any setting here will make MIND automatically restart after saving. Log back into the admin panel within 60 seconds for the changes to stay, or they will be reverted.

### Host

This tells MIND what IP to bind to. Using `0.0.0.0` will have MIND bind to all interfaces it finds on the host machine. You can also enter an IPv6 address.

_Note: this setting is not applicable if you have MIND deployed using Docker._

### Port

This tells MIND what port to listen on. The default is `8080`, which would put the MIND UI on `http://{HOST}:8080/`.

If you have MIND deployed using Docker, do not change this setting but instead follow the instructions below:

=== "Docker CLI"
    Alter the command to run the container by replacing `-p 8080:8080` with `-p {PORT}:8080`, where `{PORT}` is the desired port (e.g. `-p 8009:8080`). Run the container with the new version of the command (you will need to remove the old container if you had it running before).

=== "Docker Compose"
    Alter the file to run the container and replace `- 8080:8080` with `- {PORT}:8080`, where `{PORT}` is the desired port (e.g. `- 8009:8080`). Then re-run the container with the new version of the file.

=== "Docker Desktop"
	1. Open `Containers` and locate the `mind` container in the list.
	2. Click the stop button on the right, then the delete button.
	3. Follow the [instructions for launching the container](../installation/docker.md#launch-container), starting from step 3. At step 6, set the value to the desired port. For example, if you set it to `8009`, the web-UI will then be accessible via `http://{host}:8009/`. Continue following the rest of the steps.

### URL Prefix

If you want to put MIND behind a proxy so that you can access the web-UI via a nice URL, set a URL prefix (it must start with a `/` character). Set it empty to disable.

To get MIND running on `http://example.com/mind`, you would set your reverse proxy to forward the `/mind` path to the IP and port of your MIND instance, and set the URL prefix to `/mind`.

## Logging

### Logging Level

Keep this at `Info` in normal situations. If you encounter a problem and need to share logs, set this to `Debug` and recreate the problem. Then download the logs and set the log level back to `Info` again.

## Database Backup Settings

### Database Backup Interval

How often a backup of the database should be made.

### Database Backup Retention

The amount of backups to keep. If a new backup is made and the maximum amount of backups have already been made, then the oldest one is deleted. For example, if a backup is made once per day and the retention is set to 3 backups, then you'll have a backup of each of the last 3 days.

### Database Backup Folder

The folder that the database backups are put in. By default this is the same folder that the active database file is in, but you can change it so that the database backups are stored somewhere else.
