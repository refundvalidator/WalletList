# WalletList
Script to query all the balances of wallets on the Unification Mainchain, and rank them accordingly.

Best if run using a local node with API enabled (see https://github.com/refundvalidator/RapidUND for quick setup of a local node)

Amounts are rounded 

### If you would like your wallet to be named in the list please add it to the `named_wallets.py` file and sumbit a pull request, or message me directly

## Results will include the following results:

### For Every Wallet:

```
-Total Spendable
-Total Delegations
-Total Unbondings
-Total Rewards
-Total Comission
-Total eFUND Locked
-Total eFUND Spent
-Grand Total
```

# Script Requirements

`python3`

`pip`

Use `pip install -r requirements.txt` to install remaining dependencies.

# Usage

Simply run `python3 main.py` and wait for the script to finish, then the wallets.json file will be updated.
