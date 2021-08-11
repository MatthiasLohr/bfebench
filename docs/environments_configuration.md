# Environments Configuration

An environments configuration file contains the configuration for the endpoints and accounts being used for running the
exchange protocol.

Full environments file example:
```yaml
## Operator environment configuration.
## The operator account is used for preparations, e.g., deploying reusable contracts, funding seller and buyer, etc.
operator:
  endpoint:
    ## URL to the HTTP RPC interface
    url: https://rpc.slock.it/goerli
  
  ## Operator's Ethereum wallet
  wallet:
    ## Operator's wallet address
    ## Create a new address and private key with ./tools/generate-eth-wallet.py.
    address: 0x7A8B7d50a76cE34e518A0830802dBFE6ADb6ef9c
    
    ## Operator's private key.
    ## Can be omitted if account is known and unlocked on the endpoint.
    # privateKey: 0x0000000000000000000000000000000000000000000000000000000000000000

## Seller environment configuration.
## The seller is in hold of a file which he is going to transfer to the buyer during the exchange.
seller:
  endpoint:
    ## URL to the HTTP RPC interface
    url: https://rpc.slock.it/goerli
      
  ## Seller's Ethereum wallet
  wallet:
    ## Sellers's wallet address
    ## Create a new address and private key with ./tools/generate-eth-wallet.py.
    address: 0xbd8Ae831f910968e5755F4C3Da726E9472772D4D
    
    ## Sellers's private key.
    ## Can be omitted if account is known and unlocked on the endpoint.
    # privateKey: 0x0000000000000000000000000000000000000000000000000000000000000000

## Buyer environment configuration.
## The buyer wants to receive a file from the seller and is willing to pay tokens for that.
buyer:
  endpoint:
    ## URL to the HTTP RPC interface
    url: https://rpc.slock.it/goerli
      
  ## Buyer's Ethereum wallet
  wallet:
    ## Buyer's wallet address
    ## Create a new address and private key with ./tools/generate-eth-wallet.py.
    address: 0x7BBD65b9Cd93b6caef6d973CFb7c7B041488b5d7
    
    ## Buyer's private key.
    ## Can be omitted if account is known and unlocked on the endpoint.
    # privateKey: 0x0000000000000000000000000000000000000000000000000000000000000000
```
