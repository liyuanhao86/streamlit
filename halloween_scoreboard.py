import pandas as pd
import numpy as np
import re
import math
import streamlit as st
from PIL import Image
import base64

def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )
def DoScoreBoardF(file, sheet, ifQF=False):
	wod=[{},{},{},{},{}]
	wod[0] = {
		'Reps':1
	}
	wod[1] = {
		'Reps':1
	}
	wod[2] = {
		'reps':1
	}
	wod[3] = {
		'reps':1,
	}
	wod[4] = {
		'kg':1
	}
	wod_type = {1:'OtherFT',2:'Other',3:'FT',4:'FT',5:'Other'}
	wod_rd = {1:1,2:1,3:3,4:1,5:1}
	
	df = pd.read_excel(file, index_col=0, sheet_name = sheet).set_index(['Team'])
	score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
	score_matrix['points'][0]=0
	df = df.fillna(0)
				
	NWorkout = int(re.search(r"(?<=[A-z])[0-9]+$", df.columns[-1]).group(0))
	
	if sheet in ['FM', 'FF']:
		for w in range(1,2):
			df[f'WODdisplay{w}'] = ''
			for team in df.index:
				m = int(df[f'Minute{w}'][team])
				s = int(df[f'Second{w}'][team])
				r = int(df[f'Rep{w}'][team])
				if r == 490:
					df.loc[team,f'WODdisplay{w}'] = f'{m:02d}:{s:02d}'
				elif r<= 150:
					tmp = r
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} DUs (buy-in)'
				elif r<= 210:
					tmp = r-150
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} toes-to-bars'
				elif r<= 230:
					tmp = r-210
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} sync thrusters'
				elif r<= 270:
					tmp = r-230
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} CTB pull-ups'
				elif r<= 290:
					tmp = r-270
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} sync burpees'
				elif r<= 310:
					tmp = r-290
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} bar muscle-ups'
				elif r<= 330:
					tmp = r-310
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} sync OH squats'
				elif r<480:
					tmp = r-330
					df.loc[team,f'WODdisplay{w}'] = f'{r} reps: {tmp} DUs (buy-out)'
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
	scoreboard = df[['rank1']+ss]
	TB = df[ss2].min(axis = 1)
	TB.name = "WorstRound"
	TB2 = df[ss2].max(axis = 1)
	TB2.name = "BestRound"
	scoreboard = scoreboard.merge(TB, how='left', left_index=True, right_index=True)
	scoreboard = scoreboard.merge(TB2, how='left', left_index=True, right_index=True)
	scoreboard['PointsWithTB'] = scoreboard['TotalPoints']+0.00*scoreboard['WorstRound']+0.0000*scoreboard['BestRound']
	TotalRank = scoreboard['TotalPoints'].rank(axis=0, method='min', ascending=False)
	TotalRank.name = "TotalRank"
	TotalRankTB = scoreboard['PointsWithTB'].rank(axis=0, method='min', ascending=False)
	TotalRankTB.name = "TotalRankTB"
	scoreboard = scoreboard.merge(TotalRank, how='left', left_index=True, right_index=True)
	scoreboard = scoreboard.merge(TotalRankTB, how='left', left_index=True, right_index=True)
	display = scoreboard[['TotalRankTB']+['QualifyPoints']+['rank1']+ss2+['TotalPoints']+['WODdisplay1']+['WorstRound']+['BestRound']]
	display = display.sort_values(by=['TotalRankTB'])
	display.columns = ['Rank']+['Qualify']+['rank1']+ss3+['Total']+['WODdisplay1']+['WorstRound']+['BestRound']
	display = display.rename(columns={'WODdisplay1': 'Result', 'Workout 1': 'Final Pts', 'rank1': 'Final Rank'})
	display['Rank'] = display['Rank'].astype(int)
	display['Final Rank'] = display['Final Rank'].astype(int)
	scoreboard['Rank'] = display['Rank'].astype(int)
	woddis = scoreboard[ss4+ss2]
	if ifQF:
		return display, scoreboard, woddis
	else:
		return display.drop(columns=['Qualify']), scoreboard, woddis

def DoScoreBoardSF(file, sheet, ifQF=False):
	wod=[{},{},{},{},{}]
	wod[0] = {
		'Reps':1
	}
	wod[1] = {
		'Reps':1
	}
	wod[2] = {
		'reps':1
	}
	wod[3] = {
		'reps':1,
	}
	wod[4] = {
		'kg':1
	}
	wod_type = {1:'OtherFT',2:'Other',3:'FT',4:'FT',5:'Other'}
	wod_rd = {1:1,2:1,3:3,4:1,5:1}
	
	df = pd.read_excel(file, index_col=0, sheet_name = sheet).set_index(['Team'])
	score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
	score_matrix['points'][0]=0
	df = df.fillna(0)
				
	NWorkout = int(re.search(r"(?<=[A-z])[0-9]+$", df.columns[-1]).group(0))
	
	if sheet in ['SFM', 'SFF']:
		for w in range(1,2):
			df[f'WODdisplay{w}'] = ''
			for team in df.index:
				m = df[f'Minute{w}'][team]
				s = df[f'Second{w}'][team]
				r = df[f'Rep{w}'][team]
				cj = df['CJ'][team]
				snatch = df['Snatch'][team]
				total = cj + snatch
				df.loc[team,f'WODdisplay{w}']= f'Snatch {snatch} + C&J {cj} = {total}kg'

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
	scoreboard = df[['rank1']+ss]
	TB = df[ss2].min(axis = 1)
	TB.name = "WorstRound"
	TB2 = df[ss2].max(axis = 1)
	TB2.name = "BestRound"
	scoreboard = scoreboard.merge(TB, how='left', left_index=True, right_index=True)
	scoreboard = scoreboard.merge(TB2, how='left', left_index=True, right_index=True)
	scoreboard['PointsWithTB'] = scoreboard['TotalPoints']+0.00*scoreboard['WorstRound']+0.0000*scoreboard['BestRound']
	TotalRank = scoreboard['TotalPoints'].rank(axis=0, method='min', ascending=False)
	TotalRank.name = "TotalRank"
	TotalRankTB = scoreboard['PointsWithTB'].rank(axis=0, method='min', ascending=False)
	TotalRankTB.name = "TotalRankTB"
	scoreboard = scoreboard.merge(TotalRank, how='left', left_index=True, right_index=True)
	scoreboard = scoreboard.merge(TotalRankTB, how='left', left_index=True, right_index=True)
	display = scoreboard[['TotalRankTB']+['QualifyPoints']+['rank1']+ss2+['TotalPoints']+['WODdisplay1']+['WorstRound']+['BestRound']]
	display = display.sort_values(by=['TotalRankTB'])
	display.columns = ['Rank']+['Qualify']+['rank1']+ss3+['Total']+['WODdisplay1']+['WorstRound']+['BestRound']
	display = display.rename(columns={'WODdisplay1': 'Result', 'Workout 1': 'SF Pts', 'rank1': 'SF Rank'})
	display['Rank'] = display['Rank'].astype(int)
	display['SF Rank'] = display['SF Rank'].astype(int)
	scoreboard['Rank'] = display['Rank'].astype(int)
	woddis = scoreboard[ss4+ss2]
	if ifQF:
		return display, scoreboard, woddis
	else:
		return display.drop(columns=['Qualify']), scoreboard, woddis


def DoScoreBoard(file, sheet, ifQF=False):
	wod=[{},{},{},{},{}]
	wod[0] = {
		'Reps':1
	}
	wod[1] = {
		'Reps':1
	}
	wod[2] = {
		'reps':1
	}
	wod[3] = {
		'reps':1,
	}
	wod[4] = {
		'kg':1
	}
	wod_type = {1:'OtherFT',2:'Other',3:'FT',4:'FT',5:'Other'}
	wod_rd = {1:1,2:1,3:3,4:1,5:1}
	
	df = pd.read_excel(file, index_col=0, sheet_name = sheet).set_index(['Team'])
	score_matrix = pd.read_excel(file, index_col=0, sheet_name = 'ScoreMatrix').to_dict()
	score_matrix['points'][0]=0
	df = df.fillna(0)
				
	NWorkout = int(re.search(r"(?<=[A-z])[0-9]+$", df.columns[-1]).group(0))
	
	if sheet in ['ScoreM', 'ScoreF']:
		for w in range(1,NWorkout+1):
			df[f'WODdisplay{w}'] = ''
			if w ==1:
				for team in df.index:
					m = df[f'Minute{w}'][team]
					s = df[f'Second{w}'][team]
					r = df[f'Rep{w}'][team]
					df.loc[team,f'WODdisplay{w}']=get_wod_display(wod[w-1], m, s, r, wod_type[w], total_rd=wod_rd[w])
			if w == 2:
				for team in df.index:
					wb = df['WB'][team]
					bjo = df['BJO'][team]
					t2b = df['TTR'][team]
					ski = df['Ski'][team]
					df.loc[team,f'WODdisplay{w}'] = f'{wb} WB, {bjo} BJO, {t2b} T2R, {ski} Cals row'
			if w == 3:
				for team in df.index:
					m = int(df[f'Minute{w}'][team])
					s = int(df[f'Second{w}'][team])
					r = int(df[f'Rep{w}'][team])
					if r == 156:
						df.loc[team,f'WODdisplay{w}'] = f'{m:02d}:{s:02d}'
					elif r<= 16:
						tmp = r*2.5
						df.loc[team,f'WODdisplay{w}'] = f'{tmp}m farmer carry lunges'
					elif r<= 24:
						tmp = (r-16)*2.5
						df.loc[team,f'WODdisplay{w}'] = f'{tmp}m partner wheelbarrow'
					elif r<= 40:
						tmp = (r-24)*2.5
						df.loc[team,f'WODdisplay{w}'] = f'{tmp}m front-rack lunges'
					elif r<= 120:
						tmp = (r-40)
						df.loc[team,f'WODdisplay{w}'] = f'{tmp} crossover single unders'
					elif r<= 136:
						tmp = (r-120)*2.5
						df.loc[team,f'WODdisplay{w}'] = f'{tmp}m DB overhead lunges'
					elif r< 156:
						tmp = (r-136)
						df.loc[team,f'WODdisplay{w}'] = f'{tmp}m handstand walk'
	if sheet in ['SFM', 'SFF']:
		for w in range(1,3):
			df[f'WODdisplay{w}'] = ''
			for team in df.index:
				m = df[f'Minute{w}'][team]
				s = df[f'Second{w}'][team]
				r = df[f'Rep{w}'][team]
				df.loc[team,f'WODdisplay{w}']=get_wod_display(wod[w+2], m, s, r, wod_type[w], total_rd=wod_rd[w])

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
	scoreboard['PointsWithTB'] = scoreboard['TotalPoints']+0.00*scoreboard['WorstRound']+0.0000*scoreboard['BestRound']
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

def get_wod_display(wod, mm, ss, rep, tp, total_rd = 1, appendix = pd.DataFrame()):
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
	if tp == 'OtherFT':
		total_rep = 224
		if rep == total_rep:
			display = f'{mm:02d}:{ss:02d}'
		else:
			display = f'{rep} reps'
	display = re.sub('\,\s$', '', display)
	return display

bg_pic = 'halloweenwp.png'
add_bg_from_local(bg_pic)    
image = Image.open('CFBLogo.jpg')
image2 = Image.open('halloween.png')

file = 'Scoreboard.xlsx'

headers = {
    "selector": "th:not(.index_name)",
    "props": "background-color:#F9B233 ; color:#000080; font-weight:bold"
}
text = {
    'color': '#000080',
    'background-color':'#F9B233'
}

#st.set_page_config(layout="wide")
st.title("CrossFit Bryggen Halloween Games 2023")

st.image(image,width=100)

ifSemiFinal = True
ifFinal = True
if ifSemiFinal and ifFinal:
	option = st.selectbox(
		'Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage', 'Female Semi-Final', 'Male Semi-Final', 'Female Final', 'Male Final', 'Workout 1', 'Workout 2', 'Workout 3')
	)
elif ifSemiFinal:
	option = st.selectbox(
		'Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage', 'Female Semi-Final', 'Male Semi-Final', 'Workout 1', 'Workout 2', 'Workout 3')
	)
else:
	option = st.selectbox(
		'Select leaderboard from the dropdown menu', ('Female First Stage', 'Male First Stage', 'Workout 1', 'Workout 2', 'Workout 3')
	)

if option == 'Male First Stage':
	sheet = 'ScoreM'
	try:
		d, s, w = DoScoreBoard(file, sheet, False)
		st.subheader("Leaderboard")
		st.table(d.drop(columns=['WorstRound','BestRound']).style.set_table_styles([headers]).set_properties(**text))
	except:
		df = pd.read_excel(file, index_col=0, sheet_name = sheet)
		st.text(f'Scoreboard is not available yet')
		st.table(df[['Team']].style.set_table_styles([headers]).set_properties(**text))
elif option == 'Female First Stage':
	try:
		sheet = 'ScoreF'
		d, s, w = DoScoreBoard(file, sheet, False)
		st.subheader("Leaderboard")
		st.table(d.drop(columns=['WorstRound','BestRound']).style.set_table_styles([headers]).set_properties(**text))
	except:
		df = pd.read_excel(file, index_col=0, sheet_name = sheet)
		st.text(f'Scoreboard is not available yet')
		st.table(df[['Team']].style.set_table_styles([headers]).set_properties(**text))
elif option == 'Male Semi-Final':
	sheet = 'SFM'
	try:
		d, s, w = DoScoreBoardSF(file, sheet, True)
		st.subheader("Leaderboard")
		st.table(d.drop(columns=['WorstRound','BestRound']).style.set_table_styles([headers]).set_properties(**text))
	except:
		df = pd.read_excel(file, index_col=0, sheet_name = sheet)
		st.text(f'Scoreboard is not available yet')
elif option == 'Female Semi-Final':
	try:
		sheet = 'SFF'
		d, s, w = DoScoreBoardSF(file, sheet, True)
		st.subheader("Leaderboard")
		st.table(d.drop(columns=['WorstRound','BestRound']).style.set_table_styles([headers]).set_properties(**text))
	except:
		df = pd.read_excel(file, index_col=0, sheet_name = sheet)
		st.text(f'Scoreboard is not available yet')
elif option == 'Male Final':
	sheet = 'FM'
	try:
		d, s, w = DoScoreBoardF(file, sheet, True)
		st.subheader("Leaderboard")
		st.table(d.drop(columns=['WorstRound','BestRound']).style.set_table_styles([headers]).set_properties(**text))
	except:
		df = pd.read_excel(file, index_col=0, sheet_name = sheet)
		st.text(f'Scoreboard is not available yet')
elif option == 'Female Final':
	try:
		sheet = 'FF'
		d, s, w = DoScoreBoardF(file, sheet, True)
		st.subheader("Leaderboard")
		st.table(d.drop(columns=['WorstRound','BestRound']).style.set_table_styles([headers]).set_properties(**text))
	except:
		df = pd.read_excel(file, index_col=0, sheet_name = sheet)
		st.text(f'Scoreboard is not available yet')
elif option in ['Workout 1', 'Workout 2', 'Workout 3']:
	nwod = re.search('[0-9]$', option).group(0)
	try:
		sheet = 'ScoreF'
		d, s, w = DoScoreBoard(file, sheet, True)
		w = w.sort_values(by=[f'points{nwod}'], ascending=False)
		w['CurrentRank'] = w[f'points{nwod}'].rank(axis=0, method='min', ascending=False)
		dis_w = w[['CurrentRank', f'WODdisplay{nwod}']]
		dis_w.columns = ['Rank', option]
		dis_w['Rank'] = dis_w['Rank'].astype(int)
		st.subheader('Female Division ' + option)
		st.table(dis_w.style.set_table_styles([headers]).set_properties(**text))
	except:
		st.text(f'Scoreboard for female division {option} is not available yet')
	try:
		sheet = 'ScoreM'
		d, s, w = DoScoreBoard(file, sheet, True)
		w = w.sort_values(by=[f'points{nwod}'], ascending=False)
		w['CurrentRank'] = w[f'points{nwod}'].rank(axis=0, method='min', ascending=False)
		dis_w = w[['CurrentRank', f'WODdisplay{nwod}']]
		dis_w.columns = ['Rank', option]
		dis_w['Rank'] = dis_w['Rank'].astype(int)
		st.subheader('Male Division ' + option)
		st.table(dis_w.style.set_table_styles([headers]).set_properties(**text))
	except:
		st.text(f'Scoreboard for male division {option} is not available yet')

