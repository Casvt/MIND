# API
Below is the API documentation. Report an issue on [GitHub](https://github.com/Casvt/MIND/issues).

All endpoints have the `/api` prefix. That means, for example, that `/auth/login` can be reached at `/api/auth/login`.

## Authentication

Authentication is done using an API key.
To log in, make a POST request to the [`/api/auth/login`](#authlogin) endpoint.
You'll receive an API key, which you can then use in your requests to authenticate.
Supply it via the url parameter `api_key`.
This API key is valid for one hour (though the admin can change this duration) after which the key expires, any further requests return 401 'APIKeyExpired' and you are required to log in again.
If no `api_key` is supplied or it is invalid, 401 `APIKeyInvalid` is returned.

For example:
```bash
curl -sSL 'http://192.168.2.15:8080/api/reminders?api_key=ABCDEFG'
```

## Supplying data

Often, data needs to be supplied with a request.
If the parameters need to be supplied via `url`, add them to the url as url parameters.
If the parameters need to be supplied via `body`, add them to the body as a json object and supply the `Content-Type: application/json` header.

For example:
```bash
# URL parameter
curl -sSL 'http://192.168.2.15:8080/api/reminders/search?api_key=ABCDEFG&query=Fountain&sort_by=time_reversed'

# Body parameter
curl -sSLX POST \
	-H 'Content-Type: application/json' \
	-d '{"title": "Test service", "url": "test://fake/url"}' \
	'http://192.168.2.15:8080/api/notificationservices?api_key=ABCDEFG'
```

## Endpoints
The following is automatically generated. Please report any issues on [GitHub](https://github.com/Casvt/MIND/issues).
### `/auth/login`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| No | Login to a user account | 

??? POST

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| username | Yes | string | The username of the user account | N/A |
	| password | Yes | string | The password of the user account | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 401 | AccessUnauthorized | The password given is not correct |
	| 404 | UserNotFound | The user requested can not be found |

### `/auth/logout`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Logout of a user account | 

??? POST

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |

### `/auth/status`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Get current status of login | 

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

### `/user/add`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| No | Create a new user account | 

??? POST

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| username | Yes | string | The username of the user account | N/A |
	| password | Yes | string | The password of the user account | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 400 | UsernameInvalid | The username contains invalid characters |
	| 400 | UsernameTaken | The username is already taken |
	| 403 | NewAccountsNotAllowed | It's not allowed to create a new account except for the admin |

### `/user`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage a user account | 

??? PUT

	Change the password of the user account

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| new_password | Yes | string | The new password of the user account | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

??? DELETE

	Delete the user account

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

### `/notificationservices`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage the notification services | 

??? GET

	Get a list of all notification services

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

??? POST

	Add a notification service

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | Yes | string | The title of the entry | N/A |
	| url | Yes | string | The Apprise URL of the notification service | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

### `/notificationservices/available`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Get all available notification services and their url layout | 

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

### `/notificationservices/test`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Send a test notification using the supplied Apprise URL | 

??? POST

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| url | Yes | string | The Apprise URL of the notification service | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

### `/notificationservices/<int:n_id>`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage a specific notification service | 

Replace `<int:n_id>` with the ID of the entry. For example: `/notificationservices/2`.

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | NotificationServiceNotFound | The notification service was not found |

??? PUT

	Edit the notification service

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | No | string | The title of the entry | N/A |
	| url | No | string | The Apprise URL of the notification service | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 404 | NotificationServiceNotFound | The notification service was not found |

??? DELETE

	Delete the notification service

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| delete_reminders_using | No | bool | Instead of throwing an error when there are still reminders using the service, delete the reminders. | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 404 | NotificationServiceNotFound | The notification service was not found |

### `/reminders`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage the reminders | 

??? GET

	Get a list of all reminders

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| sort_by | No | string | How to sort the result | `time`, `time_reversed`, `title`, `title_reversed`, `date_added`, `date_added_reversed` |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |

??? POST

	Add a reminder

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | Yes | string | The title of the entry | N/A |
	| time | Yes | number,decimal number | The UTC epoch timestamp that the reminder should be sent at | N/A |
	| notification_services | Yes | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |
	| repeat_quantity | No | string | The quantity of the repeat_interval | `years`, `months`, `weeks`, `days`, `hours`, `minutes` |
	| repeat_interval | No | number | The number of the interval | N/A |
	| weekdays | No | list of numbers | On which days of the weeks to run the reminder | `0`, `1`, `2`, `3`, `4`, `5`, `6` |
	| color | No | string | The hex code of the color of the entry, which is shown in the web-ui | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | InvalidTime | The time given is in the past |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 404 | NotificationServiceNotFound | The notification service was not found |

### `/reminders/search`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Search through the list of reminders | 

??? GET

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| sort_by | No | string | How to sort the result | `time`, `time_reversed`, `title`, `title_reversed`, `date_added`, `date_added_reversed` |
	| query | Yes | string | The search term | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

### `/reminders/test`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Test send a reminder draft | 

??? POST

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | Yes | string | The title of the entry | N/A |
	| notification_services | Yes | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 404 | NotificationServiceNotFound | The notification service was not found |

### `/reminders/<int:r_id>`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage a specific reminder | 

Replace `<int:r_id>` with the ID of the entry. For example: `/reminders/2`.

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

??? PUT

	Edit the reminder

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | No | string | The title of the entry | N/A |
	| time | No | number,decimal number | The UTC epoch timestamp that the reminder should be sent at | N/A |
	| notification_services | No | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |
	| repeat_quantity | No | string | The quantity of the repeat_interval | `years`, `months`, `weeks`, `days`, `hours`, `minutes` |
	| repeat_interval | No | number | The number of the interval | N/A |
	| weekdays | No | list of numbers | On which days of the weeks to run the reminder | `0`, `1`, `2`, `3`, `4`, `5`, `6` |
	| color | No | string | The hex code of the color of the entry, which is shown in the web-ui | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | InvalidTime | The time given is in the past |
	| 404 | NotificationServiceNotFound | The notification service was not found |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

??? DELETE

	Delete the reminder

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

### `/templates`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage the templates | 

??? GET

	Get a list of all templates

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| sort_by | No | string | How to sort the result | `title`, `title_reversed`, `date_added`, `date_added_reversed` |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |

??? POST

	Add a template

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | Yes | string | The title of the entry | N/A |
	| notification_services | Yes | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |
	| color | No | string | The hex code of the color of the entry, which is shown in the web-ui | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 404 | NotificationServiceNotFound | The notification service was not found |

### `/templates/search`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Search through the list of templates | 

??? GET

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| sort_by | No | string | How to sort the result | `title`, `title_reversed`, `date_added`, `date_added_reversed` |
	| query | Yes | string | The search term | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

### `/templates/<int:t_id>`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage a specific template | 

Replace `<int:t_id>` with the ID of the entry. For example: `/templates/2`.

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | TemplateNotFound | The template was not found |

??? PUT

	Edit the template

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | No | string | The title of the entry | N/A |
	| notification_services | No | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |
	| color | No | string | The hex code of the color of the entry, which is shown in the web-ui | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 404 | NotificationServiceNotFound | The notification service was not found |
	| 404 | TemplateNotFound | The template was not found |

??? DELETE

	Delete the template

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | TemplateNotFound | The template was not found |

### `/staticreminders`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage the static reminders | 

??? GET

	Get a list of all static reminders

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| sort_by | No | string | How to sort the result | `title`, `title_reversed`, `date_added`, `date_added_reversed` |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |

??? POST

	Add a static reminder

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | Yes | string | The title of the entry | N/A |
	| notification_services | Yes | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |
	| color | No | string | The hex code of the color of the entry, which is shown in the web-ui | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 404 | NotificationServiceNotFound | The notification service was not found |

### `/staticreminders/search`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Search through the list of staticreminders | 

??? GET

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| sort_by | No | string | How to sort the result | `title`, `title_reversed`, `date_added`, `date_added_reversed` |
	| query | Yes | string | The search term | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

### `/staticreminders/<int:s_id>`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage a specific static reminder | 

Replace `<int:s_id>` with the ID of the entry. For example: `/staticreminders/2`.

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

??? POST

	Trigger the static reminder

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

??? PUT

	Edit the static reminder

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| title | No | string | The title of the entry | N/A |
	| notification_services | No | list of numbers | Array of the id's of the notification services to use to send the notification | N/A |
	| text | No | string | The body of the entry | N/A |
	| color | No | string | The hex code of the color of the entry, which is shown in the web-ui | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 404 | NotificationServiceNotFound | The notification service was not found |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

??? DELETE

	Delete the static reminder

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 404 | ReminderNotFound | The reminder with the id can not be found |

### `/admin/shutdown`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Shut down the application | 

??? POST

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |

### `/admin/restart`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Restart the application | 

??? POST

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |

### `/settings`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| No | Get the admin settings | 

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

### `/admin/settings`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Interact with the admin settings | 

??? GET

	Get the admin settings

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

??? PUT

	Edit the admin settings. Supplying a hosting setting will automatically restart MIND.

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| allow_new_accounts | No | bool | Whether or not to allow users to register a new account. The admin can always add a new account. | N/A |
	| login_time | No | number | How long a user stays logged in, in seconds. Between 1 min and 1 month (60 <= sec <= 2592000) | N/A |
	| login_time_reset | No | bool | If the Login Time timer should reset with each API request. | N/A |
	| host | No | string | The IP to bind to. Use 0.0.0.0 to bind to all addresses. | N/A |
	| port | No | number | The port to listen on. | N/A |
	| url_prefix | No | string | The base url to run on. Useful for reverse proxies. Empty string to disable. | N/A |
	| log_level | No | number | The level to log on. | `20`, `10` |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | InvalidKeyValue | The value of a key is invalid |

### `/admin/logs`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Get the debug logs | 

??? GET

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

### `/admin/users`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Get all users or add one | 

??? GET

	Get all users

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

??? POST

	Add a new user

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| username | Yes | string | The username of the user account | N/A |
	| password | Yes | string | The password of the user account | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |
	| 400 | UsernameInvalid | The username contains invalid characters |
	| 400 | UsernameTaken | The username is already taken |
	| 403 | NewAccountsNotAllowed | It's not allowed to create a new account except for the admin |

### `/admin/users/<int:u_id>`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Manage a specific user | 

Replace `<int:u_id>` with the ID of the entry. For example: `/admin/users/2`.

??? PUT

	Change the password of the user account

	**Parameters (body)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| new_password | Yes | string | The new password of the user account | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |

??? DELETE

	Delete the user account

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

### `/admin/database`

| Requires being logged in | Description |
| ------------------------ | ----------- |
| Yes | Download the database | 

??? GET

	Download the database file

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 200 | N/A | Success |

??? POST

	Upload and apply a database file. Will automatically restart MIND.

	**Parameters (url)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| copy_hosting_settings | Yes | bool | Copy the hosting settings from the current database | N/A |

	**Parameters (file)**

	| Name | Required | Data type | Description | Allowed values |
	| ---- | -------- | --------- | ----------- | -------------- |
	| file | Yes | N/A | The MIND database file | N/A |

	**Returns**
	
	| Code | Error | Description |
	| ---- | ----- | ----------- |
	| 201 | N/A | Success |
	| 400 | InvalidDatabaseFile | The uploaded database file is invalid or not supported |
	| 400 | InvalidKeyValue | The value of a key is invalid |
	| 400 | KeyNotFound | A key was not found in the input that is required to be given |