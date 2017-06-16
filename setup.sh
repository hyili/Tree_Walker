#!/bin/sh


curr_path=`pwd`

echo "--> Current directory: $curr_path"
if [ -f "$curr_path/setup.sh" ]
then
	echo "--> Ok."
else
	echo "--> You must run this script in the root of working directory."
	exit
fi

echo "\n--> Installing python3 packages ..."
pip install --upgrade pip
pip3 install -r $curr_path/requirements

if [ "$?" == 0 ]
then
	echo "--> Ok. Packages installed."
else
	echo "--> Looks like there is something terrible."
	exit
fi

echo "\n--> Generating config file ..."
cp $curr_path/tests/config/.requests.conf.example $curr_path/tests/config/.requests.conf

if [ "$?" == 0 ]
then
	echo "--> Ok. $curr_path/tests/config/.requests.conf generated."
else
	echo "--> Looks like there is something terrible."
	exit
fi

echo "\n--> Create tests/output/ and tests/logs/ ..."
mkdir -p $curr_path/tests/output $curr_path/tests/logs

if [ "$?" == 0 ]
then
	echo "--> Ok. $curr_path/tests/output/ and $curr_path/tests/logs/ generated."
else
	echo "--> Looks like there is something terrible."
	exit
fi


echo "\n"
echo "################################################################################"
echo ""
echo "Please go to http://phantomjs.org/download.html and find suitable binary."
echo ""
echo "After that, specify the binary location in $curr_path/tests/config/.requests.conf"
echo ""
echo "You can now use the tools. Or you may first want to modify the config above."
echo ""
echo "If you want do some test, you can visit the page below or read README.md."
echo ""
echo "Ref. https://github.com/hyili/Tree_Walker"
echo ""
echo "################################################################################"
