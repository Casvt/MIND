# Reporting

This page covers how to get in contact, which platform to use and how to properly share information like logs and errors.

## Choosing a Platform

If you have a question, visit the [Discord server](https://discord.gg/nMNdgG7vsE).  
If you experience behaviour that you are unsure of if it's correct, check the ['General Information' page](../general_info/workings.md).  
If you are sure that something is going wrong (bug) or is missing (feature), create a [GitHub issue](https://github.com/Casvt/MIND/issues).

## Reporting a Bug

If you experience behaviour that is not correct, you should make a 'bug report':

1. Enable [debug logging](../settings/admin_settings.md#logging-level) in the settings.
2. Reproduce the error (this way it will occur with debug logs enabled).
3. Collect all the relevant logs. You can download the debug logs from the last debug session by clicking the 'Download Debug Logs' button in the admin panel. Preferably starting from when you started reproducing, but _AT LEAST_ the complete error (A.K.A. traceback).
4. On the [GitHub issues page](https://github.com/Casvt/MIND/issues), make a new issue and choose the 'Bug report' template. Fill in each field in the template with the information requested.
5. Make sure to properly format code and errors! Otherwise it's not readable. See the tip below.
