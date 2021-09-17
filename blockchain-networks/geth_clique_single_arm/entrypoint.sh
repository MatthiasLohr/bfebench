#!/bin/sh

if [ ! -d "$GETH_DATADIR/geth" ] ; then
  echo "Initializing geth data..."
  geth init --datadir "$GETH_DATADIR" "$GETH_GENESIS"
  echo "Initialization finished."
fi

echo "$GETH_ACCOUNT_PASSWORD" > /etc/geth/node1.key.password
geth --datadir "$GETH_DATADIR" --networkid 1981 $@

