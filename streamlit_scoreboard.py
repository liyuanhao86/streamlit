import pandas as pd
import numpy as np
import re
import streamlit as st
def DoScoreBoard(file, sheet, ifQF=False):
    df = pd.read_excel(file, index_col=0, sheet_name = sheet) 
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    df = df.fillna(0)
    NWorkout = int(re.search(r"(?<=[A-z])[0-9]+$", df.columns[-1]).group(0))
    if ifQF == False:
        df['QualifyPoints'] = 0
    df['TotalPoints'] = df['QualifyPoints']
    ss = ['QualifyPoints']
    ss2 = []
    ss3 = []
    for i in range(1, NWorkout+1):
        m = 'Minute'+str(i)
        s = 'Second'+str(i)
        r = 'Rep'+str(i)
        rankvar = 'rank'+str(i)
        ss.append('points'+str(i))
        df['Score'+str(i)] = df[r]*10000-df[m]*60-df[s]
        df[rankvar] = df['Score'+str(i)].rank(axis=0, method='min', ascending=False)
        df.loc[df[r] == 0, rankvar] = 0
        df['points'+str(i)] = 0
        for j in df.index:
            df.loc[j, 'points'+str(i)] = score_matrix['points'][df.loc[j, rankvar]]
        df['TotalPoints'] += df['points'+str(i)]
    ss.append('TotalPoints')
    for i in range(1, NWorkout+1):
        if df['points'+str(i)].max() > 0:
            ss2.append('points'+str(i))
            ss3.append('Workout '+str(i))
    scoreboard = df[ss]
    TB = df[ss2].min(axis = 1)
    TB.name = "TieBreaker"
    TB2 = df[ss2].max(axis = 1)
    TB2.name = "TieBreaker2"
    scoreboard = scoreboard.merge(TB, how='left', left_index=True, right_index=True)
    scoreboard = scoreboard.merge(TB2, how='left', left_index=True, right_index=True)
    scoreboard['PointsWithTB'] = scoreboard['TotalPoints'] + scoreboard['TieBreaker']*0.01 + scoreboard['TieBreaker']*0.0001
    TotalRank = scoreboard['TotalPoints'].rank(axis=0, method='min', ascending=False)
    TotalRank.name = "TotalRank"
    TotalRankTB = scoreboard['PointsWithTB'].rank(axis=0, method='min', ascending=False)
    TotalRankTB.name = "TotalRankTB"
    scoreboard = scoreboard.merge(TotalRank, how='left', left_index=True, right_index=True)
    scoreboard = scoreboard.merge(TotalRankTB, how='left', left_index=True, right_index=True)
    display = scoreboard[['TotalRankTB']+['TotalPoints']+['QualifyPoints']+ss2]
    display = display.sort_values(by=['TotalRankTB'])
    display.columns = ['Rank']+['Total']+['Qualify']+ss3
    scoreboard2 = scoreboard.applymap('{:,.0f}'.format)
    display2 = display.applymap('{:,.0f}'.format)
    if ifQF:
        return display2, scoreboard2
    else:
        return display2.drop(columns=['Qualify']), scoreboard2

def DoSemiFinal(file, sheet, ifQF=False):
    df = pd.read_excel(file, index_col=0, sheet_name = sheet) 
    df['Total'] = df.iloc[:,0] + df.iloc[:,1]
    df['Rank'] = df['Total'].rank(axis=0, method='min', ascending=False)
    tmp = df.pop('Total')
    df.insert(0, 'Total', tmp)
    tmp = df.pop('Rank')
    df.insert(0, 'Rank', tmp)
    display = df.applymap('{:,.0f}'.format)
    display = display.sort_values(by=['Rank'])
    return display

f = 'C:\\Users\\yhli1\\OneDrive - Mowi ASA\\work_files\\CrossFit\\Scoreboard.xlsx'
f = 'C:\\Users\\Yuanhao.Li\\OneDrive - Mowi ASA\\work_files\\CrossFit\\Scoreboard.xlsx'
f = 'Scoreboard.xlsx'

st.set_page_config(layout="wide")
st.title("Frivillige PM 2022 Leaderboard")
option = st.selectbox('Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage', 'Female Semi-Final', 'Male Semi-Final'))
if option == 'Male First Stage':
    sht = 'ScoreM'
    d, s = DoScoreBoard(f, sht, True)
elif option == 'Female First Stage':
    sht = 'ScoreF'
    d, s = DoScoreBoard(f, sht, True)
if option == 'Male Semi-Final':
    sht = 'SFM'
    d = DoSemiFinal(f, sht, True)
elif option == 'Female Semi-Final':
    sht = 'SFF'
    d = DoSemiFinal(f, sht, True)
st.table(d)
