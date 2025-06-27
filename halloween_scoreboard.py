import pandas as pd
import numpy as np
import re
import math
import streamlit as st
from PIL import Image
import base64

st.set_page_config(layout="wide")

def add_bg_from_local(image_file):
    with open(image_file, "rb") as img:
        encoded_string = base64.b64encode(img.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/png;base64,{encoded_string.decode()});
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

def DoScoreBoard(df, score_matrix, ifQF=False):
    NWorkout = int(re.search(r"(?<=[A-z])[0-9]+$", df.columns[-1]).group(0))
    if not ifQF:
        df['QualifyPoints'] = 0
    df['TotalPoints'] = df['QualifyPoints']
    ss, ss2, ss3, ss4 = ['QualifyPoints'], [], [], []

    for i in range(1, NWorkout+1):
        ss.append(f'WODdisplay{i}')
        m, s, r = f'Minute{i}', f'Second{i}', f'Rep{i}'
        rankvar = f'rank{i}'; ptsvar = f'points{i}'
        ss.append(ptsvar)

        df[f'Score{i}'] = df[r]*10000 - df[m]*60 - df[s]
        df[rankvar] = df[f'Score{i}'].rank(method='min', ascending=False)
        df.loc[df[r] == 0, rankvar] = 0
        df[ptsvar] = df[rankvar].map(score_matrix['points']).fillna(0).astype(int)
        df['TotalPoints'] += df[ptsvar]

    ss.append('TotalPoints')
    for i in range(1, NWorkout+1):
        if df[f'points{i}'].max() > 0:
            ss2.append(f'points{i}')
            ss3.append(f'Workout {i}')
            ss4.append(f'WODdisplay{i}')

    scoreboard = df[ss]
    TB  = df[ss2].min(axis=1);   TB.name  = "WorstRound"
    TB2 = df[ss2].max(axis=1);   TB2.name = "BestRound"
    scoreboard = scoreboard.join([TB, TB2])
    scoreboard['PointsWithTB'] = (
        scoreboard['TotalPoints']
        + 0.01 * scoreboard['WorstRound']
        + 0.0001 * scoreboard['BestRound']
    )

    tr  = scoreboard['TotalPoints'].rank(method='min', ascending=False).astype(int);  tr.name  = "TotalRank"
    trb = scoreboard['PointsWithTB'].rank(method='min', ascending=False).astype(int); trb.name = "TotalRankTB"
    scoreboard = scoreboard.join([tr, trb])

    display = scoreboard[['TotalRankTB','Q]()]()
