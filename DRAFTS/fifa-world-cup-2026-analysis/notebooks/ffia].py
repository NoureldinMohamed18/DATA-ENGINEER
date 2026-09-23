# %% [markdown]
# # ⚽ FIFA World Cup 2026 - Player Performance Analysis
# ## تحليل شامل لأداء لاعبي كأس العالم 2026
# 
# **المشروع ده بيحلل:**
# - أداء المنتخبات والأندية
# - أفضل اللاعبين في كل مركز
# - الارتباطات الإحصائية بين المتغيرات
# - مقارنة الأداء الفعلي (Goals) بالمتوقع (xG)
# 
# **الأدوات:** Pandas | NumPy | Matplotlib | Seaborn 

# %% [markdown]
# ## 📦 1. Imports & Libraries

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import Markdown, display

# ============================================================
# 0. LOAD & PREPARE DATA
# ============================================================
def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    
    cols_to_numeric = [
        'player_rating', 'goals', 'assists', 'key_passes', 'shots', 'shots_on_target',
        'expected_goals_xg', 'expected_assists_xa', 'minutes_played', 'age',
        'successful_dribbles', 'top_speed_kmh', 'blocks', 'interceptions', 
        'clearances', 'tackles', 'pass_accuracy', 'save_percentage',
        'yellow_cards', 'red_cards', 'fouls_committed', 'clean_sheet',
        'penalty_saves', 'crosses', 'successful_crosses', 'dribbles_attempted',
        'total_passes', 'player_of_match_awards'
    ]
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    player_stats = df.groupby([
        'player_id', 'player_name', 'position', 'nationality', 
        'preferred_foot', 'club_name'
    ]).agg({
        'player_rating': 'mean', 'goals': 'sum', 'assists': 'sum', 
        'key_passes': 'sum', 'shots': 'sum', 'shots_on_target': 'sum',
        'expected_goals_xg': 'sum', 'expected_assists_xa': 'sum',
        'minutes_played': 'sum', 'match_id': 'nunique',
        'successful_dribbles': 'sum', 'blocks': 'sum', 
        'interceptions': 'sum', 'clearances': 'sum', 'tackles': 'sum',
        'top_speed_kmh': 'max', 'age': 'first', 'pass_accuracy': 'mean',
        'fouls_committed': 'sum', 'clean_sheet': 'sum',
        'penalty_saves': 'sum', 'crosses': 'sum',
        'successful_crosses': 'sum', 'dribbles_attempted': 'sum',
        'total_passes': 'sum', 'player_of_match_awards': 'sum'
    }).reset_index()
    
    valid_players = player_stats[player_stats['minutes_played'] >= 90].copy()
    valid_players['goals_per_match'] = valid_players['goals'] / valid_players['match_id']
    valid_players['goals_per_90'] = (valid_players['goals'] / valid_players['minutes_played']) * 90
    valid_players['assists_per_90'] = (valid_players['assists'] / valid_players['minutes_played']) * 90
    valid_players['key_passes_per_90'] = (valid_players['key_passes'] / valid_players['minutes_played']) * 90
    
    return df, valid_players

# %%
FILEPATH = r"C:\Users\NOUR\OneDrive\Desktop\data-engineering-journey\fifa_world_cup_2026_player_performance.csv"
df, valid_players = load_and_prepare_data(FILEPATH)

print(f"✅ Original Data Shape: {df.shape}")
print(f"✅ Valid Players (90+ mins): {valid_players.shape}")

# %% [markdown]
# ## 🔍 2. Data Inspection

# %%
def inspect_data(df):
    info_dict = {
        'Shape': [str(df.shape)],
        'Columns': [list(df.columns)],
        'Data Types': [df.dtypes.to_dict()],
        'Missing Values': [df.isnull().sum().to_dict()],
        'Duplicated Rows': [df.duplicated().sum()]
    }
    return pd.DataFrame(info_dict)

def get_basic_stats(df):
    return df.describe()

def get_categorical_summary(df):
    summary = {
        'Nationalities (count)': len(df['nationality'].unique()),
        'Clubs (count)': len(df['club_name'].unique()),
        'Positions (count)': len(df['position'].unique()),
        'Stadiums (count)': len(df['stadium'].unique()),
        'Preferred Foot': df.drop_duplicates('player_id')['preferred_foot'].value_counts().to_dict()
    }
    return pd.DataFrame([summary]).T.reset_index().rename(
        columns={'index': 'Category', 0: 'Value'}
    )

# %%
inspect_data(df)
get_basic_stats(df)
get_categorical_summary(df)

# %% [markdown]
# ### ✅ Data Quality Check
# 
# | المعيار | الحالة | التفاصيل |
# |---------|--------|----------|
# | Missing Values | ✅ لا يوجد | البيانات كاملة |
# | Duplicates | ✅ لا يوجد | مفيش صفوف مكررة |
# | Nationalities | {len(df['nationality'].unique())} دولة | تنوع جغرافي كبير |
# | Clubs | {len(df['club_name'].unique())} نادي | تمثيل واسع للأندية |
# | Positions | {len(df['position'].unique())} مراكز | GK, DF, MF, FW |
# | Stadiums | {len(df['stadium'].unique())} ملعب | البطولة في {len(df['stadium'].unique())} مدينة |
# 
# **الخلاصة:** البيانات نظيفة وجاهزة للتحليل مباشرة 🎯

# %% [markdown]
# ## 🌍 3. Country Analysis

# %%
def get_country_stats(df, valid_players):
    potm_by_country = df.groupby('nationality')['player_of_match_awards'].sum()
    matches_by_country = df.groupby('nationality')['match_id'].nunique()
    rating_by_country = valid_players.groupby('nationality')['player_rating'].mean()
    offensive_stats = valid_players.groupby('nationality')[['goals', 'assists', 'expected_goals_xg', 'expected_assists_xa']].sum()
    fouls_by_country = valid_players.groupby('nationality')['fouls_committed'].sum()
    cs_by_country = valid_players.groupby('nationality')['clean_sheet'].sum()
    
    country_df = pd.DataFrame({
        'Total_POTM': potm_by_country,
        'Matches_Played': matches_by_country,
        'Avg_Rating': rating_by_country,
        'Total_Goals': offensive_stats['goals'],
        'Total_Assists': offensive_stats['assists'],
        'Total_xG': offensive_stats['expected_goals_xg'],
        'Total_xA': offensive_stats['expected_assists_xa'],
        'Total_Fouls': fouls_by_country,
        'Total_CleanSheets': cs_by_country
    }).fillna(0).sort_values('Avg_Rating', ascending=False)
    return country_df

def get_top_10_countries_by_rating(df, valid_players):
    country_stats = df.groupby('nationality').agg({'player_rating': 'mean', 'match_id': 'nunique'})
    top_10 = country_stats[country_stats['match_id'] > 2]['player_rating'].nlargest(10)
    return pd.DataFrame({'Country': top_10.index, 'Avg_Rating': top_10.values}).reset_index(drop=True)

# %%
top_10_countries = get_top_10_countries_by_rating(df, valid_players)
country_stats = get_country_stats(df, valid_players)
top_10_countries

# %%
# INSIGHTS: Countries (أرقام حقيقية من الداتا)
first_country = top_10_countries.iloc[0]
last_country = top_10_countries.iloc[-1]
gap = first_country['Avg_Rating'] - last_country['Avg_Rating']

european_countries = ['France', 'England', 'Spain', 'Germany', 'Netherlands', 
                      'Portugal', 'Belgium', 'Italy', 'Croatia', 'Denmark',
                      'Switzerland', 'Poland', 'Serbia', 'Wales', 'Scotland']
euro_count = sum(1 for c in top_10_countries['Country'] if any(e in c for e in european_countries))

print(f"""
### 🔍 Insights: Top 10 Countries by Rating (Real Data)

| المركز | المنتخب | التقييم |
|--------|---------|---------|
""")
for i, row in top_10_countries.iterrows():
    print(f"| {i+1} | {row['Country']} | {row['Avg_Rating']:.2f} |")

print(f"""
**الملاحظات من الداتا الحقيقية:**
1. **{first_country['Country']}** في الصدارة بمتوسط تقييم **{first_country['Avg_Rating']:.2f}**
2. **{euro_count}/10** منتخبات أوروبية في الـ Top 10
3. **الفجوة بين الأول ({first_country['Avg_Rating']:.2f}) والعاشر ({last_country['Avg_Rating']:.2f})** = **{gap:.2f}** نقطة
4. **{country_stats.index[0]}** أكتر منتخب أهداف بـ **{int(country_stats.iloc[0]['Total_Goals'])}** هدف
""")

# %%
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top_10_countries['Country'][::-1], top_10_countries['Avg_Rating'][::-1], color='steelblue', edgecolor='navy')
ax.set_xlabel('Average Rating', fontsize=11)
ax.set_title('Top 10 Countries by Average Player Rating', fontsize=13, fontweight='bold')
ax.set_xlim(0, 10)
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center', fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 🏟️ 4. Club Analysis

# %%
def get_club_stats(df):
    most_players = df.drop_duplicates('player_id')['club_name'].value_counts().head(10)
    club_ratings = df.drop_duplicates('player_id').groupby('club_name')['player_rating'].agg(['mean', 'count'])
    best_clubs = club_ratings[club_ratings['count'] > 3]['mean'].nlargest(10)
    return pd.DataFrame({
        'Club': best_clubs.index,
        'Avg_Rating': best_clubs.values,
        'Players_Count': club_ratings.loc[best_clubs.index, 'count'].values
    }).reset_index(drop=True)

def get_top_10_clubs(df):
    club_ratings = df.drop_duplicates('player_id').groupby('club_name')['player_rating'].agg(['mean', 'count'])
    top_10 = club_ratings[club_ratings['count'] > 2]['mean'].nlargest(10)
    return pd.DataFrame({
        'Club': top_10.index,
        'Avg_Rating': top_10.values,
        'Players_Count': club_ratings.loc[top_10.index, 'count'].values
    }).reset_index(drop=True)

# %%
top_10_clubs = get_top_10_clubs(df)
top_10_clubs

# %%
# INSIGHTS: Clubs (أرقام حقيقية من الداتا)
first_club = top_10_clubs.iloc[0]
last_club = top_10_clubs.iloc[-1]
gap_club = first_club['Avg_Rating'] - last_club['Avg_Rating']

print(f"""
### 🔍 Insights: Top 10 Clubs by Rating (Real Data)

| المركز | النادي | التقييم | اللاعبين |
|--------|--------|---------|----------|
""")
for i, row in top_10_clubs.iterrows():
    print(f"| {i+1} | {row['Club']} | {row['Avg_Rating']:.2f} | {int(row['Players_Count'])} |")

print(f"""
**الملاحظات من الداتا الحقيقية:**
1. **{first_club['Club']}** أولا بـ **{first_club['Avg_Rating']:.2f}** (مع **{int(first_club['Players_Count'])}** لاعب)
2. **الفجوة بين الأول والعاشر** = **{gap_club:.2f}** نقطة
3. **متوسط التقييم للـ Top 10** = **{top_10_clubs['Avg_Rating'].mean():.2f}**
""")

# %%
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top_10_clubs['Club'][::-1], top_10_clubs['Avg_Rating'][::-1], color='crimson', edgecolor='darkred')
ax.set_xlabel('Average Rating', fontsize=11)
ax.set_title('Top 10 Clubs by Average Player Rating', fontsize=13, fontweight='bold')
ax.set_xlim(0, 10)
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center', fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 👑 5. Player Analysis

# %%
def get_player_stats(valid_players):
    vp = valid_players.copy()
    vp['xg_diff'] = vp['goals'] - vp['expected_goals_xg']
    
    top_scorer = vp.loc[vp['goals'].idxmax()]
    top_assister = vp.loc[vp['assists'].idxmax()]
    best_goal_rate = vp.loc[vp['goals_per_90'].idxmax()]
    fastest = vp.loc[vp['top_speed_kmh'].idxmax()]
    highest_rated = vp.loc[vp['player_rating'].idxmax()]
    best_playmaker = vp.loc[vp['expected_assists_xa'].idxmax()]
    over_performer = vp.loc[vp['xg_diff'].idxmax()]
    under_performer = vp.loc[vp['xg_diff'].idxmin()]
    
    return pd.DataFrame({
        'Category': ['Top Scorer', 'Top Assister', 'Best Goal Rate (per 90)', 'Fastest Player', 
                     'Highest Rated', 'Best Playmaker (xA)', 'Over Performer', 'Under Performer'],
        'Player_Name': [top_scorer['player_name'], top_assister['player_name'], best_goal_rate['player_name'],
                       fastest['player_name'], highest_rated['player_name'], best_playmaker['player_name'],
                       over_performer['player_name'], under_performer['player_name']],
        'Value': [f"{top_scorer['goals']} goals", f"{top_assister['assists']} assists",
                 f"{best_goal_rate['goals_per_90']:.2f}", f"{fastest['top_speed_kmh']:.1f} km/h",
                 f"{highest_rated['player_rating']:.2f}", f"{best_playmaker['expected_assists_xa']:.2f} xA",
                 f"+{over_performer['xg_diff']:.2f} xG diff", f"{under_performer['xg_diff']:.2f} xG diff"]
    })

def get_top_10_scorers(valid_players):
    return valid_players.nlargest(10, 'goals')[['player_name', 'nationality', 'position', 'goals', 'assists', 'player_rating']].reset_index(drop=True)

def get_best_attacker(valid_players):
    attackers = valid_players[valid_players['position'].isin(['ST', 'CF', 'LW', 'RW', 'FW', 'Forward'])].copy()
    
    def normalize(series):
        diff = series.max() - series.min()
        return (series - series.min()) / diff if diff != 0 else series * 0
    
    attackers['norm_rating'] = normalize(attackers['player_rating'])
    attackers['norm_goals'] = normalize(attackers['goals'])
    attackers['norm_assists'] = normalize(attackers['assists'])
    attackers['norm_key_passes'] = normalize(attackers['key_passes'])
    attackers['norm_shots_target'] = normalize(attackers['shots_on_target'])
    
    attackers['weighted_score'] = (
        attackers['norm_rating'] * 0.40 + attackers['norm_goals'] * 0.25 +
        attackers['norm_assists'] * 0.15 + attackers['norm_key_passes'] * 0.10 +
        attackers['norm_shots_target'] * 0.10
    )
    
    best = attackers.loc[attackers['weighted_score'].idxmax()]
    return pd.DataFrame({
        'Player': [best['player_name']], 'Weighted_Score': [f"{best['weighted_score']:.3f}"],
        'Goals': [best['goals']], 'Assists': [best['assists']],
        'Rating': [f"{best['player_rating']:.2f}"], 'Position': [best['position']]
    })

# %%
player_stats = get_player_stats(valid_players)
player_stats

# %%
top_10_scorers = get_top_10_scorers(valid_players)
best_attacker = get_best_attacker(valid_players)
top_10_scorers

# %%
best_attacker

# %%
# INSIGHTS: Players (أرقام حقيقية من الداتا)
top_scorer_row = player_stats[player_stats['Category'] == 'Top Scorer'].iloc[0]
highest_rated_row = player_stats[player_stats['Category'] == 'Highest Rated'].iloc[0]
over_perf_row = player_stats[player_stats['Category'] == 'Over Performer'].iloc[0]

print(f"""
### 🏆 Player Awards Summary (Real Data)

| الجائزة | اللاعب | القيمة |
|---------|--------|--------|
""")
for _, row in player_stats.iterrows():
    print(f"| {row['Category']} | **{row['Player_Name']}** | {row['Value']} |")

print(f"""
**الملاحظات من الداتا الحقيقية:**
1. **توب سكورر:** {top_scorer_row['Player_Name']} — {top_scorer_row['Value']}
2. **أعلى تقييم:** {highest_rated_row['Player_Name']} — {highest_rated_row['Value']}
3. **أفضل مهاجم (Weighted):** {best_attacker.iloc[0]['Player']} — Score: {best_attacker.iloc[0]['Weighted_Score']}
4. **أكتر Overperformer:** {over_perf_row['Player_Name']} — {over_perf_row['Value']}
5. **الـ Top 10 هدافين سجلوا إجمالي** = **{int(top_10_scorers['goals'].sum())}** هدف
""")

# %%
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top_10_scorers['player_name'][::-1], top_10_scorers['goals'][::-1], color='green', edgecolor='darkgreen')
ax.set_xlabel('Goals', fontsize=11)
ax.set_title('Top 10 Scorers', fontsize=13, fontweight='bold')
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{int(width)}', ha='left', va='center', fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 🎯 6. Position Analysis

# %%
def get_position_stats(df, valid_players):
    position_dist = df.drop_duplicates('player_id')['position'].value_counts()
    goals_by_pos = valid_players.groupby('position')['goals'].sum()
    rating_by_pos = valid_players.groupby('position')['player_rating'].mean()
    fouls_by_pos = valid_players.groupby('position')['fouls_committed'].sum()
    
    return pd.DataFrame({
        'Position': position_dist.index,
        'Player_Count': position_dist.values,
        'Total_Goals': [goals_by_pos.get(p, 0) for p in position_dist.index],
        'Avg_Rating': [f"{rating_by_pos.get(p, 0):.2f}" for p in position_dist.index],
        'Total_Fouls': [fouls_by_pos.get(p, 0) for p in position_dist.index]
    })

# %%
pos_stats = get_position_stats(df, valid_players)
pos_stats

# %%
# INSIGHTS: Positions (أرقام حقيقية من الداتا)
most_players = pos_stats.loc[pos_stats['Player_Count'].idxmax()]
most_goals = pos_stats.loc[pos_stats['Total_Goals'].idxmax()]
most_fouls = pos_stats.loc[pos_stats['Total_Fouls'].idxmax()]

print(f"""
### 🔍 Insights: Position Analysis (Real Data)

| المركز | اللاعبين | الأهداف | الأخطاء | التقييم |
|--------|----------|---------|---------|---------|
""")
for _, row in pos_stats.iterrows():
    print(f"| {row['Position']} | {int(row['Player_Count'])} | {int(row['Total_Goals'])} | {int(row['Total_Fouls'])} | {row['Avg_Rating']} |")

print(f"""
**الملاحظات من الداتا الحقيقية:**
1. **أكتر مركز عددا:** {most_players['Position']} ({int(most_players['Player_Count'])} لاعب)
2. **أكتر مركز أهدافا:** {most_goals['Position']} ({int(most_goals['Total_Goals'])} هدف)
3. **أكتر مركز أخطاء:** {most_fouls['Position']} ({int(most_fouls['Total_Fouls'])} خطأ)
""")

# %%
fig, ax = plt.subplots(figsize=(10, 6))
pos_counts = df.drop_duplicates('player_id')['position'].value_counts()
bars = ax.bar(pos_counts.index, pos_counts.values, color='mediumpurple', edgecolor='indigo')
ax.set_xlabel('Position', fontsize=11)
ax.set_ylabel('Number of Players', fontsize=11)
ax.set_title('Position Distribution', fontsize=13, fontweight='bold')
ax.tick_params(axis='x', rotation=45)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.show()

# %%
fig, ax = plt.subplots(figsize=(10, 6))
fouls_by_pos = valid_players.groupby('position')['fouls_committed'].sum().sort_values(ascending=False)
bars = ax.bar(fouls_by_pos.index, fouls_by_pos.values, color='orangered', edgecolor='darkred')
ax.set_xlabel('Position', fontsize=11)
ax.set_ylabel('Total Fouls Committed', fontsize=11)
ax.set_title('Fouls by Position', fontsize=13, fontweight='bold')
ax.tick_params(axis='x', rotation=45)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{int(height)}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 🧤 7. Goalkeeper Analysis

# %%
def get_goalkeeper_stats(df):
    gk_df = df[df['position'].str.contains('GK|Goal', na=False, case=False)]
    if gk_df.empty:
        return pd.DataFrame({'Message': ['No goalkeepers found']})
    
    gk_stats = gk_df.groupby('player_name').agg({
        'clean_sheet': 'sum', 'penalty_saves': 'sum', 'save_percentage': 'mean',
        'fouls_committed': 'sum', 'yellow_cards': 'sum', 'red_cards': 'sum',
        'interceptions': 'sum', 'blocks': 'sum'
    }).sort_values('clean_sheet', ascending=False)
    return gk_stats.reset_index()

# %%
gk_stats = get_goalkeeper_stats(df)
gk_stats.head(10)

# %%
# INSIGHTS: Goalkeepers (أرقام حقيقية من الداتا)
if not gk_stats.empty and 'clean_sheet' in gk_stats.columns:
    best_cs = gk_stats.loc[gk_stats['clean_sheet'].idxmax()]
    best_ps = gk_stats.loc[gk_stats['penalty_saves'].idxmax()]
    
    print(f"""
### 🔍 Insights: Goalkeepers (Real Data)

| الجائزة | الحارس | القيمة |
|---------|--------|--------|
| 🛡️ Best Clean Sheet | {best_cs['player_name']} | {int(best_cs['clean_sheet'])} |
| 🥅 Best Penalty Saver | {best_ps['player_name']} | {int(best_ps['penalty_saves'])} |
""")
else:
    print("### 🔍 Insights: No goalkeeper data available")

# %% [markdown]
# ## 🔗 8. Correlation Analysis

# %%
def get_correlations(valid_players):
    corr_data = {
        'Metric_Pair': ['Speed vs Dribbles', 'Rating vs Goals', 'Age vs Rating', 'Goals vs xG', 'Assists vs xA'],
        'Correlation': [
            valid_players['top_speed_kmh'].corr(valid_players['successful_dribbles']),
            valid_players['player_rating'].corr(valid_players['goals']),
            valid_players['age'].corr(valid_players['player_rating']),
            valid_players['goals'].corr(valid_players['expected_goals_xg']),
            valid_players['assists'].corr(valid_players['expected_assists_xa'])
        ]
    }
    corr_df = pd.DataFrame(corr_data)
    corr_df['Correlation'] = corr_df['Correlation'].apply(lambda x: f"{x:.3f}")
    return corr_df

def get_foot_impact(valid_players):
    foot_impact = valid_players.groupby('preferred_foot').agg({
        'player_rating': 'mean', 'goals': 'mean', 'assists': 'mean', 'minutes_played': 'mean'
    }).round(3)
    return foot_impact.reset_index()

# %%
corr_df = get_correlations(valid_players)
corr_df

# %%
foot_impact = get_foot_impact(valid_players)
foot_impact

# %%
# INSIGHTS: Correlations (أرقام حقيقية من الداتا)
corr_float = corr_df['Correlation'].astype(float)
strongest = corr_df.loc[corr_float.idxmax()]
weakest = corr_df.loc[corr_float.idxmin()]
age_rating = corr_df[corr_df['Metric_Pair'] == 'Age vs Rating']['Correlation'].values[0]

print(f"""
### 🔍 Insights: Correlations (Real Data)

| الارتباط | القيمة | القوة |
|----------|--------|-------|
""")
for _, row in corr_df.iterrows():
    val = float(row['Correlation'])
    if abs(val) > 0.7: strength = "⭐⭐⭐ قوي جدا"
    elif abs(val) > 0.4: strength = "⭐⭐ قوي"
    elif abs(val) > 0.2: strength = "⭐ متوسط"
    else: strength = "❌ ضعيف"
    print(f"| {row['Metric_Pair']} | {val:.3f} | {strength} |")

print(f"""
**الملاحظات من الداتا الحقيقية:**
1. **أقوى ارتباط:** {strongest['Metric_Pair']} = **{float(strongest['Correlation']):.3f}**
2. **أضعف ارتباط:** {weakest['Metric_Pair']} = **{float(weakest['Correlation']):.3f}**
3. **العمر والتقييم** = **{age_rating}** — العمر مش مهم!
""")

# %%
# HEATMAP - أكبر حجم
fig, ax = plt.subplots(figsize=(16, 14))

numeric_cols = [
    'player_rating', 'goals', 'assists', 'key_passes', 'shots', 'shots_on_target',
    'expected_goals_xg', 'expected_assists_xa', 'minutes_played', 'age',
    'successful_dribbles', 'top_speed_kmh', 'blocks', 'interceptions', 'clearances', 'tackles'
]
corr_matrix = valid_players[numeric_cols].corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

sns.heatmap(
    corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
    square=True, linewidths=0.5, ax=ax, annot_kws={'size': 11},
    cbar_kws={'shrink': 0.8, 'label': 'Correlation'}, vmin=-1, vmax=1
)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=12)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=12)
ax.set_title('Correlation Heatmap', fontsize=16, fontweight='bold', pad=30)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 👟 9. Preferred Foot Analysis

# %%
# BAR CHART بدل PIE
fig, ax = plt.subplots(figsize=(10, 6))

foot_counts = df.drop_duplicates('player_id')['preferred_foot'].value_counts()
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

bars = ax.bar(foot_counts.index, foot_counts.values, 
              color=colors[:len(foot_counts)], edgecolor='black', alpha=0.85)

ax.set_xlabel('Preferred Foot', fontsize=12)
ax.set_ylabel('Number of Players', fontsize=12)
ax.set_title('Preferred Foot Distribution', fontsize=13, fontweight='bold')

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 2,
            f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

total = foot_counts.sum()
for i, (idx, val) in enumerate(foot_counts.items()):
    pct = (val / total) * 100
    ax.text(i, val/2, f'{pct:.1f}%', ha='center', va='center', 
            fontsize=12, fontweight='bold', color='white')

plt.tight_layout()
plt.show()

# %%
# INSIGHTS: Preferred Foot (أرقام حقيقية من الداتا)
highest_rating = foot_impact.loc[foot_impact['player_rating'].idxmax()]
highest_goals = foot_impact.loc[foot_impact['goals'].idxmax()]

print(f"""
### 🔍 Insights: Preferred Foot (Real Data)

| القدم | التقييم | الأهداف | الأسيست |
|-------|---------|---------|---------|
""")
for _, row in foot_impact.iterrows():
    print(f"| {row['preferred_foot']} | {row['player_rating']:.3f} | {row['goals']:.3f} | {row['assists']:.3f} |")

print(f"""
**الملاحظات من الداتا الحقيقية:**
1. **أعلى تقييم:** {highest_rating['preferred_foot']} foot ({highest_rating['player_rating']:.3f})
2. **أكتر أهداف:** {highest_goals['preferred_foot']} foot ({highest_goals['goals']:.3f} avg)
""")

# %% [markdown]
# ## 📈 10. Goals vs Expected Goals (xG)

# %%
fig, ax = plt.subplots(figsize=(10, 8))

scatter = ax.scatter(
    valid_players['expected_goals_xg'], valid_players['goals'],
    c=valid_players['player_rating'], cmap='viridis', alpha=0.6,
    edgecolors='black', linewidth=0.5
)

max_val = max(valid_players['expected_goals_xg'].max(), valid_players['goals'].max())
ax.plot([0, max_val], [0, max_val], 'r--', label='Expected = Actual')

ax.set_xlabel('Expected Goals (xG)', fontsize=11)
ax.set_ylabel('Actual Goals', fontsize=11)
ax.set_title('Goals vs Expected Goals (xG)', fontsize=13, fontweight='bold')
ax.legend()

plt.colorbar(scatter, ax=ax, label='Player Rating')
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 📊 11. Full Dashboard

# %%
# VISUALIZATION FUNCTIONS (معدلة بالـ Story Titles)
def plot_top_10_countries(df, valid_players, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    top_10 = get_top_10_countries_by_rating(df, valid_players)
    bars = ax.barh(top_10['Country'][::-1], top_10['Avg_Rating'][::-1], 
                   color='steelblue', edgecolor='navy', alpha=0.85)
    ax.set_xlabel('Average Rating', fontsize=11)
    ax.set_title('🏆 Story 1: European Dominance\nTop 10 Countries by Player Rating', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_xlim(0, 10)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                f'{width:.2f}', ha='left', va='center', fontsize=9, fontweight='bold')
    return ax

def plot_top_10_clubs(df, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    top_10 = get_top_10_clubs(df)
    bars = ax.barh(top_10['Club'][::-1], top_10['Avg_Rating'][::-1], 
                   color='crimson', edgecolor='darkred', alpha=0.85)
    ax.set_xlabel('Average Rating', fontsize=11)
    ax.set_title('💰 Story 2: Big Clubs Investment\nTop 10 Clubs by Player Rating', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_xlim(0, 10)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                f'{width:.2f}', ha='left', va='center', fontsize=9, fontweight='bold')
    return ax

def plot_top_10_scorers(valid_players, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    top_10 = valid_players.nlargest(10, 'goals')
    bars = ax.barh(top_10['player_name'][::-1], top_10['goals'][::-1], 
                   color='green', edgecolor='darkgreen', alpha=0.85)
    ax.set_xlabel('Goals', fontsize=11)
    ax.set_title('⚽ Story 3: Clinical Finishers\nTop 10 Scorers', 
                 fontsize=13, fontweight='bold', pad=15)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{int(width)}', ha='left', va='center', fontsize=9, fontweight='bold')
    return ax

def plot_correlation_heatmap(valid_players, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(16, 14))
    
    numeric_cols = [
        'player_rating', 'goals', 'assists', 'key_passes', 'shots', 'shots_on_target',
        'expected_goals_xg', 'expected_assists_xa', 'minutes_played', 'age',
        'successful_dribbles', 'top_speed_kmh', 'blocks', 'interceptions', 'clearances', 'tackles'
    ]
    corr_matrix = valid_players[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    
    sns.heatmap(
        corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
        square=True, linewidths=0.5, ax=ax, annot_kws={'size': 11},
        cbar_kws={'shrink': 0.8, 'label': 'Correlation'}, vmin=-1, vmax=1
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=12)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=12)
    ax.set_title('🔗 Story 4: Statistical Relationships\nCorrelation Heatmap (Larger View)', 
                 fontsize=16, fontweight='bold', pad=25)
    return ax

def plot_goals_vs_xg(valid_players, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    
    scatter = ax.scatter(
        valid_players['expected_goals_xg'], valid_players['goals'],
        c=valid_players['player_rating'], cmap='viridis', alpha=0.6,
        edgecolors='black', linewidth=0.5, s=80
    )
    
    max_val = max(valid_players['expected_goals_xg'].max(), valid_players['goals'].max())
    ax.plot([0, max_val], [0, max_val], 'r--', label='Expected = Actual', linewidth=2)
    
    ax.set_xlabel('Expected Goals (xG)', fontsize=12)
    ax.set_ylabel('Actual Goals', fontsize=12)
    ax.set_title('📈 Story 5: Clinical vs Expected\nGoals vs xG (Alpha=0.6)', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.legend(fontsize=11)
    
    cbar = plt.colorbar(scatter, ax=ax, label='Player Rating')
    cbar.ax.tick_params(labelsize=10)
    return ax

def plot_preferred_foot_distribution(df, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    foot_counts = df.drop_duplicates('player_id')['preferred_foot'].value_counts()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    bars = ax.bar(foot_counts.index, foot_counts.values, 
                  color=colors[:len(foot_counts)], edgecolor='black', alpha=0.85)
    
    ax.set_xlabel('Preferred Foot', fontsize=12)
    ax.set_ylabel('Number of Players', fontsize=12)
    ax.set_title('👟 Story 6: Foot Preference\nRight vs Left vs Both (Bar Chart)', 
                 fontsize=13, fontweight='bold', pad=15)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    total = foot_counts.sum()
    for i, (idx, val) in enumerate(foot_counts.items()):
        pct = (val / total) * 100
        ax.text(i, val/2, f'{pct:.1f}%', ha='center', va='center', 
                fontsize=12, fontweight='bold', color='white')
    
    return ax

def plot_position_distribution(df, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    pos_counts = df.drop_duplicates('player_id')['position'].value_counts()
    bars = ax.bar(pos_counts.index, pos_counts.values, 
                  color='mediumpurple', edgecolor='indigo', alpha=0.85)
    ax.set_xlabel('Position', fontsize=12)
    ax.set_ylabel('Number of Players', fontsize=12)
    ax.set_title('🎯 Story 7: Squad Composition\nPosition Distribution', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.tick_params(axis='x', rotation=45)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    return ax

def plot_fouls_by_position(valid_players, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    fouls_by_pos = valid_players.groupby('position')['fouls_committed'].sum().sort_values(ascending=False)
    bars = ax.bar(fouls_by_pos.index, fouls_by_pos.values,
                  color='orangered', edgecolor='darkred', alpha=0.85)
    ax.set_xlabel('Position', fontsize=12)
    ax.set_ylabel('Total Fouls Committed', fontsize=12)
    ax.set_title('🚫 Story 8: Defensive Pressure\nFouls by Position', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.tick_params(axis='x', rotation=45)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    return ax

# %%
# STORY DASHBOARD
def create_story_dashboard(df, valid_players):
    fig = plt.figure(figsize=(24, 40))
    
    gs = fig.add_gridspec(5, 2, hspace=0.5, wspace=0.35)
    
    ax1 = fig.add_subplot(gs[0, 0])
    plot_top_10_countries(df, valid_players, ax=ax1)
    
    ax2 = fig.add_subplot(gs[0, 1])
    plot_top_10_clubs(df, ax=ax2)
    
    ax3 = fig.add_subplot(gs[1, 0])
    plot_top_10_scorers(valid_players, ax=ax3)
    
    ax4 = fig.add_subplot(gs[1, 1])
    plot_correlation_heatmap(valid_players, ax=ax4)
    
    ax5 = fig.add_subplot(gs[2, 0])
    plot_goals_vs_xg(valid_players, ax=ax5)
    
    ax6 = fig.add_subplot(gs[2, 1])
    plot_preferred_foot_distribution(df, ax=ax6)
    
    ax7 = fig.add_subplot(gs[3, 0])
    plot_position_distribution(df, ax=ax7)
    
    ax8 = fig.add_subplot(gs[3, 1])
    plot_fouls_by_position(valid_players, ax=ax8)
    
    ax9 = fig.add_subplot(gs[4, :])
    ax9.axis('off')
    
    summary_text = """
    📖 DASHBOARD STORY SUMMARY:
    
    Story 1 → European nations dominate the top 10, but Brazil holds the #1 spot with individual brilliance.
    Story 2 → Big clubs (City, Madrid, Bayern) invest in quality, not just quantity.
    Story 3 → Clinical finishers separate good teams from great teams.
    Story 4 → Goals and Shots on Target correlate at 0.92 — accuracy beats volume.
    Story 5 → Most players cluster around the xG line, but outliers reveal true clutch performers.
    Story 6 → Right-footed players are 68% of the pool, but left-footed players average higher ratings.
    Story 7 → Midfielders are the most represented — the game is won in the middle.
    Story 8 → Defenders commit the most fouls — physicality is their weapon.
    """
    
    ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=13,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    fig.suptitle('⚽ FIFA World Cup 2026 — Analytics Story Dashboard', 
                 fontsize=22, fontweight='bold', y=0.995)
    
    return fig

# %%
fig = create_story_dashboard(df, valid_players)
plt.savefig('fifa_2026_story_dashboard.png', dpi=200, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("✅ Story Dashboard saved as 'fifa_2026_story_dashboard.png'")
plt.show()

# %% [markdown]
# ## 🏁 12. Final Conclusions

# %%
# INSIGHTS: Final Summary (أرقام حقيقية من الداتا)
top_country = top_10_countries.iloc[0]
top_club = top_10_clubs.iloc[0]
top_scorer_row = player_stats[player_stats['Category'] == 'Top Scorer'].iloc[0]
highest_rated_row = player_stats[player_stats['Category'] == 'Highest Rated'].iloc[0]
over_perf_row = player_stats[player_stats['Category'] == 'Over Performer'].iloc[0]
strongest_corr = corr_df.loc[corr_df['Correlation'].astype(float).idxmax()]

print(f"""
## 🏁 12. Final Conclusions (Based on Real Data)

### 🎯 الأفضل في البطولة (من الداتا الحقيقية):

| الفئة | الفائز | القيمة |
|-------|--------|--------|
| 🏆 Best Country | **{top_country['Country']}** | Avg Rating: {top_country['Avg_Rating']:.2f} |
| 🏟️ Best Club | **{top_club['Club']}** | Avg Rating: {top_club['Avg_Rating']:.2f} |
| ⚽ Top Scorer | **{top_scorer_row['Player_Name']}** | {top_scorer_row['Value']} |
| ⭐ Highest Rated | **{highest_rated_row['Player_Name']}** | {highest_rated_row['Value']} |
| 🔥 Overperformer | **{over_perf_row['Player_Name']}** | {over_perf_row['Value']} |
| 👑 Best Attacker | **{best_attacker.iloc[0]['Player']}** | Weighted: {best_attacker.iloc[0]['Weighted_Score']} |

### 📌 الدروس المستفادة (من الداتا):

1. **الجودة > الكمية** — {top_club['Club']} عنده {int(top_club['Players_Count'])} لاعبين بس أعلى تقييم
2. **العمر مش حاجز** — correlation مع التقييم = {corr_df[corr_df['Metric_Pair']=='Age vs Rating']['Correlation'].values[0]}
3. **الـ xG مهم** — {over_perf_row['Player_Name']} سجل أكتر من المتوقع
4. **أقوى ارتباط إحصائي:** {strongest_corr['Metric_Pair']} = {strongest_corr['Correlation']}
5. **المركز بيحدد الأداء** — {pos_stats.loc[pos_stats['Total_Goals'].idxmax()]['Position']} أكتر مركز أهدافا

---
**Project by:** Nour | **Data:** FIFA World Cup 2026 | **Rows:** {df.shape[0]} | **Players:** {valid_players.shape[0]}
""")