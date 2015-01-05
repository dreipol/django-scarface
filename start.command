#! /bin/sh
clear
echo "Launching..."
cd "`dirname "$0"`"
ls -a

export LANG="de_CH.UTF-8"
export LC_COLLATE="de_CH.UTF-8"
export LC_CTYPE="de_CH.UTF-8"
export LC_MESSAGES="de_CH.UTF-8"
export LC_MONETARY="de_CH.UTF-8"
export LC_NUMERIC="de_CH.UTF-8"
export LC_TIME="de_CH.UTF-8"
export LC_ALL=


echo "Checking Computer for all necessary tools...please make sure you have installed Xcode and the Command Line Utilities."
echo "Looking for brew..."
hash brew 2>/dev/null || { ruby -e "$(curl -fsSkL raw.github.com/mxcl/homebrew/go)";}
echo "Looking for python..."
hash python 2>/dev/null || { brew install python; }
echo "Looking for pip..."
hash pip 2>/dev/null || { sudo easy_install pip; }
echo "Looking for virtualenv..."
hash virtualenv 2>/dev/null || { sudo easy_install virtualenv; }
echo "Looking for virtualenvwrapper..."
hash mkvirtualenv 2>/dev/null || { sudo easy_install virtualenvwrapper; }



export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/Documents/Repositories

source virtualenvwrapper.sh
	
echo "First run - would you like to setup the environment? (y/n)"
read -n 1 name;

if [ "$name" == "y" ]; then
	echo "Setting up a virtual environment for the current application..."
	rmvirtualenv venv-django_scarface
	mkvirtualenv venv-django_scarface
fi
workon venv-django_scarface

echo "Upgrading requirements..."
for line in $(cat requirements.txt)
do
	pip install $line;
done


echo "Migrating database..."
if [ "$name" == "y" ]; then
	echo "running fake migrations"
	python manage.py syncdb --all --settings=django_scarface.settings.moku
    python manage.py migrate --fake --settings=django_scarface.settings.moku

fi

python manage.py syncdb --settings=django_scarface.settings.moku
python manage.py migrate --settings=django_scarface.settings.moku

echo "Launching server..."
python manage.py runserver 0.0.0.0:8000 --settings=django_scarface.settings.moku
