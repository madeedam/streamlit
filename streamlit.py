import pandas as pd
import streamlit as st
import datetime

st.set_page_config(
    layout="centered", page_icon="📝", page_title="Inventory Stock Control", initial_sidebar_state='collapsed'
)
# Bye Bye Menu
# st.markdown(""" <style>
# #MainMenu {visibility: hidden;}
# footer {visibility: hidden;}
# </style> """, unsafe_allow_html=True)

# Session Key
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = '-'

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(sep=';').encode('utf-8')

def stripData(dataframe):
    tempdf = dataframe.copy()
    tempdf.columns = tempdf.columns.str.strip()

    df_obj = tempdf.select_dtypes(['object'])
    tempdf[df_obj.columns] = df_obj.apply(lambda x: x.str.replace("'",'').str.strip())
    
    return tempdf

st.title("📝 L'Oreal Inventory")

@st.cache(allow_output_mutation=True)
def getInventory(url):
    tempdf = stripData(pd.read_csv(url, delimiter=';', dtype=str))
    tempdf['QTY STOK UPDATE(PCS)'] = tempdf['QTY STOK UPDATE(PCS)'].apply(lambda x: int(x.replace('.','')))
    tempdf['ISI/LSN'] = tempdf['ISI/LSN'].astype(int)
    tempdf['SCH-RCNG'] = tempdf['NAMA BARANG'].str.contains('SCH-R')
    tempdf['PCODE-SCYLLA'] = tempdf['KODE SCYLLA'] + ' | ' + tempdf['NAMA BARANG']
    tempdf['PCODE-DMS'] = tempdf['KODE DMS'] + ' | ' + tempdf['NAMA BARANG']
    st.session_state.last_updated = datetime.datetime.now().strftime('%B %d ,%Y - %H:%M:%S')
    return tempdf, st.session_state.last_updated

INV, last_updated = getInventory('https://github.com/madeedam/streamlit/blob/main/INV.csv')
st.success(f"Last updated: {last_updated}")

pcode_choice = st.selectbox('Tipe PCODE', ['DMS','SCYLLA'])

if pcode_choice == 'DMS':
    selection = st.selectbox("Product Name", INV['PCODE-DMS'])
elif pcode_choice == 'SCYLLA':
    selection = st.selectbox("Product Name", INV['PCODE-SCYLLA'])

ProdName = [x.strip() for x in selection.split('|')][1]
ItemInfo = INV[INV['NAMA BARANG'] == ProdName]

TotalPCS, Carton, Pieces = ItemInfo['QTY STOK UPDATE(PCS)'].values[0],0,0
if ItemInfo['SCH-RCNG'].values == True:
    tempvalue = ItemInfo['QTY STOK UPDATE(PCS)'].values[0] / 8
    Carton = int(tempvalue // ItemInfo['ISI/LSN'].values[0])
    Pieces = int(tempvalue % ItemInfo['ISI/LSN'].values[0])
else:
    Carton = int(TotalPCS // ItemInfo['ISI/LSN'].values[0])
    Pieces = int(TotalPCS % ItemInfo['ISI/LSN'].values[0])

st.text_input("Stock Awal", value=f"{str(Carton).zfill(3)}.000.{str(Pieces).zfill(3)} <=> {TotalPCS} pcs", disabled=True)

# Download file
df = convert_df(INV)
if st.sidebar.download_button("Download File", data=df, file_name='INV.csv', mime='text/csv'):
    st.sidebar.info("Downloading")
