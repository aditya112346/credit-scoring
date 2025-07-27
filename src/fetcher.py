import requests
import pandas as pd
import time

# This is the API_KEY generated from the `etherscan.io/apidashboard`
ETHERSCAN_API_KEY = "AGZFN2HQVPTKHG82R667VUP2X93PJDUK92"  

# Compound V2 Comet addresses (ETH mainnet) this is used for compound protocol in ethereum blockchain 
COMPOUND_V2_CONTRACTS = [
    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"  
]

# Load wallet list from CSV
wallets_df = pd.read_csv('Wallet_id_Sheet1.csv')
wallet_list = wallets_df['wallet_id'].str.strip().str.lower().tolist()

def fetch_eth_transactions(wallet):
    # Returns list of txns for wallet from Etherscan API
    url = (
        f"https://api.etherscan.io/api"
        f"?module=account"
        f"&action=txlist"
        f"&address={wallet}"
        f"&startblock=0"
        f"&endblock=99999999"
        f"&sort=asc"
        f"&apikey={ETHERSCAN_API_KEY}"
    )
    res = requests.get(url)
    data = res.json()
    if data['status'] == '1':
        return data['result']  # each is a tx dict
    else:
        return []

all_wallets_txs = []
for i, wallet in enumerate(wallet_list):
    print(f"Fetching txns for {wallet} ({i+1}/{len(wallet_list)})")
    txns = fetch_eth_transactions(wallet)
    for tx in txns:
        tx['wallet_id'] = wallet
    all_wallets_txs.extend(txns)
    time.sleep(0.22)

print(f"Total raw transactions fetched: {len(all_wallets_txs)}")

pd.DataFrame(all_wallets_txs).to_csv("all_wallets_raw_eth_transactions.csv", index=False)
print("Saved all_wallets_raw_eth_transactions.csv")

