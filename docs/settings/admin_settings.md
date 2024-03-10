Here you can find documentation on the admin settings, which are the settings available in the admin panel.

## Authentication

### Allow New Accounts

Whether or not people that access the web-ui have the option to create an account. When disabled, it is not possible to create new accounts, except for the admin via the admin panel.

### Login Time

The authentication timeout. For how long users stay logged in before they have to authenticate again.

### Login Time Trigger

Whether or not to reset the login timer (A.K.A. the authentication timeout) when using MIND. If the value is set to `After Login`, the timer will start counting after the user has logged in and will force the user the authenticate again once it has run out. If the value is set to `After Last Use`, the timer will start counting after the last time the user used MIND. So if the timeout is long enough that the user will consistently use MIND more regularly than the timeout duration, the user wouldn't need to authenticate ever again (until they don't use MIND for long enough that the timer runs out).

## Logging

### Logging Level

Keep this at `Info` in normal situations. If you encounter a problem and need to share logs, set this to `Debug` and recreate the problem. Then set it back to `Info` again. More information on this on the ['Reporting' page](../other_docs/reporting.md) and [general info page on the admin panel](../general_info/admin_panel.md#logging).

## Hosting

Any changes to these settings will restart MIND immediately. The changes are applied and MIND will start running with the new hosting settings. **_If you do not log into the admin panel within one minute after restarting, the changes will be reverted._** This means that MIND will basically 'try out' the new hosting settings for one minute. If you haven't logged into the admin panel within that one minute after restart, the changes will be canceled, the old hosting settings will be applied and MIND will be restarted again. By logging into the admin panel, you keep the hosting settings. This feature is useful if you change the hosting settings in such way that the UI becomes unreachable; simply wait one minute and the changes will be reverted.

### Host

This tells MIND what IP to bind to. If you specify an IP that is _not_ on the machine running MIND, you _will_ encounter errors.  
Using `0.0.0.0` will have MIND bind to all interfaces it finds on the host machine.

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

This is used for reverse proxy support - the default is empty. If you want to put MIND behind a proxy (so you can access the web-UI via a nice URL), set a URL prefix (it _must_ start with a `/` character).  

To get MIND running on `http://example.com/mind`, you would set your reverse proxy to forward the `/mind` path to the IP and port of your mind instance, and set URL prefix to `/mind`.
