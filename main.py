import pandas as pd
import numpy as np

# Step 1: Load raw transaction CSV data
dataframe1 = pd.read_csv('src/all_wallets_raw_eth_transactions.csv')

# Step 2: Define protocol action categories
DEPOSIT_FUNCS = {'deposit', 'mint', 'supply', 'depositunderlying'}
BORROW_FUNCS = {'borrow'}
REPAY_FUNCS = {'repay', 'repayborrow'}
REDEEM_FUNCS = {'redeem', 'redeemunderlying', 'withdraw'}
LIQUIDATION_FUNCS = {'liquidationcall', 'liquidate'}

def get_action(function_name):
    fn = str(function_name).lower() if pd.notnull(function_name) else ''
    if fn in DEPOSIT_FUNCS:
        return 'deposit'
    elif fn in BORROW_FUNCS:
        return 'borrow'
    elif fn in REPAY_FUNCS:
        return 'repay'
    elif fn in REDEEM_FUNCS:
        return 'redeem'
    elif fn in LIQUIDATION_FUNCS:
        return 'liquidation'
    else:
        return 'other'

# Step 3: Generate action and convert value to ETH
dataframe1['action'] = dataframe1['functionName'].apply(get_action)
dataframe1['value_eth'] = dataframe1['value'].astype(float) / 1e18
dataframe1['timestamp_dt'] = pd.to_datetime(dataframe1['timeStamp'], unit='s')

# Step 4: Aggregate features wallet-wise
features = {}

for wallet, group in dataframe1.groupby('wallet_id'):
    feature = {}
    feature['deposit_count'] = (group['action'] == 'deposit').sum()
    feature['borrow_count'] = (group['action'] == 'borrow').sum()
    feature['repay_count'] = (group['action'] == 'repay').sum()
    feature['redeem_count'] = (group['action'] == 'redeem').sum()
    feature['liquidation_count'] = (group['action'] == 'liquidation').sum()
    
    feature['total_deposit_eth'] = group.loc[group['action'] == 'deposit', 'value_eth'].sum()
    feature['total_borrow_eth'] = group.loc[group['action'] == 'borrow', 'value_eth'].sum()
    feature['total_repay_eth'] = group.loc[group['action'] == 'repay', 'value_eth'].sum()
    feature['total_redeem_eth'] = group.loc[group['action'] == 'redeem', 'value_eth'].sum()
    
    feature['failed_tx_count'] = (group['isError'] == 1).sum()
    feature['total_transactions'] = len(group)
    
    timestamps = group['timestamp_dt'].sort_values().values
    if len(timestamps) > 1:
        diffs = np.diff(timestamps).astype('timedelta64[s]').astype(int)
        feature['avg_time_gap'] = diffs.mean()
        feature['min_time_gap'] = diffs.min()
        feature['burst_count'] = (diffs < 120).sum()
    else:
        feature['avg_time_gap'] = 0
        feature['min_time_gap'] = 0
        feature['burst_count'] = 0

    last_ts = group['timestamp_dt'].max()
    feature['last_active_days_ago'] = (pd.Timestamp.now(tz=last_ts.tz) - last_ts).days

    features[wallet] = feature

feat_dataframe1 = pd.DataFrame.from_dict(features, orient='index').reset_index().rename(columns={'index':'wallet_id'})

# Step 5: Rule-based labeling
def label_risk(row):
    if row['liquidation_count'] > 0:
        return 1
    if row['borrow_count'] > 0:
        repay_ratio = row['total_repay_eth'] / max(row['total_borrow_eth'], 1e-8)
        if repay_ratio < 0.4:
            return 1
    if row['failed_tx_count'] > 5:
        return 1
    if row['burst_count'] > 20:
        return 1
    if row['total_transactions'] < 5:
        return 0
    return 0

feat_dataframe1['is_risky'] = feat_dataframe1.apply(label_risk, axis=1)

# Step 6: Risk scoring with bigger weights and offset minimum 200 score
positive_weights = {
    'borrow_count': 40,
    'liquidation_count': 50,
    'failed_tx_count': 30,
    'burst_count': 20,
}

negative_weights = {
    'total_transactions': -20,
    'repay_count': -30,
}

def normalize(series):
    max_val = series.max()
    if max_val == 0:
        return series
    return series / max_val

def calculate_risk_score(df):
    score = np.zeros(len(df))
    for feat, weight in positive_weights.items():
        if feat in df.columns:
            norm_vals = normalize(df[feat])
            score += norm_vals * weight
    for feat, weight in negative_weights.items():
        if feat in df.columns:
            norm_vals = normalize(df[feat])
            score += norm_vals * weight
    min_score = score.min()
    max_score = score.max()
    if max_score - min_score == 0:
        norm_score = np.zeros_like(score)
    else:
        norm_score = (score - min_score) / (max_score - min_score)
    
    # Scale between 200 and 1000 to give min scores higher base
    score_scaled = norm_score * 800  # 0-800 scale
    score_scaled = score_scaled + 200  # shift by 200
    risk_score_0_1000 = np.clip(score_scaled, 200, 1000).astype(int)
    return risk_score_0_1000

feat_dataframe1['risk_score'] = calculate_risk_score(feat_dataframe1)

# Step 7: Print scores
for _, row in feat_dataframe1.iterrows():
    print(f"{row['wallet_id']}: {row['risk_score']}")

# Step 8: Save final scores CSV
feat_dataframe1.to_csv('full_features_with_risk_score.csv', index=False)
print("\nFinal scored dataframe saved to 'full_features_with_risk_score.csv'.")

