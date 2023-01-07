import requests
import json

url = f'https://rest.unification.io/cosmos'

params={'pagination.limit' : '1000000000'}

req = requests.session()

res = req.get(f'{url}/auth/v1beta1/accounts').json()
total_wallets = int(res['pagination']['total'])

res = req.get(f'{url}/auth/v1beta1/accounts',params=params).json()

wallets=[{
    "address" : "und1k03uvkkzmtkvfedufaxft75yqdfkfgvgm77zwm"
}
]

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
        print(f"Adding Balace: {float(res['balances'][0]['amount'])}")

    # Adds rewards
    res = req.get(f'{url}/distribution/v1beta1/delegators/{r["address"]}/rewards').json()
    if res['total'] != []:
        print(f"Adding Rewards: Original:{r['amount']} Adding:{float(res['total'][0]['amount'])}")
        r['amount'] += float(res['total'][0]['amount'])
        

    # Adds unbondings
    res = req.get(f'{url}/staking/v1beta1/delegators/{r["address"]}/unbonding_delegations').json()
    print(f"Adding Unbondings: Original:{r['amount']} Adding:{float(res['pagination']['total'])}")
    r['amount'] += float(res['pagination']['total'])

    # Adds redelegations
    res = req.get(f'{url}/staking/v1beta1/delegators/{r["address"]}/redelegations').json()
    r['amount'] += float(res['pagination']['total'])

    # Adds delegations
    res = req.get(f'{url}/staking/v1beta1/delegations/{r["address"]}').json()
    r['amount'] += float(res['pagination']['total'])

    ########TO DO: Add commission too


    print(f'{total_wallets-i} Wallets Remaining')