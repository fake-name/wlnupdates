#!/bin/bash

set -e

# if [ "$(id -u)" != "0" ]; then
#    echo "This script must be run as root. Please enter your password for sudo." 1>&2
#    sudo -H env PATH=$PATH INTERNAL_SUDO=TRUE "$0" "$@"
#    exit 0;
# else
#   if [ $INTERNAL_SUDO != "TRUE" ]; then
#     echo "Please allow the script to 'sudo' internally, it has to be done a specific"
#     echo "way to properly preserve some environment variables."
#     exit 1
#   fi
# fi

echo "Fetching db dump from remote server";
ssh client@ks3 'sudo -u postgres pg_dump --clean --format c -d wlndb' | pv -cN Db-Fetch-Progress > /media/Storage/Scripts/dbBak/wln_db_dump_$(date +%Y-%m-%d).sqlb
echo "Updating local database from dump file";
cat /media/Storage/Scripts/dbBak/wln_db_dump_$(date +%Y-%m-%d).sqlb  | pv -c | ssh wlnuser@10.1.1.61 -t "pg_restore --clean --format c -d wlndb"
echo "Synchronizing cover folder!"
rsync -rvvP client@ks3:/web/wlnupdates/covers /media/Extra/_web_resource_backend/
echo "Done!"

# Run the server
#source flask/bin/activate
#python run.py all


#sudo -H -u herp -- bash -c "ssh client@ks1 'tar -c /media/Storage/wlnupdates/covers | xz' | pv -cN Cover-Fetch-Progress > .$

