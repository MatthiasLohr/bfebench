# BFEBench - Blockchain-based Fair Exchange Benchmark Tool

## Usage

  * Download and install `bfebench` (e.g., by cloning the git repository and executing `pip install -e .`).
    We suggest using a virtual environment for that.
  * Select a Ethereum compatible blockchain platform to run `bfebench` on.
    We provide a couple of test networks in the [blockchain-networks](./blockchain-networks) directory,
    which are preconfigured and can be started using [docker-compose](https://docs.docker.com/compose/).
  * Create an [environments configuration file](./docs/environments_configuration.md) for the blockchain environment
    you selected.
    For the test networks in [blockchain-networks](./blockchain-networks), we provide a ready-to-use
    environments configuration file (named `bfebench-environments.yaml`).
  * Select a protocol for benchmarking.
    You can list all available protocols by executing `bfebench list-protocols`.
  * Select the strategies to be simulated for seller and buyer.
    You can list all available strategies for the selected protocol by executing `bfebench list-strategies <protocol>`.
  * Start the simulation by executing
    ```
    bfebench run <protocol> <seller strategy> <buyer strategy> <file to be exchanged> -e <environments configuration>
    ```

For a list of all supported commands and options run `bfebench -h`.


## Project Goals

The following features are planned to be supported:

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


## Evaluation

* Exp1: Runtime Performance
  * Only faithful exchange
  * Compare all protocol impls (4 variants) with different data sizes
  * Output: 
    * Protocol Comparision -- Chart: x=size, y=time (containing all 4 protocol impls)
      * Matrix: 
       - Protocol: [Public,Public-SC,Permissioned,Permissioned-SC] 
       - Data size: [1KB,2KB,3KB,...]
    * Effect of Chain -- 4 Charts (1 per protocol impl): x=percentage of execution time (CPU-seller/chain/CPU-buyer)
* Exp2: Costs
  * a) Protocol Comparision 
    * only for Faithful
    * Costs in relation to exchanged asset size
      * Matrix: 
       - Protocol: [Public,Public-SC,Permissioned,Permissioned-SC] 
       - Data size: [1KB,2KB,3KB,...]
  * b) Cheating variant cost comparison: Max damage for faithful party
    * Fixed data size (log influence of size on cost in case of cheating)
    * b1) What is a baseline of max damage for faithful party? (not a key contrib of paper)
      * Matrix: 
       - Protocol: [Public,Permissioned] 
       - Data size: [1KB,2KB,3KB,...]
       - Strategy: [SellerFaithful/BuyerMaxDamage,SellerMaxDamage/BuyerFaithful]
    * b2) How does the cost with state channel behave in case of cheating and how des it relate to the baseline (b1)?
      * Matrix: 
       - Protocol: [Public-SC,Permissioned-SC] 
       - Data size: [1KB,2KB,3KB,...]
       - Strategy: [Cheating1,Cheating2,Cheating3,...]
      
