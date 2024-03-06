## Introduction

On this page you can find more information on the type of reminders, how to add them, how to manage them and some implementation details. It is assumed that you already have [set up your notification services](../installation/setup_after_installation.md#add-a-notification-service).

## Types of Reminders

There are two types of reminders: time dependent reminders ('normal reminders') and time independent reminders ('static reminders'). Then there are also 'templates', which you can use to create normal and static reminders faster.

### Normal Reminders

Normal reminders require a time that they need to be triggered on. Once they are triggered, they are deleted (unless they repeat). In the UI, select the tab 'Reminders' and click the '+' button to add a new reminder.

1. You can select a template to build upon. More info on that in the ['Templates' section](#templates).
2. If desired, you can select a colour that the reminder will get in the list. [This image](https://github.com/Casvt/Kapowarr/assets/88994465/f55c895b-7975-4a3e-88a0-f8e2a148bf8a) displays coloured reminders in a library.
3. Next is the title, which should be what you want to be reminded of. This is also shown in the library view.
4. The time and date that is set will be the moment that the reminder will be sent.
5. Click on 'Notification Services' to see the list of services that you've set up. Select at least one for the reminder to use when it's triggered. You can also select multiple. The ['Default Notification Service' setting](../settings/user_settings.md#default-notification-service) decides which service is selected by default.
6. You can change the reminder to be repeated or not. More info on this below.
7. The text field is where you can add extra info. This is _not_ shown in the library view, but _will_ be included in the notification that is sent (if supported, which it most likely is).
8. Clicking the 'Test' button will send the reminder, so that you can check if it works as desired. Then click 'Add' to finalise the creation.

Once it's added, the timer is set! When the set time is reached, the reminder will be sent and will then disappear from your library.

#### Repeated Reminders

By default, normal reminders are 'single-use' and are deleted after they are triggered. However, it's also possible to repeat reminders either by time interval or week days.

For repetition by time interval, select 'Repeated' when creating a reminder and select the time interval (e.g. '5 days' or '1 year'). The first time the reminder will be sent is on the set time. The interval will then be added and the resulting time will be the next time the reminder will be triggered.

!!! info "Implementation detail: repetition on non-yearly days"
	If the reminder is set on a day that does not exist every interval (e.g. leap day each year, or the 31st each month) it will be triggered on the set day the first time, but from then on will trigger on the closest day within the same month and it will stay there. So if you set a reminder for 29-2-2024 (D-M-Y) and set the reminder to repeat each year, the next reminders will be triggered on 28-2-2025, 28-2-2026, 28-2-2027, 28-2-2028, etc. Notice that even in 2028, when there is a 29th day in February, it will still run on the 28th. This is because it ran on the 28th the previous year, so add one year to it and it will run on the 28th again.

Instead of repeating based on a certain time interval, it is also possible to repeat based on the week days. Select 'Week Days' when creating a reminder and select the days of the week that you want the reminder to trigger on. For example, if you select 'Mo' and 'Thu', the reminder will be triggered every Monday and Thursday. The time is based on the time set. The date of the time set decides when the reminder starts repeating.

### Static Reminders

Static reminders work the same way as normal reminders, except is there no time aspect. There is no date, time or repetition. This is because static reminders are only triggered manually. Simply click on the reminder in the library and click the 'Trigger' button to send the reminder.

The use of this is to notify people on command. For example, a notification to your kids that you'll be late. You don't want to send such a thing on a certain time or interval, but instead on command. Or an e-mail to your team notifying them of a emergency meeting. With static reminders, you can set it up once and when needed click one button to notify everyone withing seconds.

### Templates

Templates can be used to make it easier to create (static) reminders by filling in fields when selecting it. In the UI, select the 'Templates' tab and click the '+' button to add a template. Templates can store the colour, title, notification service selection and text (body) of the (static) reminder. When saved, you can start using it in the creation of (static) reminders. Simply select the template from the list and all the fields will be filled automatically. The only fields left are the time fields for normal reminders.
