## delete db
rm db.sqlite3
## delete migrations files
find . -name migrations -exec rm -r {} ;
### makemigrate 
#./manage.py makemigrations profile taxonomy product cart shop orders immoshop autocar customs invoices project profile
./manage.py makemigrations profile taxonomy product shop customer invoice  project profile
## migrate 
#./manage.py migrate
##
#./manage.py createsuperuser
