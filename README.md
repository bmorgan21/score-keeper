# score-keeper

# Helpful Links
* [Boostrap 5.3 Documentation](https://getbootstrap.com/docs/5.3)
* [Quart](https://quart.palletsprojects.com/en/latest/)
* [Tortoise ORM](https://tortoise.github.io/)
* [Websocket PubSub](https://github.com/NandaGopal56/websockets-pubsub)
* [Python, Redis & FastAPI](https://medium.com/@nandagopal05/scaling-websockets-with-pub-sub-using-python-redis-fastapi-b16392ffe291__)

# Setup Raspberry Pi

Install Raspberry Pi [OS Lite](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit)

    Flash SD Card with Image
    Add empty ssh to bootfs
    Add `userconf.txt to bootfs with username:encrypted-password
      $ echo "mypassword" | openssl passwd -6 -stdin

Start up Raspberry Pi

    $ ssh username@ip-address

Passwordless Login

    $(local) ssh-keygen -t rsa
    $(raspberry pi) mkdir ~/.ssh
    $(raspberry pi) chmod 7000 ~/.ssh
    insert contents of ~/.ssh/id_rsa.pub (local) into ~/.ssh/authorized_keys (raspberry pi)
    
Install Docker and Add Permissions

    $ curl -sSL https://get.docker.com | sh
    $ sudo gpasswd -a $USER docker
    $ sudo shutdown -r now
    
# Configuring the Server

Download code

    $ mkdir code && cd code
    $ git clone https://github.com/bmorgan21/score-keeper.git

Reboot Nightly

    $ sudo crontab -e
    15 6 * * * reboot

Start the full app

    $ docker compose --profile full up -d

Create Deployment Crontab

    $ crontab -e
    */5 * * * * cd code/score-keeper && bash deploy.sh full 2> /home/admin/error.txt`

# Getting Started


Before any of the commands will work, you MUST run `init` in each terminal.  After you run it, you will see that the terminal prompt is now prefixed with `(venv)`.  This is a visual confirmation that things are setup correctly.

Upgrade the DB schema

    aerich upgrade

Start the server

    quart start

# Resetting the DB

To initialize the configuration files for Tortoise ORM you must run the following command.  This command only needs to be run if the migrations directory is removed in order to start over again.

    aerich init -t score_keeper.settings.TORTOISE_ORM

In order to create an initial migration file, you can run the following command.  You should now see a file ending in `init.py` in `migrations/models` directory.

    aerich init-db

At this point the database will be created and the schema will be applied.  You can connect to the DB with the following command:

    psql -h ${DB_HOST} -U ${DB_USER} ${DB_NAME}

The password can be found in the `.devcontainer/docker-compose.yml` file.  One at the postgres prompt you can run `\dt` to see all the tables and then run `\d user` to see the user schema.

You can type `exit` or press `ctrl-d` to exit the postgres prompt.

When you are ready to extend your application and make changes to your models, you will need to also update the database schema.  This is managed through the same DB tool.  To create a new migration, you will run the following command with `XXX` replaced with a meaningful description (it is best to keep it short and to not have spaces):

    aerich migrate --name "XXX"

This will create a new file in the migration/models directory.  At this point no changes have been made to the database.  In order to apply those changes you must run the following command:

    aerich upgrade

----

In order to run pylint in the context of the venv, you must use this command:

    python $(which pylint) score_keeper
