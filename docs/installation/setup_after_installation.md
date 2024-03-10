After installing MIND, you should have access to the web-ui. MIND needs some configuration in order for it to work properly.

## Hosting

There are a few hosting settings which you might want to change, before you continue.

### Port

The first thing to do is decide if you want to leave MIND on the default port of `8080`. If you want to _keep_ the port, you can go to the next step. If you want to _change_ the port, see the ['Port' setting](../settings/admin_settings.md#port).

### Base URL

If you want to set a base url (e.g. for a reverse proxy), see the ['URL Prefix' setting](../settings/admin_settings.md#url-prefix).

## Admin panel and settings

It's handy to check out the admin panel and it's features. Most importantly, you should change the default password of the admin account.

### Claiming the admin account

MIND has an admin panel which allows you to manage the users, change hosting and authentication settings and more. To enter the admin panel, login using the username `admin` and password `admin`. Once inside, it's **_strongly_** advised to change the password of the admin account. Instructions on how to do that, can be found on the ['Admin Panel' settings page](../settings/admin_settings.md#user-management).

### Disabling user registration

If you are planning on exposing your MIND instance to the internet, it might be smart to disable user registration. This disables the ability for anyone to create a new account. Only the admin will be able to create new user accounts, via the admin panel. See the ['Allow New Accounts' setting](../settings/admin_settings.md#allow-new-accounts).

## User

Now we can create and use a normal user account and start making reminders!

### Creating an account

When accessing the web-ui, you'll be prompted to log in. Click on `Or create an account`, enter the desired username and password for the account and click `Create` (if user registration is disabled, ask the admin to make an account for you). The account is created and can now be logged in with. The complete authentication process is local and no data is shared with any other service.

### Set your locale

In the user settings, you can change your locale, so that the dates and times are displayed in the format used by your country. 

### Add a notification service

A notification service is a way of sending a notification. For example an e-mail to a group of people or a PushBullet notification to a specific device. What the actual content of the notification is, is decided by the title and text of the reminder. The notification service only specifies in which way the title and text is sent. You set it up once, and then you can select it when creating a reminder.

Go to the "Notification Services" tab in the web-ui and click the `+` button. Choose a platform, enter the required information and give the service a name. From then on, you can select the notification service when creating/editing a reminder.
