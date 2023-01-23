import requests
import os
import json
import time

start = time.time()
wallets = []
validators = []

named_wallets={
    "Cold Wallet" : "und1fxnqz9evaug5m4xuh68s62qg9f5xe2vzsj44l8",
    "All Unjailed Delegations" : "und1fl48vsnmsdzcv85q5d2q4z5ajdha8yu3j7wxl3",
    "Unbonding/Jailed Delegations" : "und1tygms3xhhs3yv487phx3dw4a95jn7t7lx7jhf9",
    "Unclaimed Rewards" : "	und1dacj9whw3gxpa0exrknet5x2u07wvpkevnn5hd",
    "Burned" : "und1qqqqqqqqqqqqqqqqqqqqqqqqqqqqph4djz5txt",
    "reFUND" : "und1k03uvkkzmtkvfedufaxft75yqdfkfgvgm77zwm",
    "Bitforex [CEX]" : "und18mcmhkq6fmhu9hpy3sx5cugqwv6z0wrz7nn5d7",
    "Poloniex [CEX]" : "und186slma7kkxlghwc3hzjr9gkqwhefhln5pw5k26",
    "Probit [CEX]" : "und1jkhkllr3ws3uxclawn4kpuuglffg327wvfg8r9",
    "wFUND" : "und12k2pyuylm9t7ugdvz67h9pg4gmmvhn5vcrzmhj",
    "Digifinex [CEX]" : "und1xnrruk9qlgnmh8qxcz9ypfezj45qk96v2rgnzk",
    "Locked eFUND" : "und1nwt6chnk0efe8ngwa5y63egmdumht6arlvluh3",
}

url = f'http://localhost:1317/cosmos'
#url = f'https://rest.unification.io/cosmos'

params={'pagination.limit' : '1000000000'}
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
            })

### Gets all validators ###
res = req.get(f'{url}/staking/v1beta1/validators',params=params).json()
for r in res['validators']:
    validators.append({
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
    

for val in validators:
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

with open('wallets.json', 'w') as u:
    json.dump(info,u,indent=4)
    
if (time.time()-start)/60 > 1:
    print(f"Completed in {round((time.time()-start)/60,2)} minutes")
else:
    print(f"Completed in {round((time.time()-start),2)} seconds")
