import requests
import os
import json
import time
from named import named_wallets

start = time.time()
wallets = []
validators = []

# url = f'http://localhost:1317/cosmos'
url = f'https://rest.unification.io/cosmos'

jsonpath = os.environ.get('JSON_PATH')

if jsonpath is None:
    jsonpath = "./wallets.json"
elif jsonpath[-1] == "/":
    jsonpath = f"{jsonpath}/wallets.json"


params={'pagination.limit' : '10000000000000'}
req = requests.session()
res = req.get(f'{url}/auth/v1beta1/accounts').json()
total_wallets = int(res['pagination']['total'])
total = {
    'last_updated' : 0,
    'total_wallets': total_wallets,
    'total_spendable' : 0,
    'total_delegations' : 0,
    'total_unbondings' : 0,
    'total_rewards' : 0,
    'total_commission' : 0,
    'grand_total' : 0,
    }

### Gets all addresses ###
res = req.get(f'{url}/auth/v1beta1/accounts',params=params).json()
for r in res['accounts']:
    if r['@type'] == '/cosmos.auth.v1beta1.BaseAccount':
        wallets.append({
            'rank':0,
            'name': 'Wallet', 
            'address': f"{r['address']}",
            'total':0,
            'spendable':0, 
            'delegations':0,
            'unbondings':0,
            'rewards':0,
            'commission':0,
            })
    else:
        wallets.append({
            'rank':0, 
            'name': 'Wallet',
            'address': f"{r['base_account']['address']}",
            'total':0,
            'spendable':0, 
            'delegations':0,
            'unbondings':0,
            'rewards':0,
            'commission':0,
            })

### Gets all validators (including inactive) (validators that never had commission are not shown) ###
res = req.get(f'{url}/staking/v1beta1/validators',params=params).json()
for r in res['validators']:
    validators.append({
        "rank" : 0,
        "name" : f"{r['description']['moniker']}",
        "address": f"{r['operator_address']}",
        "commission" : 0, 
    })

### Adds amounts for each validators commissions (including inactive) ###
for val in validators:
    res = req.get(f'{url}/distribution/v1beta1/validators/{val["address"]}/commission').json()
    for com in res['commission']['commission']:
        amount = float(com['amount'])
        val['commission'] += amount
        total['grand_total'] += amount
        total['total_commission'] += amount


i = 0
### Gets amounts for each wallet including rewards, unbondings, delegations ###
for wallet in wallets:
    i += 1

    # Names known wallets
    for x , y in named_wallets.items():
        if y == wallet["address"]:
            wallet["name"] = x

    # Adds spendable balance
    res = req.get(f'{url}/bank/v1beta1/balances/{wallet["address"]}').json()
    for bal in res['balances']:
        amount = float(bal['amount'])
        wallet['spendable'] += amount
        wallet['total'] += amount
        if wallet['name'] != "Locked eFUND" and wallet['name'] != "All Unjailed Delegations" and wallet['name'] != "Unclaimed Rewards" and wallet['name'] != "Unbonding/Jailed Delegations":
            total['grand_total'] += amount
            total['total_spendable'] += amount

    # Adds rewards
    res = req.get(f'{url}/distribution/v1beta1/delegators/{wallet["address"]}/rewards').json()
    for rew in res['total']:
        amount = float(rew['amount'])
        wallet['rewards'] += amount
        wallet['total'] += amount
        total['grand_total'] += amount
        total['total_rewards'] += amount

    # Adds unbondings
    res = req.get(f'{url}/staking/v1beta1/delegators/{wallet["address"]}/unbonding_delegations').json()
    for unb in res['unbonding_responses']:
        for un in unb['entries']:
            amount = float(un['balance'])
            wallet['unbondings'] += amount
            wallet['total'] += amount
            total['grand_total'] += amount
            total['total_unbondings'] += amount

    # Adds delegations
    res = req.get(f'{url}/staking/v1beta1/delegations/{wallet["address"]}').json()
    for dele in res['delegation_responses']:
        amount = float(dele['balance']['amount'])
        wallet['delegations'] += amount
        wallet['total'] += amount
        total['grand_total'] += amount
        total['total_delegations'] += amount
            
    print(f'{total_wallets-i} Wallets Remaining')


### Sorts by highest amount ###
wallets = sorted(wallets, key=lambda d: d['total'], reverse=True)
validators = sorted(validators, key=lambda d: d['commission'], reverse=True)

for val in validators:
    for wallet in wallets:
        if wallet['name'] == val['name']:
            wallet['commission'] = val['commission']
            wallet['total'] += val['commission']

### Adds proper rank to each wallet, and formatted amount in FUND ###
i = 0
for wallet in wallets:
    i += 1
    wallet['rank'] = i
    wallet['total'] = f"{round(wallet['total']/1000000000,2):,}"
    wallet['spendable'] = f"{round(wallet['spendable']/1000000000,2):,}"
    wallet['delegations'] = f"{round(wallet['delegations']/1000000000,2):,}"
    wallet['unbondings'] = f"{round(wallet['unbondings']/1000000000,2):,}"
    wallet['rewards'] = f"{round(wallet['rewards']/1000000000,2):,}"
    wallet['commission'] = f"{round(wallet['commission']/1000000000,2):,}"
    
i = 0
for val in validators:
    i += 1
    val['rank'] = i
    val['commission'] = f"{round(val['commission']/1000000000,2):,}"


t = time.localtime()
total['last_updated'] = f'{time.strftime("%H:%M", t)} CST'
total['grand_total'] = f"{round(total['grand_total']/1000000000,2):,}"
total['total_spendable'] = f"{round(total['total_spendable']/1000000000,2):,}"
total['total_delegations'] = f"{round(total['total_delegations']/1000000000,2):,}"
total['total_unbondings'] = f"{round(total['total_unbondings']/1000000000,2):,}"
total['total_rewards'] = f"{round(total['total_rewards']/1000000000,2):,}"
total['total_commission'] = f"{round(total['total_commission']/1000000000,2):,}"

info = {
    "total" : total,
    "wallets" : wallets,
    "validators" : validators,   
}

with open(jsonpath, 'w',encoding='utf8') as u:
    json.dump(info,u,indent=4,ensure_ascii=False)
    
if (time.time()-start)/60 > 1:
    print(f"Completed in {round((time.time()-start)/60,2)} minutes")
else:
    print(f"Completed in {round((time.time()-start),2)} seconds")
