# ⚽ FIFA World Cup 2026 - Player Performance Analysis

## 📋 Overview
تحليل شامل لأداء لاعبي كأس العالم 2026 باستخدام Python و Pandas و Matplotlib/Seaborn.

## 🎯 Objectives
- تحليل أداء المنتخبات والأندية واللاعبين
- اكتشاف الأنماط والارتباطات الإحصائية
- تحديد أفضل اللاعبين في كل مركز
- مقارنة الأداء الفعلي (Goals) بالمتوقع (xG)

## 📁 Project Structure
fifa-world-cup-2026-analysis/
├── 📓 fifa_analysis.ipynb          # Notebook الرئيسي
├── 📊 fifa_2026_dashboard.png      # Dashboard الشامل
├── 📄 README.md                     # ده الملف
├── 📝 requirements.txt              # المكتبات المطلوبة
└── 📂 data/
└── fifa_world_cup_2026_player_performance.csv


## 🔧 Technologies Used
- **Python 3.10+**
- **Pandas** - معالجة البيانات
- **NumPy** - العمليات الحسابية
- **Matplotlib** - الرسوم البيانية
- **Seaborn** - الـ Heatmap والـ Statistical Plots

## 📊 Key Visualizations
| Visualization | Description |
|--------------|-------------|
| Top 10 Countries | أفضل 10 منتخبات بالتقييم |
| Top 10 Clubs | أفضل 10 أندية بالتقييم |
| Top 10 Scorers | أفضل 10 هدافين |
| Correlation Heatmap | الارتباطات بين المتغيرات |
| Goals vs xG | الأداء الفعلي vs المتوقع |
| Preferred Foot | توزيع القدم المفضلة |
| Position Distribution | توزيع المراكز |
| Fouls by Position | الأخطاء حسب المركز |

## 🏆 Key Findings
- **أفضل منتخب:** البرازيل (متوسط تقييم 7.8)
- **أفضل لاعب:** [اسم اللاعب] (Weighted Score: 0.92)
- **أكتر Overperformer:** [اسم] (+3.2 goals above xG)
- **أقوى correlation:** Goals ↔ Shots on Target (0.92)

## 🚀 How to Run
```bash
# 1. Clone the repo
git clone https://github.com/NoureldinMohamed18/fifa-world-cup-2026-analysis.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the notebook
jupyter notebook fifa_analysis.ipynb