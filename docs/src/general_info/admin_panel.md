## Introduction

The admin panel allows you to manage your MIND instance. It has multiple features regarding the management of your instance and its users. You can change how users authenticate and create accounts, download the logs, change the hosting settings, add/edit/delete users, export and import the database and restart or shutdown the application.

The settings for authentication, hosting, logging and database backups are all described on the ['Admin Settings' page](../settings/admin_settings.md).

!!! warning "Restrict Access"
	The panel gives you a lot of power, so it's important that nobody can access it but you (by changing the default password).

### Accessing the panel

You can access the admin panel by logging into the admin account. The default username is `admin` and the default password is `admin`. How to change the password (which is strongly recommended) is described in the ['User Management' section](#user-management).

## User Management

The admin panel allows you to manage the users on your instance. You can add new users, change the password of existing users and delete users. The ability to add users will always be there, regardless of the value of the ['Allow New Accounts' setting](../settings/admin_settings.md#allow-new-accounts). If that setting is disabled (disallowing users to create accounts themselves), then the admin panel is the only place where new accounts can be made.

Click the large plus button to start adding an account. Enter a unique username and a password for the account, then click 'Add'. Click on the pen icon next to a user entry to change the username or password of the user. This is useful if the user has forgotten their password. You can also change the password of the admin user this way, which is strongly recommended. Use the bin icon to delete the user. You cannot delete the admin. Edit the admin account to not only change the password, but to also optionally setup MFA. The Apprise URL that you enter will be used to send the MFA code when trying to log into the account. The users can set the MFA code themselves in their account settings.

## Database

The 'Download Database' button allows you to download the complete MIND database. This file contains everything: all user accounts, their settings, notification services and reminders, and admin settings (authentication, hosting, etc.). This file represents a complete back-up of your MIND instance.

The admin panel offers the option to upload a database file to apply. There are multiple scenarios where you'd want to upload a database (import a backup):

1. You can recover all data up to the point of database export in the case that something goes wrong.
2. You can revert back to a stable state when trying something.
3. You're moving to a new computer/instance and want to move all user data too.

Select the database file that you want to import for the 'Database File' input. Enabling the 'Keep Hosting Settings' option will copy the hosting settings from the current database over to the imported database. This will result in the instance being hosted with the same settings as it is now. If you leave this setting disabled, the hosting settings from the imported database will be used. That could result in the web-UI being hosted with different settings, potentially making it unreachable.

The uploaded file could be denied for multiple reasons:

1. It is not an (sqlite) database file. Only import database files that you downloaded with the 'Download Database' button.
2. The database file is too old. If the database is for such an old version of MIND, it could fail to migrate it.
3. The database file is too new. If the database is for a newer version of MIND than the version that you upload it to, it's denied.

After importing the database, MIND will restart with the new database in use. It is required to log into the admin panel within 60 seconds in order to keep the newly imported database file. If you do not, the import will be reverted, MIND will restart again but now with the old database again. This is in order to protect you from breaking MIND if the database file is invalid or if the hosting settings make the UI unreachable (if you have the 'Keep Hosting Settings' option disabled).

The download button next to each database backup entry will download the backup file to your computer. The upload button next to each database backup entry will allow you to import/upload the backup, similar to uploading a database file yourself.

## Apprise Plugins

If you have a custom Apprise [plugin](https://appriseit.com/library/plugin/), then you click the 'Manage Paths' button to open a window where you can add the path to the file that the plugin is defined in. It will then become available to use inside MIND.

## Power

You can use these buttons to restart or shutdown the application.
