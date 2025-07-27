import pandas as pd

df = pd.read_csv('all_wallets_raw_eth_transactions.csv')

COMPOUND_V2_CONTRACTS = {
    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",  # Comptroller (V2)
    "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643",  # cDAI
    "0x39aa39c021dfbae8fac545936693ac917d5e7563",  # cUSDC
    "0xf650c3d88cc8619c7c8e2ed2c82aac8afd33c4fc",  # cUSDT
    "0x6c8c6b02e7b2be14d4fa6022dfd6da6eccab7b5b",  # cBAT
    "0x158079ee67fce2f58472a96584a73c7ab9ac95c1",  # cREP
    "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5",  # cETH
    "0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407",  # cWBTC
    "0x4b0181102a0112a2ef11abf8b0f5c5b4b2518e17",  # cZRX
    "0x35a18000230da775cac24873d00ff85bccded550",  # cUNI
    "0x95b4ef2869e02fb6f7942e93618f8e1f81e96c36",  # cCOMP
    "0x3fffb3458b94c82cb8a3e080064d946751b3c1c8",  # cMKR
    # Compound V3 LendingPool (Ethereum mainnet, adds V3 coverage)
    "0x794a61358d6845594f94dc1db02a252b5b4814ad",
}

# Normalize addresses to lowercase
COMPOUND_V2_CONTRACTS = set(addr.lower() for addr in COMPOUND_V2_CONTRACTS)

# Ensure 'to' and 'contractAddress' columns are lowercase strings (some rows may be empty/NaN)
df['to'] = df['to'].fillna('').astype(str).str.lower()
if 'contractAddress' in df.columns:
    df['contractAddress'] = df['contractAddress'].fillna('').astype(str).str.lower()
else:
    df['contractAddress'] = ''

compound_txs = df[
    (df['to'].isin(COMPOUND_V2_CONTRACTS)) | 
    (df['contractAddress'].isin(COMPOUND_V2_CONTRACTS))
].copy()

print(f"Total Compound V2/V3 related transactions found: {len(compound_txs)}")

compound_txs.to_csv('compound_v2_v3_transactions.csv', index=False)
print("Filtered Compound transactions saved to 'compound_v2_v3_transactions.csv'")
