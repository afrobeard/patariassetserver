# patariassetserver

Patari Asset Server is a free & open-source django app that provides the ability to store image derivatives and has some level of support for storing remote backups.
Even though its covered in licenses see COPYING, this software comes with no warranties. Use at your own risk.

Bugs and feature requests are tracked on GitHub's Issue Tracker.

Built with Django!

##Setting up

requires python3

use pip to install dependencies:  
	- `cd` into `patariassetserver`  
	- `pip install -r requirements.txt`

update patariassetserver/settings.py with your own configurations for the keys:  
	- `DATABASES`  
	- `ORIGINAL_BASE_PATH`  
	- `DERIVATIVE_BASE_PATH`  
    - `AZURE_UPLOAD_PATH`  

start up the server:  
- `cd` into `patariassetserver`  
- `python manage.py runserver`  