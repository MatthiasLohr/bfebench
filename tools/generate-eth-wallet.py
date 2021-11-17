#!/usr/bin/env python

from web3 import Account

account = Account.create()
print("Address:     %s" % account.address)
print("Private Key: %s" % account.privateKey.hex())
