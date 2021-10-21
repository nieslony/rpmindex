#!/bin/bash

PKG_NAME=$( rpmspec --parse rpmindex.spec | awk '/^Name:/ { print $2; }' )
PKG_VERSION=$( rpmspec --parse rpmindex.spec | awk '/^Version:/ { print $2; }' )
PY_FOLDERS=$(
    find -not -name setup.py -name "*py" -exec dirname {} \; |
    sort -u |
    sed -e 's#\./##' -e 's#/#.#' |
    awk '{ print "\"" $1 "\","; }' |
    tr -d "\n"
    )

echo $PY_FOLDERS

rpmspec --parse rpmindex.spec | awk -v packages="$PY_FOLDERS" '
    BEGIN {
        print "from distutils.core import setup";
        print "setup("
    }

    /^Name:/    { print "    name=\"" $2 "\","; }
    /^Version:/ { print "    version=\"" $2 "\","; }

    END {
        print "    packages=[" packages "]"
        print ")"
    }
' > setup.py

tar --exclude={*~,site,*gz,make_tar.sh,.git*,__pycache__,$0} \
    --transform=s/^./$PKG_NAME-$PKG_VERSION/ \
    -cvzf $PKG_NAME-$PKG_VERSION.tar.gz \
    --owner=0 --group=0 \
    .

