import pandas as pd
# ========== SERIES ==========
# Series = عمود واحد من البيانات
s = pd.Series([10, 20, 30, 40], index=['a', 'b', 'c', 'd'])
print(s)
# a    10
# b    20
# c    30
# d    40
# ========== DATAFRAME ==========
# DataFrame = جدول كامل (مجموعة Series)
data = {
    'Name': ['Ali', 'Sara', 'Mohamed'],
    'Age': [25, 30, 35],
    'City': ['Cairo', 'Alex', 'Giza'],
    'Salary': [5000, 7000, 9000]
}
df = pd.DataFrame(data)
print(df)

# ========== القراءة ==========
df_csv = pd.read_csv("data.csv")           # CSV
df_excel = pd.read_excel("data.xlsx")      # Excel
df_json = pd.read_json("data.json")        # JSON
df_sql = pd.read_sql("SELECT * FROM users", connection)  # SQL

# ========== الكتابة ==========
df.to_csv("output.csv", index=False)       # index=False عشان ما يكتبش رقم الصف
df.to_excel("output.xlsx", index=False)
df.to_json("output.json")
df.to_sql("table_name", connection, if_exists='replace')
# أول 5 صفوف
df.head(10)        # أول 10 صفوف
df.tail(5)         # آخر 5 صفوف
# معلومات عن البيانات
df.info()          # أنواع البيانات، عدد القيم الفارغة، استخدام الذاكرة
df.describe()      # إحصائيات للأعمدة الرقمية (count, mean, std, min, max, quartiles)
df.shape           # (عدد_الصفوف, عدد_الأعمدة)
df.columns         # أسماء الأعمدة
df.dtypes          # أنواع البيانات لكل عمود
# عدد القيم الفريدة
df['City'].value_counts()
# إحصائيات سريعة
df['Salary'].sum()
df['Salary'].mean()
df['Salary'].median()
# ========= اختيار أعمدة ==========
names = df['Name']              # Series واحد
subset = df[['Name', 'Salary']]  # DataFrame متعدد الأعمدة
# ========== loc (Label-based) ==========
# loc[row_labels, column_labels]
df.loc[0]                       # الصف الأول
df.loc[0:2, ['Name', 'City']]   # صفوف 0-2، أعمدة Name و City
df.loc[df['Age'] > 30]          # كل الصفوف اللي العمر > 30
# ========== iloc (Position-based) ==========
# iloc[row_positions, column_positions]
df.iloc[0]                      # الصف الأول
df.iloc[0:3, 0:2]               # 3 صفوف، أول عمودين
df.iloc[-1]                     # آخر صف
# ========== Boolean Filtering ==========
# AND (&), OR (|), NOT (~)
it_employees = df[(df['Department'] == 'IT') & (df['Salary'] > 5000)]
high_earners = df[df['Salary'] > df['Salary'].mean()]
# إضافة عمود جديد
df['Bonus'] = df['Salary'] * 0.1
df['Full_Name'] = df['First_Name'] + ' ' + df['Last_Name']
# تعديل عمود موجود
df['Age'] = df['Age'] + 1
df['Salary'] = df['Salary'].apply(lambda x: x * 1.05)  # زيادة 5%
# حذف عمود
df = df.drop('City', axis=1)        # axis=1 = عمود
df = df.drop(columns=['City', 'Age'])
# إعادة تسمية أعمدة
df = df.rename(columns={'old_name': 'new_name'})
# Sorting
df_sorted = df.sort_values('Age', ascending=False)
df_sorted = df.sort_values(['Department', 'Salary'], ascending=[True, False])
# اكتشاف القيم الفارغة
df.isnull()              # True/False لكل خلية
df.isnull().sum()        # عدد القيم الفارغة في كل عمود
df.isnull().sum() / len(df) * 100  # نسبة القيم الفارغة
# ملء القيم الفارغة
df['Age'] = df['Age'].fillna(df['Age'].mean())   # بـ المتوسط
df['City'] = df['City'].fillna('Unknown')        # بـ قيمة ثابتة
df['Salary'] = df['Salary'].fillna(method='ffill')  # forward fill (آخر قيمة صحيحة)
df['Salary'] = df['Salary'].fillna(method='bfill')  # backward fill
# حذف الصفوف/الأعمدة الفارغة
df_clean = df.dropna()                    # حذف أي صف فيه قيمة فارغة
df_clean = df.dropna(subset=['Salary'])   # حذف الصفوف الفارغة في عمود معين
df_clean = df.dropna(axis=1)             # حذف الأعمدة الفارغة
# ========== GroupBy ==========
# Split → Apply → Combine
# متوسط الراتب لكل قسم
dept_avg = df.groupby('Department')['Salary'].mean()
# أكثر من aggregation
dept_stats = df.groupby('Department').agg({
    'Salary': ['mean', 'min', 'max', 'count'],
    'Age': ['mean', 'std']
})
# GroupBy متعدد
multi_group = df.groupby(['Department', 'City'])['Salary'].sum()
# Transform (يحافظ على نفس الشكل)
df['Dept_Avg'] = df.groupby('Department')['Salary'].transform('mean')
df['Salary_Diff'] = df['Salary'] - df['Dept_Avg']
# Apply (دوال مخصصة)
def normalize(group):
    return (group - group.mean()) / group.std()
df['Normalized_Salary'] = df.groupby('Department')['Salary'].transform(normalize)
# ========== Concatenation ==========
# دمج DataFrames فوق بعض (rows) أو جنب بعض (columns)
df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
df2 = pd.DataFrame({'A': [5, 6], 'B': [7, 8]})
# دمج رأسي (rows) - default
combined = pd.concat([df1, df2], axis=0)
#     A  B
# 0   1  3
# 1   2  4
# 0   5  7   ← index متكرر!
# 1   6  8
# إعادة index
combined = pd.concat([df1, df2], ignore_index=True)
# MultiIndex (للتمييز بين المصادر)
combined = pd.concat([df1, df2], keys=['source1', 'source2'])
# دمج أفقي (columns)
df3 = pd.DataFrame({'C': [9, 10]})
combined_h = pd.concat([df1, df3], axis=1)
# ========== Merge ==========
# SQL JOINs في Pandas!
employees = pd.DataFrame({
    'emp_id': [1, 2, 3, 4],
    'name': ['Ali', 'Sara', 'Mohamed', 'Fatma'],
    'dept_id': [101, 102, 101, 103]
})
departments = pd.DataFrame({
    'dept_id': [101, 102, 104],
    'dept_name': ['IT', 'HR', 'Finance']
})
# INNER JOIN (default) - القيم المشتركة فقط
inner = pd.merge(employees, departments, on='dept_id')
# emp_id  name     dept_id  dept_name
# 1       Ali      101      IT
# 2       Sara     102      HR
# 3       Mohamed  101      IT
# LEFT JOIN - كل البيانات من اليسار + المتطابقة من اليمين
left = pd.merge(employees, departments, on='dept_id', how='left')
# Fatma هتظهر مع dept_name = NaN
# RIGHT JOIN
right = pd.merge(employees, departments, on='dept_id', how='right')
# OUTER JOIN - كل البيانات من الجانبين
outer = pd.merge(employees, departments, on='dept_id', how='outer')
# ========== Merge بأسماء أعمدة مختلفة ==========
# left_on و right_on
merged = pd.merge(df1, df2, left_on='user_id', right_on='id')
# Merge بالـ index
merged = pd.merge(df1, df2, left_index=True, right_index=True)
# Suffixes (لما يكون فيه أعمدة بنفس الاسم)
merged = pd.merge(df1, df2, on='id', suffixes=('_left', '_right'))
# ========== Pivot Table ==========
# مثل Excel Pivot Tables!
data = {
    'Date': ['2024-01', '2024-01', '2024-02', '2024-02'],
    'Product': ['A', 'B', 'A', 'B'],
    'Region': ['North', 'North', 'South', 'South'],
    'Sales': [100, 150, 200, 250]
}
df = pd.DataFrame(data)
# Pivot Table أساسي
pivot = df.pivot_table(
    values='Sales',           # القيم
    index='Product',          # الصفوف
    columns='Region',         # الأعمدة
    aggfunc='sum'             # دالة التجميع
)
# Region   North  South
# Product
# A        100    200
# B        150    250
# Pivot Table متقدم
pivot = df.pivot_table(
    values='Sales',
    index=['Product', 'Date'],
    columns='Region',
    aggfunc=['sum', 'mean', 'count'],
    fill_value=0,
    margins=True              # إجمالي الصفوف والأعمدة
)
# ========== التعامل مع التواريخ ==========
# تحويل string لـ datetime
df['Date'] = pd.to_datetime(df['Date'])
# إنشاء date range
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
# freq: 'D' (يومي), 'W' (أسبوعي), 'M' (شهري), 'H' (ساعي)
# Indexing بالوقت
df.set_index('Date', inplace=True)
# اختيار فترة زمنية
jan_data = df['2024-01']           # كل يناير
q1_data = df['2024-01':'2024-03']  # الربع الأول
# Resampling (تغيير التردد)
daily = df.resample('D').mean()    # يومي
monthly = df.resample('M').sum()   # شهري
weekly = df.resample('W').agg({'Sales': 'sum', 'Orders': 'count'})
# Shifting (التأخير)
df['Sales_Prev_Month'] = df['Sales'].shift(1)  # قيمة الشهر اللي فات
# Rolling Window (المتوسط المتحرك)
df['MA_7'] = df['Sales'].rolling(window=7).mean()
df['MA_30'] = df['Sales'].rolling(window=30).mean()