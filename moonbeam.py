from gql.transport.requests import RequestsHTTPTransport
from streamlit_autorefresh import st_autorefresh
from gql import gql, Client
from enum import IntEnum
import streamlit as st
import pandas as pd

#####
# Network Configs
#####
# https://chainlist.org/

class Network(IntEnum):
    Arbitrum = 42161
    Aurora = 1313161554
    Avalanche = 43114
    Boba = 288
    BSC = 56
    EOS = 59
    Fantom = 250
    Görli = 5
    Harmony = 1666600000
    Heco = 128
    Kovan = 42
    Mainnet = 1
    Metis = 1088
    Moonbeam = 1284
    Moonriver = 1285
    Rinkeby = 4
    Okex = 66
    Optimism = 10
    Polygon = 137
    xDai = 100

CHAIN_NETWORK_MAP = {
    'arbitrum':Network.Arbitrum,
    'aurora':Network.Aurora,
    'avax':Network.Avalanche,
    'boba':Network.Boba,
    'bsc':Network.BSC,
    'eth':Network.Mainnet,
    'eos':Network.EOS,
    'ftm':Network.Fantom,
    'heco':Network.Heco,
    'harmony':Network.Harmony,
    'matic':Network.Polygon,
    'metis':Network.Metis,
    'moonbeam':Network.Moonbeam,
    'moonriver':Network.Moonriver,
    'okex':Network.Okex,
    'optimism':Network.Optimism,
    'xdai':Network.xDai,
}

EXPLORER_APIS = {
    Network.Arbitrum: 'https://arbiscan.com/tx/',
    Network.Aurora: 'https://explorer.mainnet.aurora.dev/tx/',
    Network.Avalanche: 'https://snowtrace.io/tx/',
    Network.BSC: 'https://bscscan.com/tx/',
    Network.Boba: 'https://blockexplorer.boba.network/tx/',
    Network.Fantom: 'https://ftmscan.com/tx/',
    Network.Harmony: 'https://explorer.harmony.one/tx/',
    Network.Heco: 'https://hecoinfo.com/tx/',
    Network.Mainnet: 'https://etherscan.io/tx/',
    Network.Metis: 'https://andromeda-explorer.metis.io/tx/',
    Network.Moonbeam: 'https://moonbeam.moonscan.io/tx/',
    Network.Moonriver: 'https://moonbeam.moonscan.io/tx/',
    Network.Optimism:'https://optimistic.etherscan.io/tx/',
    Network.Polygon: 'https://polygonscan.com/tx/',
}

CHAIN_NETWORK_MAP = {v:k for k,v in CHAIN_NETWORK_MAP.items()}

#  python3.10 -m streamlit run moonbeam.py


# Refresh every 30 seconds
REFRESH_INTERVAL_SEC = 30

#####################
##### Streamlit #####
#####################

st.set_page_config(layout="wide")
ticker = st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="ticker")
st.title("Moonbeam + Synapse Bridge Analytics")

data_loading = st.text(f"[Every {REFRESH_INTERVAL_SEC} seconds] Loading data...")



SYNAPSE_BRIDGE_URL = 'https://syn-explorer-api.metagabbar.xyz'
client = Client(transport=RequestsHTTPTransport(url=SYNAPSE_BRIDGE_URL,verify=True,retries=5))

def get_confirmed_bridge_txs():
    query_text = '''
    query {
      bridgeTransactions(chainId:1284){
        fromInfo{
          chainId
          time
          txnHash
          formattedValue
          tokenSymbol
          tokenAddress
          txnHash
          address
        }
        toInfo{
          chainId
          time
          txnHash
          formattedValue
          tokenSymbol
          tokenAddress
          txnHash
          address
        }
      }
    }'''
    query = gql(query_text)
    response = client.execute(query)
    df = pd.json_normalize(response['bridgeTransactions'])
    df = df.rename(columns={'fromInfo.chainId':'From Chain','fromInfo.time':'From Time','fromInfo.formattedValue':'From Token Amount','fromInfo.tokenSymbol':'From Token Symbol','fromInfo.tokenAddress':'From Token Address','fromInfo.txnHash':'From Txn Hash','fromInfo.address':'From Address','toInfo.chainId':'To Chain','toInfo.time':'To Time','toInfo.formattedValue':'To Token Amount','toInfo.tokenSymbol':'To Token Symbol','toInfo.tokenAddress':'To Token Address','toInfo.txnHash':'To Txn Hash','toInfo.address':'To Address'})
    df['Txn Status'] = ['Success'] * len(df)
    return df

def make_latest_query(page_number):
    query_text = '''
        query {
            latestBridgeTransactions(page:''' + str(page_number) + '''){
            swapSuccess
            fromInfo{
              chainId
              time
              txnHash
              formattedValue
              tokenSymbol
              tokenAddress
              txnHash
              address
            }
            toInfo{
              chainId
              time
              txnHash
              formattedValue
              tokenSymbol
              tokenAddress
              txnHash
              address
            }
          }
        }'''
    query = gql(query_text)
    response = client.execute(query)
    return response

def get_pending_tx_list(num_pages=5):
    result_list = []
    for i in range(1,num_pages):
        result_list.extend(make_latest_query(i)['latestBridgeTransactions'])
    return result_list

def get_pending_tx_df(num_pages=5):
    result_list = get_pending_tx_list(num_pages)
    df = pd.json_normalize(result_list)
    df = df.rename(columns={'fromInfo.chainId':'From Chain','fromInfo.time':'From Time','fromInfo.formattedValue':'From Token Amount','fromInfo.tokenSymbol':'From Token Symbol','fromInfo.tokenAddress':'From Token Address','fromInfo.txnHash':'From Txn Hash','fromInfo.address':'From Address','toInfo.chainId':'To Chain','toInfo.time':'To Time','toInfo.formattedValue':'To Token Amount','toInfo.tokenSymbol':'To Token Symbol','toInfo.tokenAddress':'To Token Address','toInfo.txnHash':'To Txn Hash','toInfo.address':'To Address'})
    df = df[(df['From Chain']==1284)|(df['To Chain']==1284)]
    df['Txn Status'] = ['Success' if x else 'Pending' for x in df['swapSuccess']]
    del df['swapSuccess']
    return df

def make_clickable(link):
    # target _blank to open new window
    # extract clickable text to display for your link
    text = link.split('=')[0]
    return f'<a target="_blank" href="{link}">{text}</a>'

def format_links(df):
    for i,row in df.iterrows():
        from_chain_id = row['From Chain']
        to_chain_id = row['To Chain']
        from_url = EXPLORER_APIS[from_chain_id] + row['From Txn Hash'] if row['From Txn Hash'] else row['From Txn Hash']
        to_url = EXPLORER_APIS[to_chain_id] + row['To Txn Hash'] if row['To Txn Hash'] else row['To Txn Hash']
        df.at[i,'From Txn Hash'] = from_url
        df.at[i,'To Txn Hash'] = to_url
    df['From Txn Hash'] = df['From Txn Hash'].apply(make_clickable)
    df['To Txn Hash'] = df['To Txn Hash'].apply(make_clickable)
    return df


def format_dfs(df):
    df = format_links(df)
    df['From Time'] = pd.to_datetime(df['From Time'],unit='s',utc=True)
    df['To Time'] = pd.to_datetime(df['To Time'],unit='s',utc=True)
    df['From Chain'] = df['From Chain'].map(CHAIN_NETWORK_MAP)
    df['To Chain'] = df['To Chain'].map(CHAIN_NETWORK_MAP)
    df = df.fillna('')
    df = df.sort_values(by=['To Time','From Time'],ascending=False)
    return df


def get_dfs():
    df = get_confirmed_bridge_txs()
    df2 = get_pending_tx_df()
    df = pd.concat([df,df2])
    return df

df = get_dfs()
df = format_dfs(df)

outflow_df=df[df['From Chain']=='moonbeam'].reset_index(drop=True)


st.header('Moonbeam Outflows')
st.write(outflow_df.to_html(escape=False, index=False), unsafe_allow_html=True)
#streamlit.table(data=outflow_df)

inflow_df=df[df['To Chain']=='moonbeam'].reset_index(drop=True)
inflow_df = inflow_df[inflow_df['From Token Address']!='']

st.header('Moonbeam Inflows')
st.write(inflow_df.to_html(escape=False, index=False), unsafe_allow_html=True)
#streamlit.table(data=inflow_df)


pending_df = df[df['Txn Status']=='Pending'].reset_index(drop=True)
st.header('Pending Transactions')
st.write(pending_df.to_html(escape=False, index=False), unsafe_allow_html=True)
#streamlit.table(data=pending_df)