#!/bin/bash

source db.inc

cat data/extra/contropedia_2014-02-13.sql | mysql -u $MYSQLUSER -p$MYSQLPASS $MYSQLDB

