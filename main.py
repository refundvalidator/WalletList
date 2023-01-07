import requests
import os
import json
import time

start = time.time()
wallets = []
validators = []


url = f'https://rest.unification.io/cosmos'

params={'pagination.limit' : '1000000000'}

req = requests.session()

res = req.get(f'{url}/auth/v1beta1/accounts').json()
total_wallets = int(res['pagination']['total'])

res = req.get(f'{url}/auth/v1beta1/accounts',params=params).json()


### Gets all addresses ###
for r in res['accounts']:
    if r['@type'] == '/cosmos.auth.v1beta1.BaseAccount':
        wallets.append({'rank': 0, 'address': f"{r['address']}"})
    else:
        wallets.append({'rank': 0, 'address': f"{r['base_account']['address']}"})

### Gets all Validators ###

i = 0
### Gets amounts for each wallet including rewards, unbondings, redelegations, delegations ###
for r in wallets:
    i += 1
    
    # Adds balance
    res = req.get(f'{url}/bank/v1beta1/balances/{r["address"]}').json()
    if res['balances'] == []:
        r['amount'] = 0
    else:
        r['amount'] = float(res['balances'][0]['amount'])

    # Adds rewards
    res = req.get(f'{url}/distribution/v1beta1/delegators/{r["address"]}/rewards').json()
    if res['total'] != []:
        r['amount'] += float(res['total'][0]['amount'])

    # Adds unbondings
    res = req.get(f'{url}/staking/v1beta1/delegators/{r["address"]}/unbonding_delegations').json()
    if res['unbonding_responses'] != []:
        for unb in res['unbonding_responses']:
            r['amount'] += float(unb['entries'][0]['balance'])

    # Adds redelegations
    res = req.get(f'{url}/staking/v1beta1/delegators/{r["address"]}/redelegations').json()
    if res['redelegation_responses'] != []:
        for red in res['redelegation_responses']:
            r['amount'] += float(red['entries'][0]['balance'])

    # Adds delegations
    res = req.get(f'{url}/staking/v1beta1/delegations/{r["address"]}').json()
    if res['delegation_responses']:
        for dele in res['delegation_responses']:
            r['amount'] += float(dele['balance']['amount'])

    ########TO DO: Add commission too


    print(f'{total_wallets-i} Wallets Remaining')


### Sorts by highest amount ###
wallets = sorted(wallets, key=lambda d: d['amount'], reverse=True)

### Adds proper rank to each wallet, and formatted amount in FUND ###
i = 0
for r in wallets:
    i += 1
    r['rank'] = i
    r['amount'] = f"{r['amount']/1000000000:,}"

with open('wallets.json', 'w') as u:
    json.dump(wallets,u,indent=4)

print(f"Completed in {(time.time()-start)/60} minutes")