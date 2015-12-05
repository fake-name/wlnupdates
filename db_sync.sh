

ssh client@ks1 'sudo -u postgres pg_dump --clean -d wlndb | xz' > db_dump_$(date +%Y-%m-%d).sql.xz
