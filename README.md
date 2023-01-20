# WalletList
Script to query all the balances of wallets on the Unification Mainchain, and rank them accordingly.

Best if run using a local node with API enabled (see https://github.com/refundvalidator/RapidUND for quick setup of a local node)

Can be run with public Unification provided API endpoints, although this method is significantly slower. To achieve this, change the variable 

`url = f'http://localhost:1317/cosmos'` 

to 

`url = f'https://rest.unification.io/cosmos'`

Amounts are rounded to the nearest 2 decimal places.

wallets.json is automatically updated every 3 minutes on this page, for easy reference.

## Results will include the following results:

### For Every Wallet:

```
-Total Spendable
-Total Delegations
-Total Unbondings
-Total Rewards
-Grand Total
```

### For Every Validator (Including Jailed):
```
-Total Comissions
```
# Script Requirements

`python3`

`pip`

Use `pip install -r requirements.txt` to install remaining pip dependencies.

# Usage

Simply run `python3 main.py` and wait for the script to finish, then the wallets.json file will be automatically updated.
