paste2box
=========

paste2box is the file sharing client whose purpose is to ease process of file sharing.

### Features

* GUI client
* Command line client
* Capture screenshot (save/copy to clipboard/share)
* Share clipboard contents
* Hotkey configuration for screenshot and clipboard functions
* Multiple file sharing service support
* Logging in with your account
* GPLv3 license

### Supported file sharing services

* gist
* owncloud / nextcloud
* googledrive
* imgur.com

### Supported operating systems

* Windows (XP - W10)
* Linux (X11)

### Built with

* Python 3.5+
* PyQt4 + Qt 4.8

### Command line client examples

Add a new login:

    p2b gdrive --login someone@gmail.com

List existing logins:

    p2b gdrive --list-logins

Log out:

    p2b gdrive --logout someone@gmail.com

Share a file:

    p2b gdrive --login someone@gmail.com /path/to/file.jpg

Create gist with custom file name:

    p2b gist --login someone@gmail.com --filename fakename.cpp /path/to/file.txt

Upload image and open deletion it in default browser:

    xdg-open $(p2b imgur --output-only delete /path/to/image.png)

More information is available through commands:

    p2b --help
    p2b {owncloud,imgur,gist,gdrive} --help

![Screenshot](https://raw.githubusercontent.com/rokups/paste2box/master/screenshot.png)
