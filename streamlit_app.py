from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')
st.markdown(f'''
    <style>
        .css-18e3th9 {{padding-top: 2rem; padding-bottom: 0rem;}}
        .stButton>button {{height: 2.5rem; width: 100%;}}
    </style>''', unsafe_allow_html=True)
# ------------------------------------------------------------------------------------------------------------------------------------------------------
@st.experimental_memo
def parseSND(filepath):
    # Local File
    # with open(filepath,'r') as f:
    #     data = f.read().rstrip().splitlines()

    # Upload File
    data = []
    for line in filepath:
        _ = line.decode('utf-8').strip()
        if len(_) != 0:
            data.append(_)
    SUID_IMPORT = pd.DataFrame([line.replace('"','').split(';') for line in data[4:]], columns=data[1].split(';'), dtype=str)
    SUID_IMPORT = SUID_IMPORT.drop(SUID_IMPORT[~SUID_IMPORT['INVNumber'].apply(lambda x: x.isdigit())].index).reset_index(drop=True)

    for index, row in SUID_IMPORT.iterrows():
        SUID_IMPORT.at[index,'Outlet'] = row['Outlet'][-15:]

        SUID_IMPORT.at[index,'Case'] = int(row['Case'].replace(',',''))
        SUID_IMPORT.at[index,'Dozen'] = int(row['Dozen'].replace(',',''))
        SUID_IMPORT.at[index,'Pieces'] = int(row['Pieces'].replace(',',''))
        SUID_IMPORT.at[index,'TotalQuantity(PCS)'] = int(row['TotalQuantity(PCS)'].replace(',',''))

        SUID_IMPORT.at[index,'GSV'] = float(row['GSV'].replace(',',''))
        SUID_IMPORT.at[index,'Discount'] = float(row['Discount'].replace(',',''))
        SUID_IMPORT.at[index,'Tax'] = float(row['Tax'].replace(',',''))
        SUID_IMPORT.at[index,'Net'] = float(row['Net'].replace(',',''))
    return SUID_IMPORT

@st.experimental_memo
def parseMO(filepath):
    MO = pd.read_excel(filepath, header=8, engine='openpyxl', dtype=str)

    # Sanitize Table
    MO.columns = MO.columns.str.strip()
    MO_object = MO.select_dtypes(['object'])
    MO[MO_object.columns] = MO_object.apply(lambda x: x.str.replace("'",'').str.strip())

    MO['NO'] = MO['NO'].apply(pd.to_numeric, errors='coerce')
    MO = MO.dropna(subset=['NO'])
    MO = MO.drop(columns='NO', axis=1)

    MO = MO[MO['NAMA OUTLET'].notna()].reset_index(drop=True)
    MO['COMBINED'] = MO['NOMOR'] + ' - ' + MO['NAMA OUTLET']
    return MO

@st.experimental_memo
def parseMB(filepath):
    MB = pd.read_excel(filepath, header=19, engine='openpyxl', dtype=str)
    MB.columns = MB.columns.str.strip()
    MB_object = MB.select_dtypes(['object'])
    MB[MB_object.columns] = MB_object.apply(lambda x: x.str.replace("'",'').str.strip())
    MB['NO'] = MB['NO'].apply(pd.to_numeric, errors='coerce')
    MB = MB.dropna(subset=['NO'])
    MB = MB.drop(columns='NO', axis=1)
    MB['KONV.B'] = MB['KONV.B'].astype(int)
    MB['KONV.K'] = MB['KONV.K'].astype(int)
    return MB

def generateFiles(dataframe):
    IngestData = dataframe.copy()
    DORDER = []
    HORDER = []

    DORDER.append("DORDER")
    HORDER.append("HORDER")

    for index, row in IngestData.iterrows():
        Invoice = str(row['INVNumber'])[-8:].ljust(8)
        
        # DORDER Requirements
        SKU = str(row['SKUCode'])[-15:].ljust(15)
        Case = str(row['Case']).ljust(5)
        Dozen = str(row['Dozen']).ljust(3)
        Pieces = str(row['Pieces']).ljust(3)

        # HORDER Requirements
        Outlet = str(row['Outlet'])[-15:].ljust(15)
        PONumber = str(row['INVNumber'])[-8:].ljust(8)
        NoMobil = str().ljust(12)
        PaymentType = str().ljust(1)

        DORDER.append(f"{Invoice}{SKU}{Case}{Dozen}{Pieces}")
        HORDER.append(f"{Invoice}{Outlet}{PONumber}{NoMobil}{PaymentType}")

    LineCount = len(IngestData) + 2
    DORDER.append(f"\\\END{str(LineCount).zfill(4)}")
    HORDER.append(f"\\\END{str(LineCount).zfill(4)}")

    DORDER_CONTENT = '\n'.join(DORDER)
    HORDER_CONTENT = '\n'.join(HORDER)
    st.session_state['isFilesGenerated'] = True
    return DORDER_CONTENT, HORDER_CONTENT

def spacer(x):
    for _ in range(0,x):
        st.write("")

def showTable(dataframe, setTableHeight = 500, configureSelection = 'single'):
    options = GridOptionsBuilder.from_dataframe(dataframe, enableRowGroup=True, enableValue=True, enablePivot=True, editable=False)
    options.configure_side_bar()
    options.configure_selection(configureSelection, groupSelectsChildren=True, groupSelectsFiltered=True, use_checkbox=True, suppressRowClickSelection=True)
    HCS = False
    if configureSelection == 'multiple':
        HCS = True
    options.configure_column('INVNumber', headerCheckboxSelection=HCS)
    gridOptions = options.build()

    return AgGrid(
        dataframe,
        gridOptions=gridOptions,
        height=setTableHeight,
        theme='light,'
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        data_return_mode=DataReturnMode.FILTERED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
    )
# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Session States
if 'UID_SALES' not in st.session_state:
    st.session_state['UID_SALES'] = ''
if 'TempDF' not in st.session_state:
    st.session_state['TempDF'] = pd.DataFrame(columns=['INVNumber','Outlet','Outlet Name'])
if 'MergerTable' not in st.session_state:
    st.session_state['MergerTable'] = pd.DataFrame(columns=['INVNumber','Outlet','Outlet Name','mOutlet','mName','Iteration'])
if 'IterationCounter' not in st.session_state:
    st.session_state['IterationCounter'] = '0'
if 'Finalized' not in st.session_state:
    st.session_state['Finalized'] = ''
if 'isFilesGenerated' not in st.session_state:
    st.session_state['isFilesGenerated'] = False
if 'LastProcessedIteration' not in st.session_state:
    st.session_state['LastProcessedIteration'] = 0
# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Main Code
page1, page2, page3, page4, page5, page6 = st.tabs(['Upload','Merger','Confirmation','Download','Debug','Settings'])

with page1:
    rawUpload = st.file_uploader('Required Files', accept_multiple_files=True)
    if len(rawUpload) != 4:
        st.error('Missing Files.')
        st.stop()

    # File Verification...
    LOG_START_TIME = time.time()
    for uFile in rawUpload:
        if uFile.name == 'MB.XLS':
            MB = parseMB(uFile)
        elif uFile.name == 'MO.XLS':
            MO = parseMO(uFile)
        elif 'Processed' in uFile.name:
            PreviousInvoices = pd.read_csv(uFile, dtype=str)
        elif 'UID Extract Secondary Sale Data Report' in uFile.name:
            UID_SALES = parseSND(uFile)
        else:
            st.error(f'Unknown File | {uFile.name}')
            st.stop()
    st.success(f'Upload Completed... {time.time() - LOG_START_TIME:.2f}s')

    TotalInvoice = len(UID_SALES['INVNumber'].unique())
    if not PreviousInvoices.empty:
        st.session_state['LastProcessedIteration'] = int(PreviousInvoices['Iteration'].max())
        print(f'Last Iteration = {PreviousInvoices["Iteration"].max()}')
        OldInvoices = PreviousInvoices['INVNumber'].tolist()
        for index, row in UID_SALES.iterrows():
            if row['INVNumber'] in OldInvoices:
                UID_SALES.drop(index, inplace=True)

        if UID_SALES.empty:
            st.error('Nothing to be processed.')
            st.stop()
        else:
            UID_SALES = UID_SALES.reset_index(drop=True)
    UnprocessedInvoices = len(UID_SALES['INVNumber'].unique())
    st.warning(f'To be processed | {TotalInvoice:3} - {TotalInvoice - UnprocessedInvoices:3} = {UnprocessedInvoices:3}')

    st.session_state['UID_SALES'] = UID_SALES.copy()
    st.session_state['PendingInvoices'] = UID_SALES[['INVNumber','Outlet','Outlet Name']].drop_duplicates()

    # REMOVE THIS IF POSSIBLE
    st.markdown('---')
    if st.button('Reset Experimental Memo'):
        st.experimental_memo.clear()
        for _ in st.session_state.keys():
                del st.session_state[_]
        st.experimental_rerun()

# Merger
with page2:
    P2_DF = st.session_state['PendingInvoices']
    with st.container():
        leftcol, _, centercol, _, rightcol = st.columns([6,0.15,0.7,0.15,6])
        _, iRC1, iRC2 = st.columns([7,5,1])

        # Variables Configuration
        cacheIndex = 0
        disableSelectbox = True
        disableMergeButton = True
        confirmMergerButton = False

        # Remove Merged Invoices
        MERGE_LIST = st.session_state['MergerTable']['INVNumber'].tolist()
        for index, row in P2_DF.iterrows():
            if row['INVNumber'] in MERGE_LIST:
                P2_DF.drop(index, inplace=True)

        with leftcol:
            LDF = showTable(P2_DF, configureSelection='multiple')

            # PreSelectIndex
            if LDF['selected_rows']:
                cacheIndex = MO[MO['NOMOR'] == LDF['selected_rows'][0]['Outlet']].index.tolist()
                cacheIndex = cacheIndex[0]

        with centercol:
            spacer(10)
            if st.button(">"):
                if LDF['selected_rows']:
                    st.session_state['TempDF'] = pd.DataFrame(LDF['selected_rows'])
            if st.button("<"):
                st.session_state['TempDF'] = pd.DataFrame(columns=['INVNumber','Outlet','Outlet Name'])

        with rightcol:
            RDF = showTable(st.session_state['TempDF'])

            if not RDF['data'].empty:
                if not RDF['selected_rows']:
                    disableSelectbox = False
                else:
                    cacheIndex = MO[MO['NOMOR'].str.contains(RDF['selected_rows'][0]['Outlet'])].index.tolist()
                    if len(cacheIndex) != 1:
                        st.error(f"Programming Error | SelectedIndex Length = {len(cacheIndex)} | Line 210")
                        st.stop()
                    cacheIndex = cacheIndex[0]
                disableMergeButton = False

            with iRC1:
                FORM_SELECTED_OUTLET = st.selectbox('Outlet', (MO['COMBINED']).to_list(), index=cacheIndex, disabled=disableSelectbox)
                FORM_SELECTED_OUTLET = [x.strip() for x in FORM_SELECTED_OUTLET.split('-')][0]

            with iRC2:
                spacer(2)
                confirmMergerButton = st.button('Merge', disabled=disableMergeButton)
    if confirmMergerButton:
        st.session_state['TempDF']['mOutlet'] = FORM_SELECTED_OUTLET
        st.session_state['TempDF']['mName'] = MO[MO['NOMOR'] == FORM_SELECTED_OUTLET]['NAMA OUTLET'].values[0]
        st.session_state['TempDF']['Iteration'] = st.session_state['IterationCounter']
        st.session_state['IterationCounter'] = str(int(st.session_state['IterationCounter']) + 1)
        st.session_state['MergerTable'] = pd.concat([st.session_state['MergerTable'], st.session_state['TempDF']], ignore_index=True)

        del st.session_state['TempDF']
        st.experimental_rerun()

with page3:
    showTable(st.session_state['MergerTable'])
    if st.button('Confirm Merge'):
        with st.spinner('Wait for it...'):
            start_time = time.time()
            IngestData = st.session_state['UID_SALES'].copy()
            MDF = st.session_state['MergerTable'].copy()

            if not MDF.empty:
                for uIter in MDF['Iteration'].unique():
                    A1 = MDF[MDF['Iteration'] == uIter]
                    A1_INDEX = A1.first_valid_index()

                    for index, row in A1.iterrows():
                        match = (IngestData['INVNumber'] == row['INVNumber']) & (IngestData['Outlet'] == row['Outlet'])
                        mIndex = IngestData[match].index
                        
                        for index in mIndex:
                            IngestData.at[index, 'INVNumber'] = A1.at[A1_INDEX, 'INVNumber']
                            IngestData.at[index, 'Outlet'] = row['mOutlet']
                            IngestData.at[index, 'Outlet Name'] = row['mName']
            else:
                st.warning('Nothing to be merged.')

            IngestData = IngestData.groupby(['INVNumber','Outlet','SKUCode'], as_index=False)[['Case','Dozen','Pieces','TotalQuantity(PCS)']].sum()
            for index, row in IngestData.iterrows():
                vMB = MB[MB['PCODE'] == row['SKUCode']]
                if len(vMB) != 1:
                    raise SystemExit("Uhh.. Coding Problems | MasterBarang not Unique")
                
                Boolean = (row['Case'] * vMB['KONV.B']) + (row['Dozen'] * vMB['KONV.K']) + row['Pieces'] != row['TotalQuantity(PCS)']
                if Boolean.values[0]:
                    raise SystemExit("Uhh.. Coding Problems | TotalQuantity(PCS) Mismatch")
            st.info(f'Invoice Merged... {time.time() - start_time:.2f}s')

            # SKU Normalization
            start_time = time.time()
            for index, row in IngestData.iterrows():
                vMB = MB[MB['PCODE'] == row['SKUCode']]
                tCase = row['Case']
                tDozen = row['Dozen']
                tPieces = row['Pieces']

                # Pieces to Dozen
                CasePieces = tCase * vMB['KONV.B'].values[0]
                tCase = 0

                DozenPieces = tDozen * vMB['KONV.K'].values[0]
                tDozen = 0

                tPieces += (CasePieces + DozenPieces)

                tCase = tPieces // vMB['KONV.B'].values[0]
                tPieces %= vMB['KONV.B'].values[0]

                IngestData.at[index, 'Case'] = tCase
                IngestData.at[index, 'Dozen'] = tDozen
                IngestData.at[index, 'Pieces'] = tPieces
            st.info(f'SKU Normalized... {time.time() - start_time:.2f}s')

            # Verify Normalization
            start_time = time.time()
            for index, row in IngestData.iterrows():
                vMB = MB[MB['PCODE'] == row['SKUCode']]

                Boolean = (row['Case'] * vMB['KONV.B']) + (row['Dozen'] * vMB['KONV.K']) + row['Pieces'] != row['TotalQuantity(PCS)']
                if Boolean.values[0] or row['Dozen'] > 999 or row['Pieces'] > 999:
                    raise SystemExit("Uhh.. Coding Problems | Normalization Failed")
            st.info(f'Normalization Verified... {time.time() - start_time:.2f}s')
        st.session_state['Finalized'] = IngestData.copy()
        st.success('Done!')

with page4:
    if st.button('Generate Files...') or st.session_state['isFilesGenerated']:
        IngestData = st.session_state['Finalized'].copy()
        DC, HC = generateFiles(IngestData)

        st.markdown('---')
        st.download_button('DORDER', DC, file_name='DORDER.TXT')
        st.download_button('HORDER', HC, file_name='HORDER.TXT')

        ProcessedInvoices = st.session_state['UID_SALES'][['INVNumber','Outlet','Outlet Name']].drop_duplicates()
        ProcessedInvoices.insert(0, 'Iteration', st.session_state['LastProcessedIteration'] + 1)
        
        OUT_PI = pd.concat([PreviousInvoices, ProcessedInvoices]).reset_index(drop=True).to_csv(index=False).encode('utf-8')
        st.download_button(
            "Processed Invoices",
            OUT_PI,
            "Processed.csv",
            "text/csv",
            key='Processed-Invoices'
        )

        st.session_state['isFilesGenerated'] = True

with page5:
    st.session_state

with page6:
    st.error('Nothing to see here.')
