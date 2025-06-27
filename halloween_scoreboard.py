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
    ss = ['QualifyPoints']
    ss2 = []
    ss3 = []
    ss4 = []
    for i in range(1, NWorkout+1):
        ss.append(f'WODdisplay{i}')
        m = 'Minute'+str(i)
        s = 'Second'+str(i)
        r = 'Rep'+str(i)
        rankvar = 'rank'+str(i)
        ss.append('points'+str(i))

        df['Score'+str(i)] = df[r]*10000 - df[m]*60 - df[s]
        df[rankvar] = df['Score'+str(i)].rank(method='min', ascending=False)
        df.loc[df[r] == 0, rankvar] = 0

        df['points'+str(i)] = df[rankvar].map(score_matrix['points']).fillna(0).astype(int)
        df['TotalPoints'] += df['points'+str(i)]

    ss.append('TotalPoints')
    for i in range(1, NWorkout+1):
        if df['points'+str(i)].max() > 0:
            ss2.append('points'+str(i))
            ss3.append('Workout '+str(i))
            ss4.append('WODdisplay'+str(i))

    scoreboard = df[ss]
    TB = df[ss2].min(axis=1); TB.name = "WorstRound"
    TB2 = df[ss2].max(axis=1); TB2.name = "BestRound"
    scoreboard = scoreboard.join([TB, TB2])

    scoreboard['PointsWithTB'] = (
        scoreboard['TotalPoints']
        + 0.01 * scoreboard['WorstRound']
        + 0.0001 * scoreboard['BestRound']
    )

    TotalRank = scoreboard['TotalPoints'].rank(method='min', ascending=False).astype(int); TotalRank.name="TotalRank"
    TotalRankTB = scoreboard['PointsWithTB'].rank(method='min', ascending=False).astype(int); TotalRankTB.name="TotalRankTB"

    scoreboard = scoreboard.join([TotalRank, TotalRankTB])
    display = scoreboard[['TotalRankTB','QualifyPoints']+ss2+['TotalPoints','WorstRound','BestRound']]
    display = display.sort_values('TotalRankTB')
    display.columns = ['Rank','Qualify'] + ss3 + ['Total','WorstRound','BestRound']
    display['Rank'] = display['Rank'].astype(int)

    woddis = scoreboard[ss4 + ss2]

    if ifQF:
        return display, scoreboard, woddis
    else:
        return display.drop(columns=['Qualify']), scoreboard, woddis


def get_wod_display(wod, mm, ss, rep, tp, total_rd=1):
    mm, ss, rep = int(mm), int(ss), int(rep)
    reps_per_rd = sum(wod.values())

    if tp == 'FT':
        total_rep = total_rd * reps_per_rd
        if rep == total_rep:
            return f'{mm:02d}:{ss:02d}'
        N_rd = rep // reps_per_rd
        rem = rep - N_rd*reps_per_rd
        parts = []
        if N_rd:
            parts.append(f'{N_rd} rounds')
        if rem:
            parts.append(f'+{rem}')
        return ' '.join(parts) or ''

    if tp == 'AMRAP':
        N_rd = rep // reps_per_rd
        rem = rep - N_rd*reps_per_rd
        parts = []
        if N_rd:
            parts.append(f'{N_rd} rounds')
        if rem:
            parts.append(f'+{rem}')
        return ' '.join(parts) or ''

    if tp == 'Other':
        return f'{rep} {list(wod.keys())[0]}'
    return ''


# --- Page visuals ---
wod = [{},{},{},{},{}]
# (your wod definitions here...)
wod_type = {1:'Other',2:'Other',3:'Other'}
wod_rd = {1:1,2:1,3:1}

add_bg_from_local('summerwp.png')
logo = Image.open('CFBLogo.jpg')

st.title("CrossFit Bryggen Summer Games 2025")
st.image(logo, width=100)

option = st.selectbox(
    'Select leaderboard from the dropdown menu',
    ('Leaderboard', 'Workout 1', 'Workout 2', 'Workout 3')
)

file = 'Scoreboard.xlsx'
headers = [{
    'selector': 'th:not(.index_name)',
    'props': [('background-color', '#82e0dc'),
              ('color', '#000080'),
              ('font-weight','bold')]
}]
text = {
    'color': '#000080',
    'background-color':'#82e0dc'
}

# --- Load data once ---
try:
    # read without index_col so we keep 'Team' as a column
    df_full = pd.read_excel(file, sheet_name='Score')
    # now set Team as index for processing
    df = df_full.set_index('Team').fillna(0)

    score_matrix = (
        pd.read_excel(file, index_col=0, sheet_name='ScoreMatrix')
          .to_dict()
    )
    score_matrix['points'][0] = 0

    # build your WODdisplay columns based on df.index
    for team in df.index:
        r1, r2 = df.at[team,'Row1'], df.at[team,'DP1']
        df.at[team,'WODdisplay1'] = f'{r1+r2} reps = {r1} cals row + {r2} Devil Presses'
    for team in df.index:
        r1, r2 = df.at[team,'Bench2'], df.at[team,'Paddle2']
        df.at[team,'WODdisplay2'] = f'{r1 + r2*10} pts = {r1} kg bench + {r2} beach paddles x10'
    for team in df.index:
        r1 = df.at[team,'Rep3']
        df.at[team,'WODdisplay3'] = f'{r1} cals'

except FileNotFoundError:
    st.text("Scoreboard is not available yet")
    teams = pd.read_excel(file, sheet_name='Score')[['Team']]
    st.table(
        teams
          .style
          .set_table_styles(headers)
          .set_properties(**text)
    )
    st.stop()
except Exception as e:
    st.error(f"Error loading scoreboard: {e}")
    st.stop()


# --- Render based on selection ---
if option == 'Leaderboard':
    try:
        display_df, score_df, wod_display = DoScoreBoard(df, score_matrix, False)
        st.subheader("Leaderboard")
        st.table(
            display_df
              .drop(columns=['WorstRound','BestRound'])
              .style
              .set_table_styles(headers)
              .set_properties(**text)
        )
    except Exception as e:
        st.text(e)
        st.text("Scoreboard is not available yet")
        teams = df_full[['Team']]
        st.table(
            teams
              .style
              .set_table_styles(headers)
              .set_properties(**text)
        )

elif option in ['Workout 1', 'Workout 2', 'Workout 3']:
    wod_num = int(option[-1])
    try:
        _, _, wod_display = DoScoreBoard(df, score_matrix, False)
        w = wod_display.sort_values(by=[f'points{wod_num}'], ascending=False)
        w['CurrentRank'] = w[f'points{wod_num}'].rank(method='min', ascending=False).astype(int)
        dis_w = w[['CurrentRank', f'WODdisplay{wod_num}']]
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
