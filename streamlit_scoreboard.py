import pandas as pd
import numpy as np
import re
import streamlit as st
import math
from PIL import Image
pd.options.mode.chained_assignment = None  # default='warn'

def DoScoreBoard(df, score_matrix, ifQF=False):
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
    TB.name = "WorstRound"
    TB2 = df[ss2].max(axis = 1)
    TB2.name = "BestRound"
    scoreboard = scoreboard.merge(TB, how='left', left_index=True, right_index=True)
    scoreboard = scoreboard.merge(TB2, how='left', left_index=True, right_index=True)
    scoreboard['PointsWithTB'] = scoreboard['TotalPoints'] 
    TotalRank = scoreboard['TotalPoints'].rank(axis=0, method='min', ascending=False)
    TotalRank.name = "TotalRank"
    TotalRankTB = scoreboard['PointsWithTB'].rank(axis=0, method='min', ascending=False)
    TotalRankTB.name = "TotalRankTB"
    scoreboard = scoreboard.merge(TotalRank, how='left', left_index=True, right_index=True)
    scoreboard = scoreboard.merge(TotalRankTB, how='left', left_index=True, right_index=True)
    display = scoreboard[['TotalRankTB']+['QualifyPoints']+ss2+['TotalPoints']+['WorstRound']+['BestRound']]
    display = display.sort_values(by=['TotalRankTB'])
    display.columns = ['Rank']+['Qualify']+ss3+['Total']+['WorstRound']+['BestRound']
    display['Rank'] = display['Rank'].astype(int)
    scoreboard['Rank'] = display['Rank'].astype(int)
    if ifQF:
        return display, scoreboard, len(ss2)
    else:
        return display.drop(columns=['Qualify']), scoreboard, len(ss2)
def ifNeedTieBreaker(data, NQualify):
    return NQualify<len(data[data['Rank']<=NQualify])
def DoTieBreaker(data, NQualify):
    d2 = data[data['Rank']<=NQualify]
    d2 = d2.sort_values(by=['Rank'])
    subdf = df[df.index.isin([x for x in d2[d2['Rank']==d2['Rank'][-1]].index])]
    subd, subs, tmp = DoScoreBoard(subdf, score_matrix, True)
    subd2 = subd['Rank']
    subd2.name ='TBRank'
    d_withtb = d.merge(subd2, how='left',left_index=True, right_index=True).fillna(0)
    d_withtb['RankWithTB'] = d_withtb['Rank'] + 0.01*d_withtb['TBRank']-0.0001*d_withtb['WorstRound']-0.000001*d_withtb['BestRound']
    d_withtb['RankWithTB'][d_withtb['TBRank']==0] = 0
    t = d_withtb.sort_values(by=['Rank','RankWithTB'])
    t = t.drop(columns='RankWithTB')
    t['TBRank'] = t['TBRank'].astype(int)
    return t, subd
def GetQualified(data, NQualify):
    return data.iloc[0:NQualify,:].index
def normal_round(n, decimals=0):
    expoN = n * 10 ** decimals
    if abs(expoN) - abs(math.floor(expoN)) < 0.5:
        return math.floor(expoN) / 10 ** decimals
    return math.ceil(expoN) / 10 ** decimals    

file = 'Scoreboard.xlsx'
image = Image.open('CFBLogo.jpg')

st.set_page_config(layout="wide")
st.title("Politimesterskap i Funksjonell Fitness 2022 Leaderboard")

st.image(image,width=100)

ifSemiFinal = True
ifFinal = False
if ifSemiFinal and ifFinal:
    option = st.selectbox(
        'Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage', 'Female Semi-Final', 'Male Semi-Final', 'Female Final', 'Male Final')
    )
elif ifSemiFinal:
    option = st.selectbox('Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage', 'Female Semi-Final', 'Male Semi-Final'))
else:
    option = st.selectbox('Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage'))

if option == 'Male First Stage':
    sheet = 'ScoreM'
    df = pd.read_excel(file, index_col=0, sheet_name = sheet) 
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    df = df.fillna(0)
    d, s, N = DoScoreBoard(df, score_matrix, True)
    if N==5:
        if ifNeedTieBreaker(d, 6):
            display_tb, sub_leaderboard = DoTieBreaker(d, 6)
            st.subheader("Leaderboard")
            st.table(display_tb.drop(columns=['WorstRound','BestRound']))
            st.subheader("Tie-breaker leaderboard")
            st.table(sub_leaderboard.drop(columns=['WorstRound','BestRound']))
        else:
            st.subheader("Leaderboard")
            st.table(d.drop(columns=['WorstRound','BestRound']))
    else:
        st.subheader("Leaderboard")
        st.table(d.drop(columns=['WorstRound','BestRound']))
elif option == 'Female First Stage':
    sheet = 'ScoreF'
    df = pd.read_excel(file, index_col=0, sheet_name = sheet) 
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    df = df.fillna(0)
    d, s, N = DoScoreBoard(df, score_matrix, True)
    if N==5:
        if ifNeedTieBreaker(d, 6):
            display_tb, sub_leaderboard = DoTieBreaker(d, 6)
            st.subheader("Leaderboard")
            st.table(display_tb.drop(columns=['WorstRound','BestRound']))
            st.subheader("Tie-breaker leaderboard")
            st.table(sub_leaderboard.drop(columns=['WorstRound','BestRound']))
        else:
            st.subheader("Leaderboard")
            st.table(d.drop(columns=['WorstRound','BestRound']))
    else:
        st.subheader("Leaderboard")
        st.table(d.drop(columns=['WorstRound','BestRound']))
elif option == 'Male Semi-Final':
    sheet = 'SFM'
    dfsf = pd.read_excel(file, index_col=0, sheet_name = sheet)
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    dfsf['Total Lift'] = dfsf['Snatch']+dfsf['Clean and Jerk']
    dfsf['Rank6'] = dfsf['Total Lift'].rank(axis=0, method='min', ascending=False)
    dfsf['Workout 6 Points'] = 0
    for j in dfsf.index:
        dfsf.loc[j, 'Workout 6 Points'] = score_matrix['points'][dfsf.loc[j, 'Rank6']]
    dfsf['Workout 6 Points'] = dfsf['Workout 6 Points'].astype(int)
    dfsf['Semi Final Total'] = dfsf['Workout 6 Points']+dfsf['First Stage Points']
    dfsf['SFScore'] = dfsf['Semi Final Total']*1000+dfsf['Total Lift']
    dfsf['Semi Final Rank'] = dfsf['SFScore'].rank(axis=0, method='min', ascending=False).astype(int)
    tmpsf = dfsf[['Semi Final Rank', 'Semi Final Total', 'Workout 6 Points', 'First Stage Points', 'Snatch', 'Clean and Jerk', 'Total Lift']]
    tmpsf = tmpsf['Rank'][tmpsf.index=='Ole Andre Elvebakk og Georg Kongsvik'] = 4
    tmpsf = tmpsf.sort_values(by=['Semi Final Rank'])
    st.subheader("Leaderboard")
    st.table(tmpsf)
elif option == 'Female Semi-Final':
    sheet = 'SFF'
    dfsf = pd.read_excel(file, index_col=0, sheet_name = sheet)
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    dfsf['Total Lift'] = dfsf['Snatch']+dfsf['Clean and Jerk']
    dfsf['Rank6'] = dfsf['Total Lift'].rank(axis=0, method='min', ascending=False)
    dfsf['Workout 6 Points'] = 0
    for j in dfsf.index:
        dfsf.loc[j, 'Workout 6 Points'] = score_matrix['points'][dfsf.loc[j, 'Rank6']]
    dfsf['Workout 6 Points'] = dfsf['Workout 6 Points'].astype(int)
    dfsf['Semi Final Total'] = dfsf['Workout 6 Points']+dfsf['First Stage Points']
    dfsf['SFScore'] = dfsf['Semi Final Total']*1000+dfsf['Total Lift']
    dfsf['Semi Final Rank'] = dfsf['SFScore'].rank(axis=0, method='min', ascending=False).astype(int)
    tmpsf = dfsf[['Semi Final Rank', 'Semi Final Total', 'Workout 6 Points', 'First Stage Points', 'Snatch', 'Clean and Jerk', 'Total Lift']].sort_values(by=['Semi Final Rank'])
    st.subheader("Leaderboard")
    st.table(tmpsf)
elif option == 'Male Final':
    sheet = 'FM'
    dff = pd.read_excel(file, index_col=0, sheet_name = sheet)
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    dff['FScore'] = dff['Rep']*10000-dff['Minute']*60-dff['Second']
    dff['Rank7'] = dff['FScore'].rank(axis=0, method='min', ascending=False).astype(int)
    dff['Workout 7 Points'] = 0
    for j in dff.index:
        dff.loc[j, 'Workout 7 Points'] = score_matrix['points'][dff.loc[j, 'Rank7']]
    dff['Workout 7 Points'] = dff['Workout 7 Points'].astype(int)
    dff['Final Total Points'] = dff['First Stage Points'] + dff['Workout 6 Points'] + dff['Workout 7 Points']
    dff['Final Rank'] = dff['Final Total Points'].rank(axis=0, method='min', ascending=False).astype(int)
    tmpf = dff[['Final Rank', 'Final Total Points', 'Workout 7 Points', 'Workout 6 Points', 'First Stage Points', 'Minute', 'Second', 'Rep']]
    st.subheader("Leaderboard")
    st.table(tmpf)
elif option == 'Female Final':
    sheet = 'FF'
    dff = pd.read_excel(file, index_col=0, sheet_name = sheet)
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    dff['FScore'] = dff['Rep']*10000-dff['Minute']*60-dff['Second']
    dff['Rank7'] = dff['FScore'].rank(axis=0, method='min', ascending=False).astype(int)
    dff['Workout 7 Points'] = 0
    for j in dff.index:
        dff.loc[j, 'Workout 7 Points'] = score_matrix['points'][dff.loc[j, 'Rank7']]
    dff['Workout 7 Points'] = dff['Workout 7 Points'].astype(int)
    dff['Final Total Points'] = dff['First Stage Points'] + dff['Workout 6 Points'] + dff['Workout 7 Points']
    dff['Final Rank'] = dff['Final Total Points'].rank(axis=0, method='min', ascending=False).astype(int)
    tmpf = dff[['Final Rank', 'Final Total Points', 'Workout 7 Points', 'Workout 6 Points', 'First Stage Points', 'Minute', 'Second', 'Rep']]
    st.subheader("Leaderboard")
    st.table(tmpf)
