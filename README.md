# BFEBench - Blockchain-based Fair Exchange Benchmark Tool

## Project Goals

The following features are planned to be supported:

  * Environments
    * [ ] Ethereum -- public Ethereum networks (e.g. Mainnet, Ropsten, Goerli)
    * [ ] [Quorum](https://consensys.net/quorum/) -- permissioned Ethereum network
    * [ ] [Py-EVM](https://github.com/ethereum/py-evm) -- for testing purposes
  * Protocol Implementations
    * [ ] FairSwap
    * [ ] FairSwap with State Channels
    * [ ] OptiSwap (optional)
    * [ ] SmartJudge FairSwap (optional)
  * Seller/Buyer Strategies
    * [ ] Successful Exchange, Max Benefit (faithful execution)
    * [ ] Max Benefit
    * [ ] Max Damage
  * Aspect Analysis
    * [ ] Overall performance (exchanges/second)
    * [ ] Blockchain performance (tx/s, limiting factor?)
    * [ ] CPU performance of parties
    * [ ] cost (tx fees, CPU/RAM required)
    * [ ] Cost Fairness
