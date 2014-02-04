nodectrl
========

## Description
There's a huge stack of network devices, and after installing the last switch, you forgot where's the first one, then NodeCTRL could help you.

This application based on Flask + SQLAlchemy wrote to help you catalog your network hardware in your net.

Also you can check if device is alive or not.

And this is not a full list of features this application provides.

![Screenshot](/img/nodectrl.png)

## Installation
This is quick and easy in Ubuntu:

    sudo apt-get -y install git python-flask python-sqlalchemy nmap libsnmp-python python-ipaddr
    git clone https://github.com/Sets88/nodectrl.git
    cd nodectrl
    python web.py

This is a good idea to run so for overview or test, but if you are going to use it on real server you'll better to use uwsgi + Nginx or mod_wsgi + Apache


## Configuration
For configurating use internal settings manager: "Switch -> Settings", where preferably add the first user, set key(it's better to generate it, this key used to hash users passwords)

You can use sqlite instead of mysql.

You'll have to add categories you'll probably need.

You also can add additional links, which apears on right top corner.


After adding a user, don't forget to change user permissions, change "settings_edit" permission, which allows users to access to settings, it is allowed for everybody by default, just set there administrator's login, or even several separated by comma, for example:

    vasya, root, admin

This will allow users: vasya, root and admin to access settings menu (of course if they are already exists)


Warning, when you'll start creating hierarchy, dont forget to start name of swich "(v)" (without quotes) for ones which can answer by SNMP, for example this title pretty nice: (v) Lenin 90 (DES-1228)

This were done to let application know whom to ask by SNMP, about, on which port there is the required MAC address, also it uses in "auto move nodes" feature, and when you find by MAC address.

Not sure this feature will work on non D-Link devices.

## Additional features

### "Warning" flag

Sometimes you have to know that your device turned off (we use external software to check automatically if device is alive every 5 minutes), then, you have to make your external software to visit special url link, and warning flag would be set.

That's how you do it:

1. Open Switch -> Settings
2. Find field "Generate hash..." type in the external machine's IP, which have to set flags
3. Push generate
4. Now you got token, copy it to buffer

Now URL you'll need will be like this:

	http://nashnodectrl:port/api/setflag/{IP}/{Status}/{TOKEN}/

For exapmple:

	http://192.168.1.1:5000/api/setflag/10.90.90.176/1/8a3c2b1d5d8d2bbb5e190e0e9bc39ce01f981eaa/

Will set flag to first found device with IP 10.90.90.176, then you'll see "!" sign on this node

### Where's that MAC

I need to find out, on which switch located host with current MAC address

URL will be like this:

	http://nashnodectrl:port/api/getnodebymac/{MAC}/{TOKEN}/

For example:

	http://192.168.1.1:5000/api/getnodebymac/00:e0:4c:11:5a:2c/8a3c2b1d5d8d2bbb5e190e0e9bc39ce01f981eaa/

Will return the name of node on which current MAC located
