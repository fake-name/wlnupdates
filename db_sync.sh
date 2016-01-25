#!/bin/bash

set -e

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root. Please enter your password for sudo." 1>&2
   sudo -H env PATH=$PATH "$0" "$@"
#else
#   echo "Please allow the script to 'sudo' internally, it has to be done a specific"
#   echo "way to properly preserve some environment variables."
#   exit 1
fi


sudo -H -u herp -- bash -c "ssh client@ks1 'sudo -u postgres pg_dump --clean -d wlndb | xz' | pv -cN Db-Fetch-Progress > db_dump_$(date +%Y-%m-%d).sql.xz"
sudo -H -u postgres -- env PATH=$PATH  bash -c "xz -d db_dump_$(date +%Y-%m-%d).sql.xz -c | pv -c | psql -d wlndb"
