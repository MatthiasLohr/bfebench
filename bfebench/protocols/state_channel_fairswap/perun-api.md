# Perun API Documentation

  * https://perun.network/ -- official website
  * https://labs.hyperledger.org/perun-doc/ -- documentation at Hyperledger labs
  * https://github.com/hyperledger-labs/go-perun -- Go API source code
  * https://github.com/hyperledger-labs/perun-eth-contracts -- Solidity Contracts for Ethereum
  * https://github.com/hyperledger-labs/perun-node -- Perun Node project


## Contracts

### Adjudicator

Full contract:
[Adjucator.sol](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol)

  * [register](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L74-L87):
    Register disputes the state of a ledger channel and its sub-channels.
  * [progress](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L170-L211):
    Progress is used to advance the state of an app on-chain.
    If the call was successful, a Progressed event is emitted.
  * [conclude](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L222-L234):
    concludes the channel identified by params including its sub-channels and sets the accumulated outcome at the assetholders.
    The channel must be a ledger channel and not have been concluded yet.
    Sub-channels are force-concluded if the parent channel is concluded.
  * [concludeFinal](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L236-L268):
    immediately concludes the channel identified by `params` if the provided state is valid and final.
    The caller must provide signatures from all participants.
    Since any fully-signed final state supersedes any ongoing dispute, concludeFinal may skip any registered dispute.
    The function emits events Concluded and FinalConcluded.
  * [channelID](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L270-L277):
    Calculates the channel's ID from the given parameters.
  * [hashState](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L279-L286):
    Calculates the hash of a state.


### AssetHolder

Full contract:
[AssetHolder.sol](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/AssetHolder.sol),
[AssetHolderETH.sol](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/AssetHolderETH.sol)

  * [deposit](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/AssetHolder.sol#L120-L138):
    Function that is used to fund a channel.
  * [withdraw](https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/AssetHolder.sol#L140-L165):
    Sends money from authorization.participant to authorization.receiver.
