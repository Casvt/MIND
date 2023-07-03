# Backup your data

It's possible, and very easy, to backup all MIND data. This way, you can recover data if something goes wrong, port your instance over to an other computer or run redundant instances.

## Backing up the data

It's as simple as making a copy of the database file and storing it somewhere safe.

1. Stop MIND, if it's still running.
2. Go inside the docker volume of the container (most likely `mind-db`) or the mapped folder.
3. Inside the volume/folder, you'll find the `MIND.db` file. Make a copy of this. That's all you need.
4. You can now start the instance back up.

The database file contains all data and is the only thing needed to keep a complete backup of your MIND instance.

## Recovering the data

It's as simple as putting the database file in the database folder and restarting the instance.

1. Stop MIND, if it's still running.
2. Go inside the docker volume of the container (most likely `mind-db`) or the mapped folder.
3. Inside the volume/folder, place the database file that you backed up.
4. You can now start the instance back up. Everything should be recovered.
