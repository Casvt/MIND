## Repeating Reminders at an Interval

It is possible to create a repeated reminder that triggers on a day that doesn't always exist. For example, a reminder that runs on leap day, every year. Or a reminder that runs on the 31st of the month, every month. The targeted days don't always exist when the reminder runs. MIND will run the reminder on a day that _does_ exist, and comes before the targeted day. So for example, with the leap year example, that'd mean the reminder would run on the following days (D-M-Y format):

- 29-2-2024
- 28-2-2025
- 28-2-2026
- 28-2-2027
- 29-2-2028

## Detecting Timezone Changes

MIND has handling for when the timezone of the computer that it runs on changes. It could for example be that the timezone switches between daylight savings time and standard time or that the computer is moved to another country where the timezone is different. If MIND detects this, the reminders are appropriately altered so that they still trigger at the same time. That means that if the reminder originally ran at 3 o'clock in the afternoon, then after the timezone switch the reminder will still run at 3 o'clock in the afternoon even though this is technically a different point in the absolute timeline.

It can take up to a day before MIND detects that the timezone has changed. On Windows it might require a restart of MIND before the change is detected.
