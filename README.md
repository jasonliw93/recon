team03-Project
==============

REsearch Citations in On-line Networks (RECON)
---------------------------------------------
The Report file in git relevant to Phase 4 is in the root and is called Phase4.pdf.

The challenge is to create a application for the researcher Alehanjro that he can use to analyse data about foreign (specifically Israeli) news sources.  He wants to see which Twitter Posts(TP) and English News Sources(ENS) are linking to Israeli-English News Sources (INS) and how that link is made.  We will use these terms as examples for what the application will do but the application should also work for any kind of website/news source.  

Our project will be built on the *Django* framework using *Scrapy* to scrape webpages for data.

Installation
-------------
Install Python 2.7 - https://www.python.org/downloads/<br>

	$ sudo apt-get install libffi-dev libxml2-dev libxslt1-dev libssl-dev python-dev
	
Ensure that the above libraries are installed.  If not running on matlab make sure to do this command.<br>  If on matlab please proceed without running the above command.
	
	$ cd recon_site
	$ PATH="$HOME/.local/bin:$PATH"
	$ make build

NOTE : Installation takes a long time.

Testing
--------

	$ make test
Starting
--------

	$ make start
	$ make open
	
Login : admin<br>
Password : admin<br>

Stopping
--------
	
	$ make stop

Build and Run
-------------
	
	$ make
	$ make open


Prerequisites 
-------------

Python 2.7 <br>
Django 1.7 <br>
Scrapy 0.24 <br>
Tweepy 2.4 (https://github.com/svven/tweepy.git#egg=tweepy) <br>
Pywb 0.6.3<br>
Warcprox 1.3<br>
Uwsgi 2.0.6<br>
Django-Celery 3.1.16<br>
Django user-accounts 1.0 <br>
Django - Jsonfield 0.9.13 <br>
Django Eztables 0.3.2 <br>
Kombu 3.0.23<br>
Pinax Theme Bootstrap 5.5.1<br>

Packages
--------
libffi-dev <br>
libxml2-dev <br>
libxslt1-dev <br>
libssl-dev <br>
python-dev <br>

Dear User: Are you confused? No idea where to start in our awesome website? Find answers to all your life questions at RECON_User_Manual.pdf, saved under the root directory.
