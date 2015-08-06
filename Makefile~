default: clean build start

clean:	stop
	find . -name '*.pyc' -exec rm {} \;
	rm celeryev.pid celerybeat.pid dump.rdb ; \
	if [ -d redis ] ; \
	then \
	     cd redis/src && make clean; \
	fi;
	if [ -d logs ] ; \
	then \
	     rm -r logs; \
	fi;
build:
	export $PATH="$HOME/.local/bin:$PATH";
	python get-pip.py --user
	pip install -r requirements.txt --user
	mkdir logs
	mkdir logs/crawler
	mkdir logs/twitter
	if [ ! -d redis ] ; \
	then \
		tar xzf redis.tar.gz; \
	fi;
	cd redis/src && make
test: 
	python manage.py test
start:
	./redis/src/redis-server &
	python manage.py celerybeat &
	python manage.py celerycam &
	python manage.py celery worker -l INFO -E &
	cd warc && python pywb-webrecorder.py &
	
open:
	xdg-open http://127.0.0.1:8000

stop:
	@foo=`ps xau | sed -e 1d | grep -v grep | \
	grep 'celery' | awk '{print $$2}'` ; \
	if test -n "$${foo}" ; then \
	for pid in $${foo} ; do \
	kill $${pid} ; \
	done ; \
	fi
	@foo=`ps xau | sed -e 1d | grep -v grep | \
	grep 'uwsgi' | awk '{print $$2}'` ; \
	if test -n "$${foo}" ; then \
	for pid in $${foo} ; do \
	kill $${pid} ; \
	done ; \
	fi
	@foo=`ps xau | sed -e 1d | grep -v grep | \
	grep 'warcprox' | awk '{print $$2}'` ; \
	if test -n "$${foo}" ; then \
	for pid in $${foo} ; do \
	kill $${pid} ; \
	done ; \
	fi
	@foo=`ps xau | sed -e 1d | grep -v grep | \
	grep 'pywb-webrecorder.py' | awk '{print $$2}'` ; \
	if test -n "$${foo}" ; then \
	for pid in $${foo} ; do \
	kill $${pid} ; \
	done ; \
	fi
	@foo=`ps xau | sed -e 1d | grep -v grep | \
	grep 'runserver' | awk '{print $$2}'` ; \
	if test -n "$${foo}" ; then \
	for pid in $${foo} ; do \
	kill $${pid} ; \
	done ; \
	fi
	@foo=`ps xau | sed -e 1d | grep -v grep | \
	grep 'redis' | awk '{print $$2}'` ; \
	if test -n "$${foo}" ; then \
	for pid in $${foo} ; do \
	kill -9 $${pid} ; \
	done ; \
	fi
	
	echo SERVER STOPPED

	
