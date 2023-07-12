import requests
import os
import json
import time
import bech32
from named_wallets import named_wallets

class Wallets:
    def __init__(self,url="http://localhost:1317", debug=False):
        self.url = url
        self.debug = debug
        self.wallets = []
        self.validators = []
        self.data = {}
        self.params={'pagination.limit' : '100000000000000000'}
        self.req = requests.session()

    def start(self):
        while True:
            self.validators = []
            self.wallets = []
            start = time.time()
            res = self.req.get(f'{self.url}/cosmos/auth/v1beta1/accounts').json()
            total_wallets = int(res['pagination']['total'])
            total = {
                'last_updated' : 0,
                'total_wallets': total_wallets,
                'total_spendable' : 0,
                'total_delegations' : 0,
                'total_unbondings' : 0,
                'total_rewards' : 0,
                'total_commission' : 0,
                'total_efund' : 0,
                'total_spent_efund': 0,
                'grand_total' : 0,
                }

            ### Gets all addresses ###
            res = self.req.get(f'{self.url}/cosmos/auth/v1beta1/accounts',params=self.params).json()
            for r in res['accounts']:
                if r['@type'] == '/cosmos.auth.v1beta1.BaseAccount':
                    self.wallets.append({
                        'rank':0,
                        'name': 'Wallet', 
                        'address': f"{r['address']}",
                        'total':0,
                        'spendable':0, 
                        'delegations':0,
                        'unbondings':0,
                        'rewards':0,
                        'commission':0,
                        'efund': 0,
                        'spent_efund':0,
                        })
                else:
                    self.wallets.append({
                        'rank':0, 
                        'name': 'Wallet',
                        'address': f"{r['base_account']['address']}",
                        'total':0,
                        'spendable':0, 
                        'delegations':0,
                        'unbondings':0,
                        'rewards':0,
                        'commission':0,
                        'efund': 0,
                        'spent_efund':0,
                        })

            ### Gets all validators (including inactive) (validators that never had commission are not shown) ###
            res = self.req.get(f'{self.url}/cosmos/staking/v1beta1/validators',params=self.params).json()
            for r in res['validators']:
                # Converts undval address to und address (self-delegation address)
                _, data = bech32.bech32_decode(r['operator_address'])
                address = bech32.bech32_encode("und", data)
                self.validators.append({
                    "rank" : 0,
                    "name" : f"{r['description']['moniker']}\n( Validator )",
                    "val_address": f"{r['operator_address']}",
                    "address": f"{address}",
                    "commission" : 0, 
                })

            ### Adds amounts for each validators commissions (including inactive) ###
            for val in self.validators:
                res = self.req.get(f'{self.url}/cosmos/distribution/v1beta1/validators/{val["val_address"]}/commission', params=self.params).json()
                for com in res['commission']['commission']:
                    amount = float(com['amount'])
                    val['commission'] += amount
                    total['grand_total'] += amount
                    total['total_commission'] += amount

            i = 0
            ### Gets amounts for each wallet including rewards, unbondings, delegations ###
            for wallet in self.wallets:
                i += 1
                
                # Adds spendable balance
                res = self.req.get(f'{self.url}/cosmos/bank/v1beta1/balances/{wallet["address"]}', params=self.params).json()
                for bal in res['balances']:
                    amount = float(bal['amount'])
                    wallet['spendable'] += amount
                    wallet['total'] += amount
                    if wallet['name'] != "Locked eFUND" and wallet['name'] != "All Unjailed Delegations" and wallet['name'] != "Unclaimed Rewards" and wallet['name'] != "Unbonding/Jailed Delegations":
                        total['grand_total'] += amount
                        total['total_spendable'] += amount

                # Adds rewards
                res = self.req.get(f'{self.url}/cosmos/distribution/v1beta1/delegators/{wallet["address"]}/rewards', params=self.params).json()
                for rew in res['total']:
                    amount = float(rew['amount'])
                    wallet['rewards'] += amount
                    wallet['total'] += amount
                    total['grand_total'] += amount
                    total['total_rewards'] += amount

                # Adds unbondings
                res = self.req.get(f'{self.url}/cosmos/staking/v1beta1/delegators/{wallet["address"]}/unbonding_delegations', params=self.params).json()
                for unb in res['unbonding_responses']:
                    for un in unb['entries']:
                        amount = float(un['balance'])
                        wallet['unbondings'] += amount
                        wallet['total'] += amount
                        total['grand_total'] += amount
                        total['total_unbondings'] += amount

                # Adds delegations
                res = self.req.get(f'{self.url}/cosmos/staking/v1beta1/delegations/{wallet["address"]}', params=self.params).json()
                for dele in res['delegation_responses']:
                    amount = float(dele['balance']['amount'])
                    wallet['delegations'] += amount
                    wallet['total'] += amount
                    total['grand_total'] += amount
                    total['total_delegations'] += amount

                # Adds eFUND 
                res = self.req.get(f'{self.url}/mainchain/enterprise/v1/account/{wallet["address"]}', params=self.params).json()
                amount = float(res['account']['locked_efund']['amount'])
                spent_amount = float(res['account']['spent_efund']['amount'])
                wallet['efund'] += amount
                wallet['spent_efund'] += spent_amount
                total['total_efund'] += amount


            ### List of already named wallets, incase a wallet might have multiple names ### 
            named = []

            ### Names the validators wallets in the wallet list and sets comission ###
            for val in self.validators:
                for wallet in self.wallets:
                    if wallet['address'] == val['address']:
                        wallet['name'] = val['name']
                        wallet['commission'] = val['commission']
                        wallet['total'] += val['commission']
                        named.append(wallet['address'])

            ### Names the registered beacons ###
            res = self.req.get(f'{self.url}/mainchain/beacon/v1/beacons', params=self.params).json()
            for bea in res['beacons']:
                for wallet in self.wallets:
                    if wallet['address'] == bea['owner']:
                        if bea['owner'] in named:
                            wallet['name'] += f"\n&&\n{bea['name']}\n( Beacon #{bea['beacon_id']} )"
                        else: 
                            wallet['name'] = f"{bea['name']}\n( Beacon #{bea['beacon_id']} )"
                            named.append(bea['owner'])

            ### Names the wrkchains ###
            res = self.req.get(f'{self.url}/mainchain/wrkchain/v1/wrkchains', params=self.params).json()
            for wrk in res['wrkchains']:
                for wallet in self.wallets:
                    if wallet['address'] == wrk['owner']:
                        if wrk['owner'] in named:
                            wallet['name'] += f"\n&&\n{wrk['name']}\n( WRKChain #{wrk['wrkchain_id']} )"
                        else: 
                            wallet['name'] = f"{wrk['name']}\n( WRKChain #{wrk['wrkchain_id']} )"
                            named.append(wrk['owner'])

            ### Names other known wallets ###
            for wallet in self.wallets:
                for x , y in named_wallets.items():
                    if y == wallet["address"]:
                        if wallet["address"] in named:
                            wallet["name"] += f"\n&&\n{x}"
                        else:
                            wallet["name"] = x
                            named.append(x)

            ### Sorts by highest amount ###
            self.wallets = sorted(self.wallets, key=lambda d: d['total'], reverse=True)


            ### Adds proper rank to each wallet, and formatted amount in FUND ###
            for i, wallet in enumerate(self.wallets):
                wallet['rank'] = i+1
                wallet['total'] = f"{round(wallet['total']/1000000000,2):,}"
                wallet['spendable'] = f"{round(wallet['spendable']/1000000000,2):,}"
                wallet['delegations'] = f"{round(wallet['delegations']/1000000000,2):,}"
                wallet['unbondings'] = f"{round(wallet['unbondings']/1000000000,2):,}"
                wallet['rewards'] = f"{round(wallet['rewards']/1000000000,2):,}"
                wallet['commission'] = f"{round(wallet['commission']/1000000000,2):,}"
                wallet['efund'] = f"{round(wallet['efund']/1000000000,2):,}"
                wallet['spent_efund'] = f"{round(wallet['spent_efund']/1000000000,2):,}"
            
            ### Formatted totals and update time
            t = time.localtime()
            total['last_updated'] = f'{time.strftime("%H:%M", t)} {time.tzname[0]}'
            total['grand_total'] = f"{round(total['grand_total']/1000000000,2):,}"
            total['total_spendable'] = f"{round(total['total_spendable']/1000000000,2):,}"
            total['total_delegations'] = f"{round(total['total_delegations']/1000000000,2):,}"
            total['total_unbondings'] = f"{round(total['total_unbondings']/1000000000,2):,}"
            total['total_rewards'] = f"{round(total['total_rewards']/1000000000,2):,}"
            total['total_commission'] = f"{round(total['total_commission']/1000000000,2):,}"
            total['total_efund'] = f"{round(total['total_efund']/1000000000,2):,}"
            total['total_spent_efund'] = f"{round(total['total_spent_efund']/1000000000,2):,}"

            self.data = {
                "total" : total,
                "wallets" : self.wallets,
            }
            print(f"{[time.strftime('%H:%M:%S', t)]} Wallets updated in {round((time.time()-start),2)} seconds")
            if self.debug:
                print(json.dumps(self.data,indent=4))

if __name__ == "__main__":
    Wallets().start()
