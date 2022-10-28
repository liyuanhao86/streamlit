import pandas as pd
import numpy as np
import re
import math
import streamlit as st
def DoScoreBoard(file, sheet, ifQF=False):
	wod=[{},{},{},{},{}]
	wod[0] = {
		'Single-Unders':150,
		'Burpee BGO': 15,
		'Sumo DLHP':50,
		'Burpee BGO2':15,
		'Single-Unders2':150
	}
	wod[1] = {
		'Reps':1
	}
	wod[2] = {
		'Wall walks':6,
		'Wallballs':50,
		'Deadlifts':30
	}
	wod[3] = {
		'Row':400,
		'T2B':40,
		'Row2':400,
		'HSPU':20
	}
	wod[4] = {
		'kg':1
	}
	wod_type = {1:'FT',2:'Other',3:'FT',4:'FT',5:'Other'}
	wod_rd = {1:1,2:1,3:3,4:1,5:1}
	
	df = pd.read_excel(file, index_col=0, sheet_name = sheet).set_index(['Team'])
    score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
    score_matrix['points'][0]=0
    df = df.fillna(0)
	
	if sheet in ['ScoreM', 'ScoreF']:
		for w in range(1,4):
			df[f'WODdisplay{w}'] = ''
			for team in df.index:
				m = df[f'Minute{w}'][team]
				s = df[f'Second{w}'][team]
				r = df[f'Rep{w}'][team]
				df.loc[team,f'WODdisplay{w}']=get_wod_display(wod[w-1], m, s, r, wod_type[w], total_rd=wod_rd[w])
	if sheet in ['SFM', 'SFF']:
		for w in range(1,3):
			df[f'WODdisplay{w}'] = ''
			for team in df.index:
				m = df[f'Minute{w}'][team]
				s = df[f'Second{w}'][team]
				r = df[f'Rep{w}'][team]
				df.loc[team,f'WODdisplay{w}']=get_wod_display(wod[w+2], m, s, r, wod_type[w], total_rd=wod_rd[w])
				
    NWorkout = int(re.search(r"(?<=[A-z])[0-9]+$", df.columns[-1]).group(0))
    if ifQF == False:
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
            ss4.append('WODdisplay'+str(i))
    scoreboard = df[ss]
    TB = df[ss2].min(axis = 1)
    TB.name = "WorstRound"
    TB2 = df[ss2].max(axis = 1)
    TB2.name = "BestRound"
    scoreboard = scoreboard.merge(TB, how='left', left_index=True, right_index=True)
    scoreboard = scoreboard.merge(TB2, how='left', left_index=True, right_index=True)
    scoreboard['PointsWithTB'] = scoreboard['TotalPoints']+0.01*scoreboard['WorstRound']+0.0001*scoreboard['BestRound']
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
    woddis = scoreboard[ss4+ss2]
    if ifQF:
        return display, scoreboard, woddis
    else:
        return display.drop(columns=['Qualify']), scoreboard, woddis

def get_wod_display(wod, mm, ss, rep, tp, total_rd = 1):
    mm = int(mm)
    ss = int(ss)
    rep = int(rep)
    reps_per_rd = 0
    for i in wod.keys():
        reps_per_rd += wod[i]
    if tp == 'FT':
        total_rep = total_rd * reps_per_rd
        if rep == total_rep:
            display = f'{mm:02d}:{ss:02d}'
        else:
            N_rd = math.floor(rep/reps_per_rd)
            if N_rd > 0:
                display1 = f'{N_rd} rounds'
            else:
                display1 = ''
            reps_remain = rep - N_rd*reps_per_rd
            if reps_remain == 0 or N_rd == 0:
                display2 = ''
            else:
                display2 = '+'
            for k in wod.keys():
                if reps_remain <= wod[k]:
                    display2 = display2+str(reps_remain)+' '+re.sub('[0-9]$','',k)+', '
                else:
                    display2 = display2+str(wod[k])+' '+re.sub('[0-9]$','',k)+', '
                reps_remain = reps_remain - wod[k]
                if reps_remain <= 0:
                    break
            display = display1 + display2
    if tp == 'AMRAP':
        N_rd = math.floor(rep/reps_per_rd)
        if N_rd > 0:
            display1 = f'{N_rd} rounds'
        else:
            display1 = ''
        reps_remain = rep - N_rd*reps_per_rd
        if reps_remain == 0 or N_rd == 0:
            display2 = ''
        else:
            display2 = ' + '
        for k in wod.keys():
            if reps_remain <= wod[k]:
                display2 = display2+str(reps_remain)+' '+re.sub('[0-9]$','',k)+', '
            else:
                display2 = display2+str(wod[k])+' '+re.sub('[0-9]$','',k)+', '
            reps_remain = reps_remain - wod[k]
            if reps_remain <= 0:
                break
        display = display1 + display2
    if tp == 'Other':
        display = f'{rep} {list(wod.keys())[0]}'
    display = re.sub('\,\s$', '', display)
    return display



f = 'C:\\Users\\yhli1\\OneDrive - Mowi ASA\\work_files\\CrossFit\\Scoreboard.xlsx'
f = 'C:\\Users\\Yuanhao.Li\\OneDrive - Mowi ASA\\work_files\\CrossFit\\Scoreboard.xlsx'
f = 'Scoreboard.xlsx'
option = st.selectbox('Select leaderboard', ('Male', 'Female'))
if option == 'Male':
    sht = 'ScoreM'
else:
    sht = 'ScoreF'
d, s = DoScoreBoard(f, sht, True)
st.table(d)