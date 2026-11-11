#!/bin/bash 

pg_dump \
  --host=$DB_HOST \
  --port=$DB_PORT \
  --username=$DB_USER \
  --format=custom \
  --no-owner \
  --no-acl \
  --file=local_database.dump \
  $DB_NAME
