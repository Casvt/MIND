# Noted Reminders
A simple self hosted reminder platform that uses push to send notifications to your device. Set the reminder and forget about it! 📢

Noted is a simple self hosted application for creating reminders that get pushed to your device using the [Apprise](https://github.com/caronc/apprise) API. You can send messages to just about every platform, including scheduled emails!

![noted-reminders-dashboard](https://user-images.githubusercontent.com/57927413/212753936-8306b0bb-57a7-4912-a675-d92e25cd2220.png)

## Core Features
* Basic auth
* Utilizes Apprise
* Create and delete reminders
* Schedule reminders

## Planned Features
You can see our planned features in our [Project board](https://github.com/users/Casvt/projects/3).

## Installation

```
sudo apt-get install git python3-pip
sudo git clone https://github.com/Casvt/Noted.git /opt/Noted
cd /opt/Noted
python3 -m pip install -r requirements.txt
python3 Noted.py
```
You can see the [wiki](https://github.com/Casvt/Noted/wiki) for instructions on how to install using other OS.
