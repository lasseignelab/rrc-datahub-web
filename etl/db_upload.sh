#!/bin/bash

pg_restore \
  --verbose \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  --dbname="$RENDER_DATABASE_URL" \
  local_database.dump
