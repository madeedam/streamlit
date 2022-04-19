import streamlit as st
import pandas as pd
import numpy as np
import datetime
import calendar
import os
from io import BytesIO

st.set_page_config(layout="wide")
root = os.path.join(os.path.dirname(__file__))

st.markdown(f'''
    <style>
        .stDownloadButton>button {{
            background-color: #f44336;
            color: white;
            height: 3rem;
            width: 100%;
        }}
    </style>''', unsafe_allow_html=True)

def getEntries(timestamps):
    ValidEntries = []
    for item in timestamps:
        entry, leave = '', ''
        if len(item) == 0:
            entry = ''
            leave = ''

        # CutOff 2 PM
        elif len(item) == 1:
            if int(item[0].split(':')[0]) < 14:
                entry = item[0]
            else:
                leave = item[0]

        elif len(item) == 2:
            entry = item[0]
            leave = item[1]

        else:
            entry = item[0] # First Fingerprint = First Entry
            for x in item[1:]:
                if int(x.split(':')[0]) >= 14: # First Fingerprint after 2PM = Leave
                    leave = x
                    break

        payload = [entry, leave]
        ValidEntries.append(payload)

    return ValidEntries

def Office_K2(uploadedFile, daysinmonth):
    data = pd.read_excel(uploadedFile, engine='xlrd', sheet_name='Catatan')
    col = [('','ID'),('','NAME')]
    for day in daysinmonth:
        col.append((day,'Datang'))
        col.append((day,'Pulang'))

    DF = pd.DataFrame(columns=pd.MultiIndex.from_tuples(col))
    for index in range(3,len(data),2):
        EID = str(data.at[index,'Unnamed: 2']).strip()
        ENAME = str(data.at[index,'Unnamed: 10']).strip()

        if ENAME == 'nan':
            ENAME = ''

        try:
            timestamp = data.iloc[index+1].values
        except IndexError:
            timestamp = np.empty(shape=(1,31), dtype=object).flatten()

        checklog = []
        for line in timestamp:
            checklog.append(str(line).split('\n')[:-1])
        checklog = checklog[:len(daysinmonth)]
        
        VE = getEntries(checklog)
        DF.at[len(DF)] = [EID, ENAME, *[item for sublist in VE for item in sublist]]
    
    return DF

def convertFingerprint():
    with st.sidebar:
        st.subheader("Fingerprint Conversion")
        uploadedFile = st.file_uploader("Upload File")
        officeSelection = st.radio('Select Office', ['Mataram','Jegles'])
        DIM = int(st.number_input("Select Month", value=datetime.datetime.now().month, min_value=1, max_value=12))

    daysinmonth = [datetime.date(2022, DIM, day).strftime('%d/%m/%Y') for day in range(1, calendar.monthrange(2022, DIM)[1]+1)]
    if officeSelection == 'Jegles' and uploadedFile:
        DF = Office_K2(uploadedFile, daysinmonth)
        st.dataframe(DF, height=800)

    if uploadedFile:
        output = BytesIO()
        DF.to_excel(output)
        with st.sidebar:
            st.download_button(
            label="Download Excel workbook",
            data=output.getvalue(),
            file_name="workbook.xlsx",
            mime="application/vnd.ms-excel"
        )
    
convertFingerprint()
