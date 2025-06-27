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
        rankvar, ptsvar = f'rank{i}', f'points{i}'

        df[f'Score{i}'] = df[r]*10000 - df[m]*60 - df[s]
        df[rankvar] = df[f'Score{i}'].rank(method='min', ascending=False)
        df.loc[df[r] == 0, rankvar] = 0
        df[ptsvar] = df[rankvar].map(score_matrix['points']).fillna(0).astype(int)
        df['TotalPoints'] += df[ptsvar]
        ss.append(ptsvar)

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

    display = scoreboard[['TotalRankTB','QualifyPoints'] + ss2 + ['TotalPoints','WorstRound','BestRound']]
    display = display.sort_values('TotalRankTB')
    display.columns = ['Rank','Qualify'] + ss3 + ['Total','WorstRound','BestRound']
    display['Rank'] = display['Rank'].astype(int)

    woddis = scoreboard[ss4 + ss2]
    return (display, scoreboard, woddis) if ifQF else (display.drop(columns=['Qualify']), scoreboard, woddis)


def get_wod_display(wod, mm, ss, rep, tp, total_rd=1):
    mm, ss, rep = map(int, (mm, ss, rep))
    reps_per_rd = sum(wod.values())

    if tp == 'FT':
        total_rep = reps_per_rd * total_rd
        if rep == total_rep:
            return f'{mm:02d}:{ss:02d}'
        rounds, rem = divmod(rep, reps_per_rd)
        parts = ([f'{rounds} rounds'] if rounds else []) + ([f'+{rem}'] if rem else [])
        return ' '.join(parts) or ''

    if tp == 'AMRAP':
        rounds, rem = divmod(rep, reps_per_rd)
        parts = ([f'{rounds} rounds'] if rounds else []) + ([f'+{rem}'] if rem else [])
        return ' '.join(parts) or ''

    if tp == 'Other':
        return f'{rep} {list(wod.keys())[0]}'
    return ''


# --- Page visuals setup ---
wod       = [{},{},{},{},{}]  # define as needed
wod_type  = {1:'Other',2:'Other',3:'Other'}
wod_round = {1:1,2:1,3:1}

add_bg_from_local('summerwp.png')
logo = Image.open('CFBLogo.jpg')

st.title("CrossFit Bryggen Summer Games 2025")
st.image(logo, width=100)

option = st.selectbox(
    'Select leaderboard from the dropdown menu',
    ('Leaderboard','Workout 1','Workout 2','Workout 3')
)

file = 'Scoreboard.xlsx'
headers = [{
    'selector': 'th:not(.index_name)',
    'props': [
        ('background-color', '#82e0dc'),
        ('color', '#000080'),
        ('font-weight','bold')
    ]
}]
text = {'color':'#000080','background-color':'#82e0dc'}


# --- Load data once ---
try:
    df_full = pd.read_excel(file, sheet_name='Score')
    df      = df_full.set_index('Team').fillna(0)
    score_matrix = pd.read_excel(file, index_col=0, sheet_name='ScoreMatrix').to_dict()
    score_matrix['points'][0] = 0

    # build WODdisplay columns
    for t in df.index:
        df.at[t,'WODdisplay1'] = (
            f"{df.at[t,'Row1']+df.at[t,'DP1']} reps = "
            f"{df.at[t,'Row1']} cals row + {df.at[t,'DP1']} Devil Presses"
        )
        df.at[t,'WODdisplay2'] = (
            f"{df.at[t,'Bench2']+df.at[t,'Paddle2']*10} pts = "
            f"{df.at[t,'Bench2']} kg bench + {df.at[t,'Paddle2']} beach paddles x10"
        )
        df.at[t,'WODdisplay3'] = f"{df.at[t,'Rep3']} cals"

except FileNotFoundError:
    st.text("Scoreboard is not available yet")
    teams = pd.read_excel(file, sheet_name='Score')[['Team']]
    rows = teams.to_dict(orient='records')
    st.table(rows)
    st.stop()

except Exception as e:
    st.error(f"Error loading scoreboard: {e}")
    st.stop()


# --- Render based on user choice ---
if option == 'Leaderboard':
    try:
        disp, _, _ = DoScoreBoard(df, score_matrix, False)
        st.subheader("Leaderboard")
        st.table(
            disp
              .drop(columns=['WorstRound','BestRound'])
              .style
              .set_table_styles(headers)
              .set_properties(**text)
        )
    except Exception:
        st.text("Scoreboard is not available yet")
        teams = df_full[['Team']]
        rows = teams.to_dict(orient='records')
        st.table(rows)

elif option in ['Workout 1','Workout 2','Workout 3']:
    n = int(option[-1])
    try:
        _, _, wod_disp = DoScoreBoard(df, score_matrix, False)
        w = wod_disp.sort_values(by=[f'points{n}'], ascending=False)
        w['CurrentRank'] = w[f'points{n}'].rank(method='min', ascending=False).astype(int)
        dis_w = w[['CurrentRank', f'WODdisplay{n}']]
        dis_w.columns = ['Rank', option]
        st.subheader(option)
        st.table(
            dis_w
              .style
              .set_table_styles(headers)
              .set_properties(**text)
        )
    except Exception:
        st.text(f"Scoreboard for {option} is not available yet")
