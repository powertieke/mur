# update
if [ -e install/readonly_on ];
then
	mount -o remount,rw /
fi

git pull
cd install
./install.sh