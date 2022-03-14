from re import L
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

INV, last_updated = getInventory('https://raw.githubusercontent.com/madeedam/streamlit/main/INV.csv')
st.success(f"Last updated: {last_updated}")

pcode_choice = st.selectbox('Tipe PCODE', ['DMS','SCYLLA'])

if pcode_choice == 'DMS':
    selection = st.selectbox("Product Name", INV['PCODE-DMS'])
elif pcode_choice == 'SCYLLA':
    selection = st.selectbox("Product Name", INV['PCODE-SCYLLA'])

ProdName = [x.strip() for x in selection.split('|')][1]
ItemInfo = INV[INV['NAMA BARANG'] == ProdName]

CartonConversion = ItemInfo['ISI/LSN'].values[0]
TotalPCS, Carton, Pieces = ItemInfo['QTY STOK UPDATE(PCS)'].values[0],0,0
if ItemInfo['SCH-RCNG'].values == True:
    tempvalue = ItemInfo['QTY STOK UPDATE(PCS)'].values[0] / 8
    Carton = int(tempvalue // CartonConversion)
    Pieces = int(tempvalue % CartonConversion)
else:
    Carton = int(TotalPCS // CartonConversion)
    Pieces = int(TotalPCS % CartonConversion)

st.text_input("Stock Awal", value=f"{str(Carton).zfill(3)}.000.{str(Pieces).zfill(3)} <=> {TotalPCS} pcs", disabled=True)

with st.expander("Adjustment"):
    col1, col2, col3 = st.columns(3)
    with col1:
        CM = st.number_input("Carton", min_value=1, max_value=Carton)
        OpenCarton = Carton - CM
    with col2:
        st.number_input("Pieces", value=(OpenCarton * CartonConversion) + Pieces)
    with col3:
        st.markdown("Save Adjustment")
        st.button("Confirm")

# with st.expander("Selisih"):
#     with st.form("StockManual", clear_on_submit=True):
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.number_input("Carton", value=0)
#         with col2:
#             st.number_input("Pieces", value=0)
#         with col3:
#             st.number_input("Total Pieces", value=0)

#         if st.form_submit_button("Confirm"):
#             st.success("Data telah disimpan.")
        

# Download file
# df = convert_df(INV)
# if st.sidebar.download_button("Download File", data=df, file_name='INV.csv', mime='text/csv'):
#     st.sidebar.info("Downloading")
