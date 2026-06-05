# predictive v2 - real data

"""
build_predictive2.py  — v2
Reads all 21 real trend files from Data/trend/
Generates predictive_data.json with real multi-year analysis.
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime

TREND_PATH = 'Data/trend'
YEARS_HIST = [2021, 2022, 2023, 2024]
FORECAST_YEARS = [2025, 2026, 2027, 2028]

GOVS = ["العاصمة","البلقاء","الزرقاء","مأدبا","إربد","المفرق","جرش","عجلون","الكرك","الطفيلة","معان","العقبة"]

NAME_MAP = {
    'العاصمة عمان':'العاصمة','عمان':'العاصمة',
    'اربد':'إربد','مادبا':'مأدبا',
    'محافظة العاصمة':'العاصمة',
}
def norm(n):
    n = str(n).strip()
    return NAME_MAP.get(n, n)

def safe(v):
    try:
        f = float(str(v).replace('%','').replace(',','').strip())
        return f if np.isfinite(f) else None
    except: return None

def linear_trend(years, values):
    pts = [(y,v) for y,v in zip(years,values) if v is not None]
    if len(pts) < 2: return 0, 0, {}
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    xm = xs.mean()
    slope = np.dot(xs-xm, ys) / np.dot(xs-xm, xs-xm)
    intercept = ys.mean() - slope*xm
    ss_res = np.sum((ys - (slope*xs+intercept))**2)
    ss_tot = np.sum((ys - ys.mean())**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    forecast = {yr: round(slope*yr+intercept, 2) for yr in FORECAST_YEARS}
    return round(slope,4), round(r2,3), forecast

def trend_class(slope, lower_better, base):
    mag = abs(slope)/(abs(base)+0.001)*100
    improving = (slope<0 if lower_better else slope>0)
    if not improving and mag>2: return 'تراجع_حاد','🔴'
    if not improving and mag>0.3: return 'تراجع_معتدل','🟠'
    if improving and mag>2: return 'تحسن_ملحوظ','🟢'
    if improving: return 'تحسن_تدريجي','🔵'
    return 'مستقر','🟡'

def risk(tc, gap):
    base = {'تراجع_حاد':80,'تراجع_معتدل':55,'مستقر':30,'تحسن_تدريجي':15,'تحسن_ملحوظ':5}.get(tc,30)
    if gap < -10: base = min(100, base+20)
    elif gap < -5: base = min(100, base+10)
    elif gap > 10: base = max(0, base-10)
    return base

# ===== LOAD ALL FILES =====
print('Loading trend files...')

def load_simple(fname, col_map):
    """Load file where columns map directly to years."""
    try:
        df = pd.read_excel(f'{TREND_PATH}/{fname}')
        df['_gov'] = df.iloc[:,0].apply(norm)
        df = df[df['_gov'].isin(GOVS)]
        result = {}
        for _, row in df.iterrows():
            gov = row['_gov']
            result[gov] = {}
            for yr, col in col_map.items():
                if col in df.columns:
                    result[gov][yr] = safe(row[col])
        return result
    except Exception as e:
        print(f'  ERROR {fname}: {e}')
        return {}

# --- UNEMPLOYMENT (2022-2025) ---
unemp = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Unemployment.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    for _, row in df.iterrows():
        gov = row['_gov']
        unemp[gov] = {}
        for yr, col in [(2022,'معدل البطالة 2022'),(2023,'معدل البطالة 2023'),(2024,'معدل البطالة 2024'),(2025,'معدل البطالة 2025')]:
            v = safe(row.get(col))
            if v is None:
                unemp[gov][yr] = None
                continue
            # Convert fraction to percentage if needed
            if v < 1:
                v = round(v * 100, 1)
            # Sanity check: unemployment rate must be between 0 and 60%
            if v > 60 or v < 0:
                unemp[gov][yr] = None
            else:
                unemp[gov][yr] = v
    print(f'  Unemployment: {len(unemp)} govs')
except Exception as e: print(f'  ERROR Unemployment: {e}')

# --- BASIC EDUCATION ENROLLMENT (2021-2024) ---
edu_basic = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Basic_Education_Enrollment_Rates.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'الأساسي' in str(c)]
    years_found = [2021,2022,2023,2024]
    for _, row in df.iterrows():
        gov = row['_gov']
        edu_basic[gov] = {yr: safe(row[c]) for yr,c in zip(years_found, cols[:4])}
    print(f'  Basic Education: {len(edu_basic)} govs')
except Exception as e: print(f'  ERROR Basic Education: {e}')

# --- SECONDARY EDUCATION (2021-2024) ---
edu_sec = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Secondary_Education_Enrollment_Rate.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'الثانوي' in str(c)]
    for _, row in df.iterrows():
        gov = row['_gov']
        edu_sec[gov] = {yr: safe(row[c]) for yr,c in zip([2021,2022,2023,2024], cols[:4])}
    print(f'  Secondary Education: {len(edu_sec)} govs')
except Exception as e: print(f'  ERROR Secondary Education: {e}')

# --- PRE-BASIC ENROLLMENT (2021-2024) ---
edu_pre = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Pre_Basic_Enrollment_Rates_Jordan.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    num_cols = [c for c in df.columns if c != 'المحافظة' and c != '_gov']
    for _, row in df.iterrows():
        gov = row['_gov']
        edu_pre[gov] = {yr: safe(row[c]) for yr,c in zip([2021,2022,2023,2024], num_cols[:4])}
    print(f'  Pre-Basic Education: {len(edu_pre)} govs')
except Exception as e: print(f'  ERROR Pre-Basic: {e}')

# --- POPULATION (2021-2025) ---
population = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Jordan_Governorates_Estimated_Population.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    for _, row in df.iterrows():
        gov = row['_gov']
        population[gov] = {}
        for yr in [2021,2022,2023,2024,2025]:
            col = f'عدد السكان {yr}'
            if col in df.columns: population[gov][yr] = safe(row[col])
    print(f'  Population: {len(population)} govs')
except Exception as e: print(f'  ERROR Population: {e}')

# --- BIRTHS (2021-2024) ---
births = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Birth_Rates_by_Jordan_Governorates.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'مواليد' in str(c)]
    for _, row in df.iterrows():
        gov = row['_gov']
        births[gov] = {yr: safe(row[c]) for yr,c in zip([2021,2022,2023,2024], cols[:4])}
    print(f'  Births: {len(births)} govs')
except Exception as e: print(f'  ERROR Births: {e}')

# --- DEATHS (2021-2024) ---
deaths = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Death_Rates_by_Governorate_Jordan.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'وفيات' in str(c)]
    for _, row in df.iterrows():
        gov = row['_gov']
        deaths[gov] = {yr: safe(row[c]) for yr,c in zip([2021,2022,2023,2024], cols[:4])}
    print(f'  Deaths: {len(deaths)} govs')
except Exception as e: print(f'  ERROR Deaths: {e}')

# --- MARRIAGES (2021-2024) ---
marriages = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Annual_Marriage_Registrations.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    for _, row in df.iterrows():
        gov = row['_gov']
        marriages[gov] = {yr: safe(row.get(str(yr))) for yr in [2021,2022,2023,2024]}
    print(f'  Marriages: {len(marriages)} govs')
except Exception as e: print(f'  ERROR Marriages: {e}')

# --- DIVORCES (2021-2024) ---
divorces = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Demographic_Divorce_Data.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'طلاق' in str(c)]
    for _, row in df.iterrows():
        gov = row['_gov']
        divorces[gov] = {yr: safe(row[c]) for yr,c in zip([2024,2023,2022,2021], cols[:4])}
    print(f'  Divorces: {len(divorces)} govs')
except Exception as e: print(f'  ERROR Divorces: {e}')

# --- CHARITIES (2021-2024) ---
charities = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Number of Charities per Governorate.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'جمعيات' in str(c)]
    for _, row in df.iterrows():
        gov = row['_gov']
        charities[gov] = {yr: safe(row[c]) for yr,c in zip([2021,2022,2023,2024], cols[:4])}
    print(f'  Charities: {len(charities)} govs')
except Exception as e: print(f'  ERROR Charities: {e}')

# --- WATER SUPPLY (2021-2024) ---
water_supply = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/Water Supply.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    cols = [c for c in df.columns if 'التزود' in str(c)]
    for _, row in df.iterrows():
        gov = row['_gov']
        water_supply[gov] = {yr: safe(row[c]) for yr,c in zip([2021,2022,2023,2024], cols[:4])}
    print(f'  Water Supply: {len(water_supply)} govs')
except Exception as e: print(f'  ERROR Water Supply: {e}')

# --- WATER PER CAPITA (2021-2024) ---
water_pc = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/water_share_per_capita_stats.xlsx', header=0)
    # This file has merged header — row 0 is actual header
    df2 = pd.read_excel(f'{TREND_PATH}/water_share_per_capita_stats.xlsx', header=None, skiprows=1)
    df2.columns = ['المحافظة','2021','2022','2023','2024']
    df2['_gov'] = df2['المحافظة'].apply(norm)
    df2 = df2[df2['_gov'].isin(GOVS)]
    for _, row in df2.iterrows():
        gov = row['_gov']
        water_pc[gov] = {yr: safe(row[str(yr)]) for yr in [2021,2022,2023,2024]}
    print(f'  Water per capita: {len(water_pc)} govs')
except Exception as e: print(f'  ERROR Water per capita: {e}')

# --- OLIVE PRODUCTION (2021-2025) ---
olive = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/olive_production_stats.xlsx')
    df['_gov'] = df.iloc[:,0].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    prod_cols = [c for c in df.columns if 'انتاج' in str(c)]
    yrs = [2021,2022,2023,2024,2025]
    for _, row in df.iterrows():
        gov = row['_gov']
        olive[gov] = {yr: safe(row[c]) for yr,c in zip(yrs, prod_cols[:5])}
    print(f'  Olive production: {len(olive)} govs')
except Exception as e: print(f'  ERROR Olive: {e}')

# --- ANIMAL WEALTH (2021-2024) total sheep+goats+cattle ---
animals = {}
try:
    df = pd.read_excel(f'{TREND_PATH}/animal_wealth_stats.xlsx')
    df['_gov'] = df['المحافظة'].apply(norm)
    df = df[df['_gov'].isin(GOVS)]
    for _, row in df.iterrows():
        gov = row['_gov']
        animals[gov] = {}
        for yr in [2021,2022,2023,2024]:
            sheep_col = [c for c in df.columns if 'ضأن' in str(c) and str(yr) in str(c)]
            goat_col = [c for c in df.columns if 'ماعز' in str(c) and str(yr) in str(c)]
            cow_col = [c for c in df.columns if 'أبقار' in str(c) and str(yr) in str(c)]
            total = sum(filter(None, [
                safe(row[sheep_col[0]]) if sheep_col else None,
                safe(row[goat_col[0]]) if goat_col else None,
                safe(row[cow_col[0]]) if cow_col else None,
            ]))
            animals[gov][yr] = total if total > 0 else None
    print(f'  Animal wealth: {len(animals)} govs')
except Exception as e: print(f'  ERROR Animals: {e}')

print('All files loaded.')

# ===== LOAD SYRIAN REFUGEE DATA =====
REFUGEE_DATA = {}
try:
    ref_df = pd.read_excel(f'{TREND_PATH}/../input/Registered_Syrian_Refugees_In-Jordan-2026.xlsx')
    ref_df['_gov'] = ref_df[ref_df.columns[0]].apply(norm)
    ref_df = ref_df[ref_df['_gov'].isin(GOVS)]
    for _, row in ref_df.iterrows():
        gov = row['_gov']
        count = safe(row.iloc[1])
        pct = safe(row.iloc[2])
        REFUGEE_DATA[gov] = {'count': int(count) if count else 0, 'pct': round(pct, 4) if pct else 0.0}
    print(f'  Refugee data: {len(REFUGEE_DATA)} govs loaded')
    for gov in GOVS:
        if gov in REFUGEE_DATA:
            d = REFUGEE_DATA[gov]
            print(f'    {gov}: {d["count"]:,} refugees ({d["pct"]*100:.2f}%)')
except Exception as e:
    print(f'  ERROR loading refugee data: {e}')
    REFUGEE_DATA = {}

# ===== INDICATOR DEFINITIONS =====
INDICATORS = {
    'البطالة': {
        'label': 'معدل البطالة', 'unit': '%', 'lower_better': True,
        'sector': 'التنمية الاجتماعية', 'weight': 1.5, 'data': unemp,
        'years': [2022,2023,2024,2025]
    },
    'التعليم_الأساسي': {
        'label': 'الالتحاق بالتعليم الأساسي', 'unit': '%', 'lower_better': False,
        'sector': 'التعليم', 'weight': 1.2, 'data': edu_basic,
        'years': [2021,2022,2023,2024]
    },
    'التعليم_الثانوي': {
        'label': 'الالتحاق بالتعليم الثانوي', 'unit': '%', 'lower_better': False,
        'sector': 'التعليم', 'weight': 1.0, 'data': edu_sec,
        'years': [2021,2022,2023,2024]
    },
    'التعليم_ما_قبل_الأساسي': {
        'label': 'الالتحاق بما قبل الأساسي', 'unit': '%', 'lower_better': False,
        'sector': 'التعليم', 'weight': 0.8, 'data': edu_pre,
        'years': [2021,2022,2023,2024]
    },
    'المواليد': {
        'label': 'إجمالي المواليد', 'unit': 'مولود', 'lower_better': False,
        'sector': 'الصحة', 'weight': 0.8, 'data': births,
        'years': [2021,2022,2023,2024]
    },
    'الوفيات': {
        'label': 'إجمالي الوفيات', 'unit': 'حالة', 'lower_better': True,
        'sector': 'الصحة', 'weight': 1.0, 'data': deaths,
        'years': [2021,2022,2023,2024]
    },
    'الزواج': {
        'label': 'عقود الزواج', 'unit': 'عقد', 'lower_better': False,
        'sector': 'الثقافة', 'weight': 0.7, 'data': marriages,
        'years': [2021,2022,2023,2024]
    },
    'الطلاق': {
        'label': 'وقوعات الطلاق', 'unit': 'حالة', 'lower_better': True,
        'sector': 'الثقافة', 'weight': 0.8, 'data': divorces,
        'years': [2021,2022,2023,2024]
    },
    'الجمعيات_الخيرية': {
        'label': 'الجمعيات الخيرية', 'unit': 'جمعية', 'lower_better': False,
        'sector': 'الثقافة', 'weight': 0.9, 'data': charities,
        'years': [2021,2022,2023,2024]
    },
    'التزود_المائي': {
        'label': 'التزود المائي', 'unit': 'مليون م³', 'lower_better': False,
        'sector': 'المياه والصرف الصحي', 'weight': 1.2, 'data': water_supply,
        'years': [2021,2022,2023,2024]
    },
    'حصة_الفرد_المياه': {
        'label': 'حصة الفرد من المياه', 'unit': 'لتر/يوم', 'lower_better': False,
        'sector': 'المياه والصرف الصحي', 'weight': 1.3, 'data': water_pc,
        'years': [2021,2022,2023,2024]
    },
    'إنتاج_الزيتون': {
        'label': 'إنتاج الزيتون', 'unit': 'طن', 'lower_better': False,
        'sector': 'الزراعة', 'weight': 1.0, 'data': olive,
        'years': [2021,2022,2023,2024,2025]
    },
    'الثروة_الحيوانية': {
        'label': 'إجمالي الثروة الحيوانية', 'unit': 'رأس', 'lower_better': False,
        'sector': 'الزراعة', 'weight': 1.0, 'data': animals,
        'years': [2021,2022,2023,2024]
    },
    'السكان': {
        'label': 'عدد السكان', 'unit': 'نسمة', 'lower_better': False,
        'sector': 'البنية التحتية', 'weight': 0.6, 'data': population,
        'years': [2021,2022,2023,2024,2025]
    },
}

# ===== GOVERNORATE CONTEXT PROFILES =====
GOV_CONTEXT = {
    'العاصمة': {
        'terrain': 'حضرية، مركز سياسي واقتصادي',
        'features': ['العاصمة', 'مركز اقتصادي', 'كثافة سكانية عالية', 'وجود الوزارات والمؤسسات المركزية'],
        'agri_context': 'أراضٍ زراعية محدودة، تركيز على الزراعة الحضرية والمشاتل',
        'tourism_context': 'متاحف ومواقع أثرية (القلعة، المدرج الروماني، المدينة الرياضية)',
        'water_context': 'شبكات مياه متطورة لكنها قديمة وتحتاج صيانة، استهلاك مرتفع',
        'economy_context': 'قطاع خدمات ومال وأعمال مهيمن، فرص استثمارية في التكنولوجيا',
    },
    'البلقاء': {
        'terrain': 'سهلية غربية، مطلّة على البحر الميت',
        'features': ['سهول خصبة', 'إطلالة على البحر الميت', 'قرب من العاصمة', 'منتجعات سياحية'],
        'agri_context': 'أراضٍ زراعية خصبة، أشجار مثمرة وخضار، عين الباشا والشونة',
        'tourism_context': 'المنتجعات السياحية على البحر الميت، المواقع الطبيعية',
        'water_context': 'مصادر مياه محدودة نسبياً، اعتماد على مياه الأمطار والآبار',
        'economy_context': 'اقتصاد زراعي وسياحي، فرص في الصناعات الغذائية',
    },
    'الزرقاء': {
        'terrain': 'سهلية شرقية، منطقة صناعية كبرى',
        'features': ['مدينة صناعية', 'منطقة حرة', 'كثافة سكانية', 'مركز نقل ولوجستي'],
        'agri_context': 'أراضٍ زراعية محدودة، تربية حيوانية في المناطق الريفية المحيطة',
        'tourism_context': 'مواقع أثرية قليلة، سياحة تسوق وصناعية',
        'water_context': 'مياه جوفية مهددة بالتلوث الصناعي، حاجة لمعالجة متقدمة',
        'economy_context': 'قطاع صناعي ضخم (مصانع، منطقة حرة)، فرص في الطاقة المتجددة',
    },
    'مأدبا': {
        'terrain': 'هضبة وسطى، أرض زراعية خصبة',
        'features': ['مدينة الفسيفساء', 'مواقع أثرية مسيحية', 'أراضٍ زراعية', 'قرب من العاصمة'],
        'agri_context': 'أراضٍ زراعية جيدة، محاصيل حقلية وأشجار زيتون',
        'tourism_context': 'كنائس الفسيفساء، المواقع الأثرية، جبل نيبو، السياحة الدينية',
        'water_context': 'موارد مياه معتدلة، زراعات مروية محدودة',
        'economy_context': 'اقتصاد سياحي وزراعي حرفي، فرص في الصناعات التقليدية',
    },
    'إربد': {
        'terrain': 'سهلية شمالية خصبة، ثاني أكبر مدينة',
        'features': ['سهول حوران الخصبة', 'جامعات كبرى', 'سكان متعلمون', 'منطقة تجارية نشطة'],
        'agri_context': 'أرض زراعية من الأخصب في الأردن (حبوب، خضار، زيتون)',
        'tourism_context': 'مواقع أثرية (أم قيس، بيت رأس، درب الحجاز)، سياحة ثقافية',
        'water_context': 'مياه جوفية محدودة، اعتماد على الأمطار في الزراعة',
        'economy_context': 'قطاع تعليمي وزراعي وتجاري، أيدٍ عاملة شابة ومتعلمة',
    },
    'المفرق': {
        'terrain': 'بادية شمالية شرقية، أراضٍ صحراوية واسعة',
        'features': ['بادية واسعة', 'قرب من الحدود', 'منطقة عسكرية', 'طاقة شمسية واعدة'],
        'agri_context': 'زراعة مطرية محدودة (حبوب)، ثروة حيوانية (أغنام وإبل)',
        'tourism_context': 'سياحة صحراوية، محميات طبيعية، مواقع أثرية بدوية',
        'water_context': 'شح مائي حاد، اعتماد كامل على المياه الجوفية العميقة',
        'economy_context': 'اقتصاد رعوي وحدودي، فرص كبيرة في الطاقة الشمسية',
    },
    'جرش': {
        'terrain': 'جبلية شمالية، غابات وطبيعة خلابة',
        'features': ['مدينة جرش الأثرية', 'غابات كثيفة', 'ينابيع مياه', 'سياحة أثرية'],
        'agri_context': 'أراضٍ زراعية على سفوح الجبال، أشجار زيتون وفواكه',
        'tourism_context': 'موقع جرش الأثري (أهم المواقع الرومانية)، مهرجان جرش',
        'water_context': 'ينابيع مياه طبيعية وافرة نسبياً، شبكات قديمة',
        'economy_context': 'اقتصاد سياحي وزراعي، حرف يدوية تقليدية',
    },
    'عجلون': {
        'terrain': 'جبلية وعرة، غابات كثيفة، تضاريس جبلية',
        'features': ['قلعة عجلون', 'غابات كثيفة', 'منتزهات طبيعية', 'تضاريس جبلية وعرة'],
        'agri_context': 'تضاريس جبلية تصلح لأشجار الزيتون والتفاح، مصاطب زراعية',
        'tourism_context': 'قلعة عجلون، محمية غابات عجلون، السياحة البيئية والمغامرات',
        'water_context': 'مياه أمطار غزيرة نسبياً، ينابيع موسمية، حصاد مائي واعد',
        'economy_context': 'اقتصاد سياحي وزراعي جبلي، فرص في السياحة البيئية',
    },
    'الكرك': {
        'terrain': 'جبال جنوبية، هضبة وعرة',
        'features': ['قلعة الكرك', 'مواقع أثرية تاريخية', 'أراضٍ زراعية', 'تراث ثقافي غني'],
        'agri_context': 'أراضٍ زراعية في الوديان والهضاب، كرمة وعنب وزيتون',
        'tourism_context': 'قلعة الكرك، متاحف، طريق الملوك',
        'water_context': 'موارد مائية محدودة، حاجة لتطوير حصاد الأمطار',
        'economy_context': 'اقتصاد متنوع بين الزراعة والسياحة والخدمات الحكومية',
    },
    'الطفيلة': {
        'terrain': 'جبلية جنوبية، غابات صنوبر',
        'features': ['غابات صنوبر', 'منتزهات طبيعية', 'ينابيع', 'أراضٍ زراعية مرتفعة'],
        'agri_context': 'أراضٍ زراعية مرتفعة، تفاح وخوخ وعنب، زراعات بعلية',
        'tourism_context': 'غابات الطفيلة، المحميات الطبيعية، السياحة البيئية',
        'water_context': 'مياه جوفية محدودة، اعتماد على الينابيع الموسمية',
        'economy_context': 'اقتصاد زراعي وغابي محدود، فرص في السياحة البيئية',
    },
    'معان': {
        'terrain': 'صحراوية جنوبية، هضبة صخرية',
        'features': ['صحراء واسعة', 'موقع استراتيجي على طريق الحجاز', 'منطقة صناعية واعدة', 'طاقة متجددة'],
        'agri_context': 'زراعة محدودة (واحات زيتون ونخيل)، ثروة حيوانية (أغنام وإبل)',
        'tourism_context': 'العقبة قريبة، البتراء قريبة، سياحة مغامرات صحراوية',
        'water_context': 'شح مائي حاد جداً، اعتماد على مياه الآبار الجوفية العميقة',
        'economy_context': 'اقتصاد خدمي ولوجستي، المنطقة الصناعية، طاقة شمسية واعدة',
    },
    'العقبة': {
        'terrain': 'ساحلية جنوبية، شاطئ البحر الأحمر',
        'features': ['ميناء بحري', 'منطقة اقتصادية خاصة', 'شواطئ ومنتجعات', 'سياحة غوص'],
        'agri_context': 'زراعة محدودة في وادي عربة، استزراع سمكي واعد',
        'tourism_context': 'الغوص والشواطئ، منتجعات فاخرة، سياحة بحرية دولية',
        'water_context': 'تحلية مياه البحر مصدر رئيسي، مياه مدعومة حكومياً',
        'economy_context': 'منطقة اقتصادية خاصة، ميناء، سياحة عالمية، فرص لوجستية',
    },
}

# ===== CAUSAL FACTORS FOR INTERPRETIVE GAP ANALYSIS =====
CAUSAL_FACTORS = {
    'العاصمة': {
        'refugee_pressure': 'متوسطة', 'covid_impact': 'مرتفع',
        'poverty': 'منخفض', 'dependency': 'منخفض', 'border': False,
        'large_area': False, 'dense': True, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': False,
    },
    'البلقاء': {
        'refugee_pressure': 'متوسطة', 'covid_impact': 'متوسط',
        'poverty': 'متوسط', 'dependency': 'متوسط', 'border': False,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': False,
    },
    'الزرقاء': {
        'refugee_pressure': 'مرتفع', 'covid_impact': 'متوسط',
        'poverty': 'متوسط', 'dependency': 'متوسط', 'border': False,
        'large_area': True, 'dense': True, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': False,
    },
    'مأدبا': {
        'refugee_pressure': 'منخفض', 'covid_impact': 'منخفض',
        'poverty': 'متوسط', 'dependency': 'متوسط', 'border': False,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': True,
    },
    'إربد': {
        'refugee_pressure': 'مرتفع', 'covid_impact': 'متوسط',
        'poverty': 'متوسط', 'dependency': 'متوسط', 'border': True,
        'large_area': False, 'dense': True, 'syrian_returnee': True,
        'transport_weak': False, 'low_participation': False,
    },
    'المفرق': {
        'refugee_pressure': 'مرتفع', 'covid_impact': 'منخفض',
        'poverty': 'مرتفع', 'dependency': 'مرتفع', 'border': True,
        'large_area': True, 'dense': False, 'syrian_returnee': True,
        'transport_weak': True, 'low_participation': True,
    },
    'جرش': {
        'refugee_pressure': 'متوسطة', 'covid_impact': 'متوسط',
        'poverty': 'مرتفع', 'dependency': 'مرتفع', 'border': False,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': True,
    },
    'عجلون': {
        'refugee_pressure': 'متوسطة', 'covid_impact': 'متوسط',
        'poverty': 'مرتفع', 'dependency': 'مرتفع', 'border': False,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': True, 'low_participation': True,
    },
    'الكرك': {
        'refugee_pressure': 'منخفض', 'covid_impact': 'متوسط',
        'poverty': 'مرتفع', 'dependency': 'متوسط', 'border': False,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': False,
    },
    'الطفيلة': {
        'refugee_pressure': 'منخفض', 'covid_impact': 'منخفض',
        'poverty': 'مرتفع', 'dependency': 'مرتفع', 'border': False,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': True,
    },
    'معان': {
        'refugee_pressure': 'منخفض', 'covid_impact': 'منخفض',
        'poverty': 'مرتفع', 'dependency': 'مرتفع', 'border': True,
        'large_area': True, 'dense': False, 'syrian_returnee': False,
        'transport_weak': True, 'low_participation': True,
    },
    'العقبة': {
        'refugee_pressure': 'منخفض', 'covid_impact': 'مرتفع',
        'poverty': 'منخفض', 'dependency': 'منخفض', 'border': True,
        'large_area': False, 'dense': False, 'syrian_returnee': False,
        'transport_weak': False, 'low_participation': False,
    },
}

def refugee_band(gov):
    """Return (refugee_text_inclusion_flag, band_label) based on actual Syrian refugee %."""
    rd = REFUGEE_DATA.get(gov, {})
    pct = rd.get('pct', 0.0)
    count = rd.get('count', 0)
    pct_display = f'{pct*100:.2f}%'

    if pct > 0.10:
        return (True, f'\u0636\u063a\u0637 \u062f\u064a\u0645\u0648\u063a\u0631\u0627\u0641\u064a \u0642\u0633\u0631\u064a \u0623\u062f\u0649 \u0644\u0625\u0646\u0647\u0627\u0643 \u0627\u0644\u0645\u0631\u0627\u0641\u0642 \u2014 \u0641\u0646\u0633\u0628\u0629 \u0627\u0644\u0644\u0627\u062c\u0626\u064a\u0646 \u0627\u0644\u0633\u0648\u0631\u064a\u064a\u0646 \u062a\u0628\u0644\u063a {pct_display} \u0645\u0646 \u0633\u0643\u0627\u0646 \u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629 ({count:,} \u0644\u0627\u062c\u0626\u0627\u064b)')
    elif 0.02 <= pct <= 0.05:
        return (True, f'\u0645\u0646\u0627\u0641\u0633\u0629 \u0645\u062a\u0632\u0627\u064a\u062f\u0629 \u0639\u0644\u0649 \u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0623\u0633\u0627\u0633\u064a\u0629 \u0648\u0633\u0648\u0642 \u0627\u0644\u0639\u0645\u0644 \u0628\u0633\u0628\u0628 \u0648\u062c\u0648\u062f {count:,} \u0644\u0627\u062c\u0626\u064b\u0627 \u0633\u0648\u0631\u064a\u0627\u064b (\u0646\u0633\u0628\u0629 {pct_display})')
    elif 0.01 <= pct < 0.02:
        return (True, f'\u0636\u063a\u0648\u0637 \u0645\u0639\u062a\u062f\u0644\u0629 \u0639\u0644\u0649 \u0628\u0639\u0636 \u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0639\u0627\u0645\u0629 \u0648\u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0646\u062a\u064a\u062c\u0629 \u0648\u062c\u0648\u062f {count:,} \u0644\u0627\u062c\u0626\u064b\u0627 (\u0646\u0633\u0628\u0629 {pct_display})')
    else:
        return (False, '')

GOV_FLAVOR = {
    '\u0627\u0644\u0639\u0627\u0635\u0645\u0629': '\u0641\u064a \u0639\u0645\u0627\u0646 \u0627\u0644\u0645\u0643\u062a\u0638\u0629 \u0628\u0627\u0644\u0633\u0643\u0627\u0646 \u0648\u0627\u0644\u0623\u0646\u0634\u0637\u0629 \u0627\u0644\u0627\u0642\u062a\u0635\u0627\u062f\u064a\u0629\u060c \u062a\u062a\u0636\u0627\u0639\u0641 \u0627\u0644\u0641\u062c\u0648\u0629 \u0628\u0633\u0628\u0628 \u0627\u0644\u0637\u0644\u0628 \u0627\u0644\u0645\u062a\u0632\u0627\u064a\u062f \u0639\u0644\u0649 \u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0648\u0636\u063a\u0637 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0627\u0644\u0642\u062f\u064a\u0645\u0629',
    '\u0627\u0644\u0628\u0644\u0642\u0627\u0621': '\u0641\u064a \u0627\u0644\u0628\u0644\u0642\u0627\u0621\u060c \u062d\u064a\u062b \u0627\u0644\u062a\u0648\u0627\u0632\u0646 \u0628\u064a\u0646 \u0627\u0644\u0637\u0628\u064a\u0639\u0629 \u0627\u0644\u0633\u0647\u0644\u064a\u0629 \u0648\u0627\u0644\u0627\u0642\u062a\u0631\u0627\u0628 \u0645\u0646 \u0627\u0644\u0639\u0627\u0635\u0645\u0629\u060c \u062a\u062a\u0636\u0627\u0641\u0642 \u0636\u063a\u0648\u0637 \u0627\u0644\u0644\u062c\u0648\u0621 \u0645\u0639 \u062d\u062f\u0648\u062f \u0627\u0644\u0642\u062f\u0631\u0629 \u0627\u0644\u0627\u0633\u062a\u064a\u0639\u0627\u0628\u064a\u0629 \u0644\u0644\u062e\u062f\u0645\u0627\u062a',
    '\u0627\u0644\u0632\u0631\u0642\u0627\u0621': '\u062a\u0634\u0647\u062f \u0627\u0644\u0632\u0631\u0642\u0627\u0621 \u062a\u0631\u0643\u0632\u0627\u064b \u0643\u0628\u064a\u0631\u0627\u064b \u0644\u0644\u0627\u062c\u0626\u064a\u0646 \u0641\u064a \u0645\u062e\u064a\u0645\u0627\u062a \u0631\u0633\u0645\u064a\u0629\u060c \u0645\u0627 \u064a\u0636\u0627\u0639\u0641 \u0627\u0644\u0636\u063a\u0637 \u0639\u0644\u0649 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0648\u0634\u0628\u0643\u0627\u062a \u0627\u0644\u0645\u064a\u0627\u0647 \u0648\u0627\u0644\u0635\u0631\u0641 \u0627\u0644\u0635\u062d\u064a',
    '\u0645\u0623\u062f\u0628\u0627': '\u0641\u064a \u0645\u0623\u062f\u0628\u0627\u060c \u062d\u064a\u062b \u0627\u0644\u0647\u0636\u0628\u0629 \u0627\u0644\u0632\u0631\u0627\u0639\u064a\u0629\u060c \u062a\u0646\u0639\u0643\u0633 \u0627\u0644\u0636\u063a\u0648\u0637 \u0627\u0644\u062f\u064a\u0645\u0648\u063a\u0631\u0627\u0641\u064a\u0629 \u0639\u0644\u0649 \u0627\u0644\u0642\u0637\u0627\u0639\u064a\u0646 \u0627\u0644\u0632\u0631\u0627\u0639\u064a \u0648\u0627\u0644\u062e\u062f\u0645\u064a \u0628\u0634\u0643\u0644 \u0645\u062a\u0632\u0627\u064a\u062f',
    '\u0625\u0631\u0628\u062f': '\u0625\u0631\u0628\u062f \u0627\u0644\u0645\u062a\u0627\u062e\u0645\u0629 \u0628\u0627\u0644\u062d\u062f\u0648\u062f \u0627\u0644\u0633\u0648\u0631\u064a\u0629 \u062a\u0648\u0627\u062c\u0647 \u0636\u063a\u0648\u0637\u0627\u064b \u0645\u0636\u0627\u0639\u0641\u0629 \u0639\u0644\u0649 \u0642\u0637\u0627\u0639\u064a \u0627\u0644\u062a\u0639\u0644\u064a\u0645 \u0648\u0627\u0644\u0635\u062d\u0629 \u0646\u062a\u064a\u062c\u0629 \u0627\u0644\u062a\u0648\u0627\u062c\u062f \u0627\u0644\u0633\u0643\u0627\u0646\u064a \u0627\u0644\u0643\u062b\u064a\u0641 \u0644\u0644\u0627\u062c\u0626\u064a\u0646',
    '\u0627\u0644\u0645\u0641\u0631\u0642': '\u0641\u064a \u0627\u0644\u0645\u0641\u0631\u0642\u060c \u0623\u0639\u0644\u0649 \u0646\u0633\u0628 \u0644\u062c\u0648\u0621 \u0641\u064a \u0627\u0644\u0645\u0645\u0644\u0643\u0629\u060c \u062d\u064a\u062b \u0623\u0646\u0647\u0643\u062a \u0627\u0644\u0645\u062e\u064a\u0645\u0627\u062a \u0627\u0644\u0642\u062f\u0631\u0629 \u0627\u0644\u0627\u0633\u062a\u064a\u0639\u0627\u0628\u064a\u0629 \u0644\u0644\u0645\u0631\u0627\u0641\u0642 \u0641\u064a \u0645\u062d\u0627\u0641\u0638\u0629 \u0635\u062d\u0631\u0627\u0648\u064a\u0629 \u0641\u0642\u064a\u0631\u0629 \u0627\u0644\u0645\u0648\u0627\u0631\u062f \u0623\u0635\u0644\u0627\u064b',
    '\u062c\u0631\u0634': '\u062a\u062a\u0645\u064a\u0632 \u062c\u0631\u0634 \u0628\u0645\u0648\u0642\u0639\u0647\u0627 \u0627\u0644\u0623\u062b\u0631\u064a \u0627\u0644\u0641\u0631\u064a\u062f\u060c \u0648\u0644\u0643\u0646 \u0627\u0644\u0636\u063a\u0648\u0637 \u0627\u0644\u062f\u064a\u0645\u0648\u063a\u0631\u0627\u0641\u064a\u0629 \u062a\u0632\u064a\u062f \u0645\u0646 \u0627\u0644\u0639\u0628\u0621 \u0639\u0644\u0649 \u062e\u062f\u0645\u0627\u062a\u0647\u0627 \u0627\u0644\u0645\u062d\u062f\u0648\u062f\u0629 \u0623\u0635\u0644\u0627\u064b',
    '\u0639\u062c\u0644\u0648\u0646': '\u0641\u064a \u0639\u062c\u0644\u0648\u0646 \u0627\u0644\u062c\u0628\u0644\u064a\u0629\u060c \u062a\u062a\u0631\u0643\u0632 \u0627\u0644\u0636\u063a\u0648\u0637 \u0639\u0644\u0649 \u0645\u0631\u0627\u0641\u0642 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0627\u0644\u0645\u062d\u062f\u0648\u062f\u0629 \u0648\u0634\u0628\u0643\u0627\u062a \u0627\u0644\u0637\u0631\u0642 \u0627\u0644\u0648\u0639\u0631\u0629',
    '\u0627\u0644\u0643\u0631\u0643': '\u0641\u064a \u0627\u0644\u0643\u0631\u0643\u060c \u062d\u064a\u062b \u0627\u0644\u062a\u0636\u0627\u0631\u064a\u0633 \u0627\u0644\u062c\u0628\u0644\u064a\u0629 \u0627\u0644\u0648\u0639\u0631\u0629\u060c \u062a\u0632\u062f\u0627\u062f \u0635\u0639\u0648\u0628\u0629 \u062a\u0648\u0641\u064a\u0631 \u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0645\u0639 \u0627\u0644\u0636\u063a\u0648\u0637 \u0627\u0644\u0633\u0643\u0627\u0646\u064a\u0629 \u0627\u0644\u0645\u062a\u0632\u0627\u064a\u062f\u0629',
    '\u0627\u0644\u0637\u0641\u064a\u0644\u0629': '\u062a\u0639\u0627\u0646\u064a \u0627\u0644\u0637\u0641\u064a\u0644\u0629 \u0645\u0646 \u0636\u0639\u0641 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0648\u0645\u062d\u062f\u0648\u062f\u064a\u0629 \u0627\u0644\u0645\u0648\u0627\u0631\u062f \u0627\u0644\u062a\u0646\u0645\u0648\u064a\u0629 \u0641\u064a \u0627\u0644\u0623\u0633\u0627\u0633',
    '\u0645\u0639\u0627\u0646': '\u0641\u064a \u0645\u0639\u0627\u0646 \u0627\u0644\u0635\u062d\u0631\u0627\u0648\u064a\u0629\u060c \u062a\u062a\u0636\u0627\u0639\u0641 \u0627\u0644\u0641\u062c\u0648\u0629 \u0628\u0633\u0628\u0628 \u0645\u0648\u0642\u0639\u0647\u0627 \u0627\u0644\u062d\u062f\u0648\u062f\u064a \u0648\u0634\u062d \u0627\u0644\u0645\u0648\u0627\u0631\u062f \u0627\u0644\u0637\u0628\u064a\u0639\u064a\u0629 \u0648\u0627\u0644\u0628\u0634\u0631\u064a\u0629',
    '\u0627\u0644\u0639\u0642\u0628\u0629': '\u0641\u064a \u0627\u0644\u0639\u0642\u0628\u0629 \u0627\u0644\u0633\u0627\u062d\u0644\u064a\u0629\u060c \u064a\u0631\u062a\u0628\u0637 \u0627\u0644\u062a\u062d\u062f\u064a \u0627\u0644\u0631\u0626\u064a\u0633\u064a \u0628\u062a\u0648\u0627\u0632\u0646 \u0627\u0644\u0646\u0645\u0648 \u0627\u0644\u0633\u0631\u064a\u0639 \u0645\u0639 \u0642\u062f\u0631\u0629 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0648\u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0639\u0644\u0649 \u0645\u0648\u0627\u0643\u0628\u0629 \u0627\u0644\u0637\u0644\u0628',
}

def causal_detail(ind_key, gov, gap_pct, cf, terrain):
    """Generate causal explanation text per the interpretive framework."""
    include_ref, ref_txt = refugee_band(gov)
    low_p = cf.get('low_participation', False)
    transp = cf.get('transport_weak', False)
    syr_ret = cf.get('syrian_returnee', False)
    is_edu = '\u062a\u0639\u0644\u064a\u0645' in ind_key.replace('_', '')
    flavor = GOV_FLAVOR.get(gov, '')

    # Economic base — always included
    economic_clause = '\u062a\u062f\u0627\u062e\u0644 \u0639\u0648\u0627\u0645\u0644 \u0627\u0642\u062a\u0635\u0627\u062f\u064a\u0629 (\u062a\u0636\u062e\u0645 \u0648\u0641\u0642\u0631 \u0648\u0627\u0631\u062a\u0641\u0627\u0639 \u0643\u0644\u0641 \u0627\u0644\u0645\u0639\u064a\u0634\u0629)'

    if include_ref:
        demographic_clause = f'\u0636\u063a\u0648\u0637 \u062f\u064a\u0645\u0648\u063a\u0631\u0627\u0641\u064a\u0629 \u0646\u0627\u062a\u062c\u0629 \u0639\u0646 {ref_txt}'
        base = f'\u062a\u064f\u0639\u0632\u0649 \u0647\u0630\u0647 \u0627\u0644\u0641\u062c\u0648\u0629 \u0627\u0644\u062a\u064a \u0628\u0644\u063a\u062a {gap_pct}% \u0625\u0644\u0649 {economic_clause} \u0645\u0639 {demographic_clause}\u060c \u0645\u0636\u0627\u0641\u0627\u064b \u0625\u0644\u064a\u0647\u0627 \u0622\u062b\u0627\u0631 \u0627\u0644\u062a\u0639\u0627\u0641\u064a \u0627\u0644\u0628\u0637\u064a\u0621 \u0645\u0646 \u0623\u0632\u0645\u0629 \u0643\u0648\u0631\u0648\u0646\u0627'
    else:
        # Refugee < 1%: focus only on poverty, inflation, COVID
        base = f'\u062a\u064f\u0639\u0632\u0649 \u0647\u0630\u0647 \u0627\u0644\u0641\u062c\u0648\u0629 \u0627\u0644\u062a\u064a \u0628\u0644\u063a\u062a {gap_pct}% \u0625\u0644\u0649 {economic_clause}\u060c \u0645\u0636\u0627\u0641\u0627\u064b \u0625\u0644\u064a\u0647\u0627 \u0636\u0639\u0641 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0648\u0645\u062d\u062f\u0648\u062f\u064a\u0629 \u0627\u0644\u0645\u0648\u0627\u0631\u062f \u0627\u0644\u062a\u0646\u0645\u0648\u064a\u0629\u060c \u0645\u0639 \u0622\u062b\u0627\u0631 \u0627\u0644\u062a\u0639\u0627\u0641\u064a \u0627\u0644\u0628\u0637\u064a\u0621 \u0645\u0646 \u0623\u0632\u0645\u0629 \u0643\u0648\u0631\u0648\u0646\u0627'

    parts = [base]
    if flavor:
        parts.append(flavor)
    if transp and (is_edu or '\u0645\u064a\u0627\u0647' in ind_key):
        parts.append('\u0648\u064a\u0631\u0627\u0641\u0642 \u0630\u0644\u0643 \u0636\u0639\u0641 \u0634\u0628\u0643\u0629 \u0627\u0644\u0646\u0642\u0644 \u0627\u0644\u0639\u0627\u0645 \u0641\u064a \u0647\u0630\u0647 \u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629 \u0630\u0627\u062a \u0627\u0644\u0645\u0633\u0627\u062d\u0627\u062a \u0627\u0644\u0648\u0627\u0633\u0639\u0629 \u0645\u0645\u0627 \u064a\u0639\u064a\u0642 \u0627\u0644\u0648\u0635\u0648\u0644 \u0644\u0644\u062e\u062f\u0645\u0627\u062a \u0641\u064a \u0627\u0644\u0645\u0646\u0627\u0637\u0642 \u0627\u0644\u0646\u0627\u0626\u064a\u0629')
    if syr_ret and ind_key == '\u0627\u0644\u0633\u0643\u0627\u0646':
        parts.append('\u0643\u0645\u0627 \u0623\u0646 \u0639\u0648\u062f\u0629 \u0623\u0639\u062f\u0627\u062f \u0645\u0646 \u0627\u0644\u0644\u0627\u062c\u0626\u064a\u0646 \u0627\u0644\u0633\u0648\u0631\u064a\u064a\u0646 \u0625\u0644\u0649 \u0628\u0644\u0627\u062f\u0647\u0645 \u062a\u0624\u062b\u0631 \u0639\u0644\u0649 \u0627\u0644\u062a\u0631\u0643\u064a\u0628\u0629 \u0627\u0644\u0633\u0643\u0627\u0646\u064a\u0629 \u0648\u062a\u062e\u0641\u0641 \u0627\u0644\u0636\u063a\u0637 \u0639\u0644\u0649 \u0627\u0644\u062e\u062f\u0645\u0627\u062a')

    result = '\u060c '.join(parts) + '.'

    if ind_key == '\u0627\u0644\u0628\u0637\u0627\u0644\u0629' and low_p:
        result += ' \u0648\u0644\u0627 \u064a\u0645\u0643\u0646 \u0645\u0639\u0627\u0644\u062c\u062a\u0647\u0627 \u0628\u0645\u062c\u0631\u062f \u062a\u0648\u0641\u064a\u0631 \u0648\u0638\u0627\u0626\u0641\u060c \u0628\u0644 \u062a\u062a\u0637\u0644\u0628 \u062a\u0645\u0643\u064a\u0646\u0627\u064b \u0627\u0642\u062a\u0635\u0627\u062f\u064a\u0627\u064b \u0634\u0627\u0645\u0644\u0627\u064b \u0648\u0645\u0639\u0627\u0644\u062c\u0629 \u062c\u0630\u0631\u064a\u0629 \u0644\u0644\u0641\u0642\u0631 \u0627\u0644\u0647\u064a\u0643\u0644\u064a.'

    return result

def crisis_solutions(ind_key, cf):
    """Add crisis-resilience solutions to face future shocks."""
    sols = []
    covid = cf.get('covid_impact', '')
    if covid in ('مرتفع', 'متوسط'):
        sols.append('تعزيز شبكات الحماية الاجتماعية لمواجهة الصدمات المستقبلية المماثلة للأزمات الصحية العالمية')
    is_edu = 'تعليم' in ind_key.replace('_', '')
    if is_edu or ind_key == 'البطالة':
        sols.append('التحول الرقمي في تقديم الخدمات (التعليم عن بُعد/التوظيف الإلكتروني) لضمان استمرارية الخدمات في الأزمات')
    elif ind_key in ('التزود_المائي', 'حصة_الفرد_المياه'):
        sols.append('التحول الرقمي في إدارة الموارد المائية (العدادات الذكية وأنظمة الإنذار المبكر)')
    elif ind_key in ('إنتاج_الزيتون', 'الثروة_الحيوانية'):
        sols.append('التحول الرقمي في الزراعة (الزراعة الذكية مناخياً وأنظمة الإنذار المبكر للجفاف)')
    else:
        sols.append('التحول الرقمي لضمان استمرارية الخدمات الأساسية في الأزمات المستقبلية')
    if ind_key == 'السكان' and cf.get('border'):
        sols.append('تعزيز شبكات الحماية الاجتماعية للمجتمعات المضيفة والمتأثرة بتداعيات اللجوء')
    return sols

def prepend_crisis_solutions(actions, crisis_sols):
    """Prepend crisis solutions to action list, keeping existing actions after."""
    for s in reversed(crisis_sols):
        actions.insert(0, s)

SECTOR_RELATIONS = [
    ('المياه والصرف الصحي', 'الزراعة', '\u062a\u0637\u0648\u064a\u0631 \u062d\u0644\u0648\u0644 \u062d\u0635\u0627\u062f \u0645\u0627\u0626\u064a \u0644\u062f\u0639\u0645 \u0627\u0644\u0627\u0633\u062a\u062f\u0627\u0645\u0629 \u0627\u0644\u0632\u0631\u0627\u0639\u064a\u0629'),
    ('\u0627\u0644\u062a\u0639\u0644\u064a\u0645', '\u0627\u0644\u0628\u0637\u0627\u0644\u0629', '\u0625\u0635\u0644\u0627\u062d \u0645\u062e\u0631\u062c\u0627\u062a \u0627\u0644\u062a\u0639\u0644\u064a\u0645 \u0644\u062a\u062e\u0641\u064a\u0636 \u0627\u0644\u0628\u0637\u0627\u0644\u0629 \u0628\u062a\u0648\u062c\u064a\u0647 \u0627\u0644\u062e\u0631\u064a\u062c\u064a\u0646 \u0644\u0644\u0645\u0647\u0627\u0631\u0627\u062a \u0627\u0644\u0645\u0637\u0644\u0648\u0628\u0629'),
    ('\u0627\u0644\u0635\u062d\u0629', '\u0627\u0644\u062b\u0642\u0627\u0641\u0629 \u0648\u0627\u0644\u0645\u062c\u062a\u0645\u0639', '\u0625\u0637\u0644\u0627\u0642 \u0628\u0631\u0627\u0645\u062c \u062a\u0648\u0639\u064a\u0629 \u0645\u062c\u062a\u0645\u0639\u064a\u0629 \u0644\u0644\u0635\u062d\u0629 \u0627\u0644\u0648\u0642\u0627\u0626\u064a\u0629 \u0648\u0627\u0644\u0646\u0638\u0627\u0641\u0629'),
]

# ===== RECOMMENDATION ENGINE =====
USED_TEMPLATES = {}  # gov -> set of template_ids

def template_key(gov, template_id):
    if gov not in USED_TEMPLATES:
        USED_TEMPLATES[gov] = set()
    USED_TEMPLATES[gov].add(template_id)

def is_template_used(gov, template_id):
    if gov not in USED_TEMPLATES:
        return False
    # Allow up to 2 uses of same template_id per gov
    count = sum(1 for tid in USED_TEMPLATES.get(gov, set()) if tid == template_id)
    return count >= 2

def make_recs(gov, ind_key, tc, slope, cur, nat_avg, f2028, lower_b, sector, gap, local_cagr=None):
    label = INDICATORS[ind_key]['label']
    unit = INDICATORS[ind_key]['unit']
    ctx = GOV_CONTEXT.get(gov, {})
    cf = CAUSAL_FACTORS.get(gov, {})
    features = ctx.get('features', [])
    recs = []
    gap_abs = abs(gap) if gap else 0
    gap_pct_of_nat = round(gap_abs / nat_avg * 100, 1) if nat_avg and nat_avg > 0 else 0
    cagr_str = f'{abs(local_cagr)*100:.1f}%' if local_cagr else 'غير محسوب'

    if tc in ('\u062a\u0631\u0627\u062c\u0639_\u062d\u0627\u062f', '\u062a\u0631\u0627\u062c\u0639_\u0645\u0639\u062a\u062f\u0644'):
        urgency = '\u0627\u0633\u062a\u0628\u0627\u0642\u064a_\u0639\u0627\u062c\u0644' if tc == '\u062a\u0631\u0627\u062c\u0639_\u062d\u0627\u062f' else '\u062a\u062f\u062e\u0644_\u062a\u0646\u0645\u0648\u064a'
        icon = '\U0001f6a8' if tc == '\u062a\u0631\u0627\u062c\u0639_\u062d\u0627\u062f' else '\u26a0\ufe0f'

        if ind_key == '\u0627\u0644\u0628\u0637\u0627\u0644\u0629':
            tid = 'unemp_decline'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                feat = features[0] if features else '\u0627\u062d\u062a\u064a\u0627\u062c\u0627\u062a \u0627\u0644\u0633\u0648\u0642'
                action_pool = [
                    f'\u0625\u0637\u0644\u0627\u0642 \u0628\u0631\u0646\u0627\u0645\u062c \u062a\u062f\u0631\u064a\u0628 \u0645\u0647\u0646\u064a \u0645\u0643\u062b\u0641 \u0641\u064a {gov} \u0628\u0627\u0644\u062a\u0631\u0643\u064a\u0632 \u0639\u0644\u0649 {feat}',
                    '\u062a\u0641\u0639\u064a\u0644 \u062d\u0648\u0627\u0641\u0632 \u0636\u0631\u064a\u0628\u064a\u0629 \u0644\u0644\u0645\u0646\u0634\u0622\u062a \u0627\u0644\u062a\u064a \u062a\u0648\u0638\u0641 \u0645\u0646 \u0623\u0628\u0646\u0627\u0621 \u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629',
                    f'\u0625\u0646\u0634\u0627\u0621 \u0645\u0631\u0643\u0632 \u062e\u062f\u0645\u0627\u062a \u0627\u0644\u062a\u0634\u063a\u064a\u0644 \u0648\u0627\u0644\u062a\u0648\u062c\u064a\u0647 \u0627\u0644\u0645\u0647\u0646\u064a \u0641\u064a {gov}',
                    '\u0631\u0628\u0637 \u0645\u062e\u0631\u062c\u0627\u062a \u0627\u0644\u062a\u0639\u0644\u064a\u0645 \u0627\u0644\u0645\u0647\u0646\u064a \u0628\u0627\u062d\u062a\u064a\u0627\u062c\u0627\u062a \u0633\u0648\u0642 \u0627\u0644\u0639\u0645\u0644 \u0627\u0644\u0645\u062d\u0644\u064a',
                    '\u062a\u0637\u0648\u064a\u0631 \u0645\u0634\u0627\u0631\u064a\u0639 \u0631\u064a\u0627\u062f\u0629 \u0627\u0644\u0623\u0639\u0645\u0627\u0644 \u0627\u0644\u0635\u063a\u064a\u0631\u0629 \u0648\u0627\u0644\u0645\u062a\u0648\u0633\u0637\u0629',
                ]
                unemp_title = f'\u0627\u0631\u062a\u0641\u0627\u0639 \u0645\u0639\u062f\u0644 \u0627\u0644\u0628\u0637\u0627\u0644\u0629 \u0628\u0641\u062c\u0648\u0629 {gap_pct_of_nat}% \u0639\u0646 \u0627\u0644\u0648\u0637\u0646\u064a'
                if cf.get('low_participation'):
                    unemp_title = f'\u062a\u0645\u0643\u064a\u0646 \u0627\u0642\u062a\u0635\u0627\u062f\u064a \u0648\u0645\u0639\u0627\u0644\u062c\u0629 \u0627\u0644\u0641\u0642\u0631 \u0627\u0644\u0647\u064a\u0643\u0644\u064a \u0641\u064a {gov} \u2014 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%'
                causal = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(action_pool, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': unemp_title,
                    'detail': causal,
                    'actions': action_pool
                })
        elif '\u062a\u0639\u0644\u064a\u0645' in ind_key:
            level = '\u0627\u0644\u0623\u0633\u0627\u0633\u064a' if '\u0623\u0633\u0627\u0633\u064a' in ind_key else ('\u0627\u0644\u062b\u0627\u0646\u0648\u064a' if '\u062b\u0627\u0646\u0648\u064a' in ind_key else '\u0645\u0627 \u0642\u0628\u0644 \u0627\u0644\u0623\u0633\u0627\u0633\u064a')
            tid = 'edu_decline'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                edu_actions = [
                    f'\u0645\u0631\u0627\u062c\u0639\u0629 \u0623\u0633\u0628\u0627\u0628 \u0627\u0644\u062a\u0633\u0631\u0628 \u0627\u0644\u0645\u062f\u0631\u0633\u064a \u0641\u064a {gov} \u0648\u0625\u0637\u0644\u0627\u0642 \u0628\u0631\u0646\u0627\u0645\u062c \u0627\u062d\u062a\u0648\u0627\u0621',
                    '\u062a\u0639\u0632\u064a\u0632 \u0628\u0631\u0627\u0645\u062c \u0627\u0644\u0646\u0642\u0644 \u0627\u0644\u0645\u062f\u0631\u0633\u064a \u0641\u064a \u0627\u0644\u0645\u0646\u0627\u0637\u0642 \u0627\u0644\u0646\u0627\u0626\u064a\u0629',
                    '\u0625\u0637\u0644\u0627\u0642 \u062d\u0648\u0627\u0641\u0632 \u0645\u0627\u0644\u064a\u0629 \u0644\u0644\u0623\u0633\u0631 \u0644\u062a\u0634\u062c\u064a\u0639 \u0627\u0644\u0627\u0633\u062a\u0645\u0631\u0627\u0631 \u0641\u064a \u0627\u0644\u062a\u0639\u0644\u064a\u0645',
                    '\u0641\u062a\u062d \u0641\u0635\u0648\u0644 \u0645\u0633\u0627\u0626\u064a\u0629 \u0648\u0628\u062f\u064a\u0644\u0629 \u0644\u0644\u0645\u062a\u0633\u0631\u0628\u064a\u0646',
                    '\u062a\u0637\u0648\u064a\u0631 \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0644\u0644\u0645\u062f\u0627\u0631\u0633 \u0641\u064a \u0627\u0644\u0645\u0646\u0627\u0637\u0642 \u0627\u0644\u0623\u0642\u0644 \u062e\u062f\u0645\u0629'
                ]
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(edu_actions, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': f'\u062a\u0631\u0627\u062c\u0639 \u0627\u0644\u0627\u0644\u062a\u062d\u0627\u0642 \u0628\u0627\u0644\u062a\u0639\u0644\u064a\u0645 {level} \u2014 \u0646\u0633\u0628\u0629 \u0627\u0644\u0641\u062c\u0648\u0629: {gap_pct_of_nat}%',
                    'detail': cau,
                    'actions': edu_actions
                })
        elif ind_key == '\u0627\u0644\u0648\u0641\u064a\u0627\u062a':
            tid = 'deaths_increase'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                deaths_actions = [
                    '\u062a\u0639\u0632\u064a\u0632 \u0628\u0631\u0627\u0645\u062c \u0627\u0644\u0643\u0634\u0641 \u0627\u0644\u0645\u0628\u0643\u0631 \u0639\u0646 \u0627\u0644\u0623\u0645\u0631\u0627\u0636 \u0627\u0644\u0645\u0632\u0645\u0646\u0629',
                    '\u062a\u0648\u0633\u064a\u0639 \u062a\u063a\u0637\u064a\u0629 \u0627\u0644\u062a\u0623\u0645\u064a\u0646 \u0627\u0644\u0635\u062d\u064a \u0644\u0644\u0641\u0626\u0627\u062a \u0627\u0644\u0647\u0634\u0629',
                    '\u062a\u0637\u0648\u064a\u0631 \u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0637\u0648\u0627\u0631\u0626 \u0648\u0627\u0644\u0625\u0633\u0639\u0627\u0641',
                    '\u0625\u0637\u0644\u0627\u0642 \u062d\u0645\u0644\u0627\u062a \u062a\u0648\u0639\u064a\u0629 \u0635\u062d\u064a\u0629 \u0645\u062c\u062a\u0645\u0639\u064a\u0629',
                    '\u0627\u0633\u062a\u0642\u0637\u0627\u0628 \u0623\u0637\u0628\u0627\u0621 \u0645\u062a\u062e\u0635\u0635\u064a\u0646 \u0644\u0644\u0645\u062d\u0627\u0641\u0638\u0629'
                ]
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(deaths_actions, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': f'\u0627\u0631\u062a\u0641\u0627\u0639 \u0627\u0644\u0648\u0641\u064a\u0627\u062a \u0641\u064a {gov} \u2014 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%',
                    'detail': cau,
                    'actions': deaths_actions
                })
        elif ind_key == '\u0627\u0644\u0637\u0644\u0627\u0642':
            tid = 'divorce_increase'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                div_actions = [
                    '\u062a\u0641\u0639\u064a\u0644 \u0645\u0631\u0627\u0643\u0632 \u0627\u0644\u0625\u0631\u0634\u0627\u062f \u0627\u0644\u0623\u0633\u0631\u064a \u0648\u0627\u0644\u0627\u062c\u062a\u0645\u0627\u0639\u064a',
                    '\u0625\u0637\u0644\u0627\u0642 \u0628\u0631\u0627\u0645\u062c \u062f\u0639\u0645 \u0627\u0644\u0623\u0633\u0631\u0629 \u0648\u0627\u0644\u062a\u0645\u0627\u0633\u0643 \u0627\u0644\u0645\u062c\u062a\u0645\u0639\u064a',
                    '\u0645\u0639\u0627\u0644\u062c\u0629 \u0627\u0644\u0623\u0633\u0628\u0627\u0628 \u0627\u0644\u0627\u0642\u062a\u0635\u0627\u062f\u064a\u0629 (\u0627\u0644\u0628\u0637\u0627\u0644\u0629\u060c \u0627\u0644\u0641\u0642\u0631) \u0627\u0644\u0645\u0631\u062a\u0628\u0637\u0629 \u0628\u0627\u0644\u0637\u0644\u0627\u0642',
                    '\u062a\u0639\u0632\u064a\u0632 \u062f\u0648\u0631 \u0627\u0644\u062c\u0645\u0639\u064a\u0627\u062a \u0627\u0644\u062e\u064a\u0631\u064a\u0629 \u0641\u064a \u0627\u0644\u062f\u0639\u0645 \u0627\u0644\u0623\u0633\u0631\u064a'
                ]
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(div_actions, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': f'\u0627\u0631\u062a\u0641\u0627\u0639 \u062d\u0627\u0644\u0627\u062a \u0627\u0644\u0637\u0644\u0627\u0642 \u0641\u064a {gov}',
                    'detail': cau,
                    'actions': div_actions
                })
        elif ind_key in ('\u0627\u0644\u062a\u0632\u0648\u062f_\u0627\u0644\u0645\u0627\u0626\u064a', '\u062d\u0635\u0629_\u0627\u0644\u0641\u0631\u062f_\u0627\u0644\u0645\u064a\u0627\u0647'):
            tid = 'water_decline'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                w_ctx = ctx.get("water_context", "\u0638\u0631\u0648\u0641 \u0645\u0627\u0626\u064a\u0629 \u062e\u0627\u0635\u0629")
                w_actions = [
                    f'\u062a\u0637\u0648\u064a\u0631 \u0645\u0634\u0627\u0631\u064a\u0639 \u062d\u0635\u0627\u062f \u0645\u064a\u0627\u0647 \u0627\u0644\u0623\u0645\u0637\u0627\u0631 \u0641\u064a {gov} \u0627\u0633\u062a\u0646\u0627\u062f\u0627\u064b \u0644\u0640 {w_ctx}',
                    '\u0625\u0639\u0627\u062f\u0629 \u062a\u0623\u0647\u064a\u0644 \u0634\u0628\u0643\u0627\u062a \u0627\u0644\u0645\u064a\u0627\u0647 \u0627\u0644\u0642\u062f\u064a\u0645\u0629 \u0648\u0627\u0644\u0645\u062a\u0647\u0627\u0644\u0643\u0629',
                    '\u062a\u0637\u0648\u064a\u0631 \u0645\u062d\u0637\u0627\u062a \u0645\u0639\u0627\u0644\u062c\u0629 \u0627\u0644\u0645\u064a\u0627\u0647 \u0648\u0625\u0639\u0627\u062f\u0629 \u0627\u0633\u062a\u062e\u062f\u0627\u0645\u0647\u0627',
                    '\u0625\u0637\u0644\u0627\u0642 \u062d\u0645\u0644\u0627\u062a \u062a\u0631\u0634\u064a\u062f \u0627\u0633\u062a\u0647\u0644\u0627\u0643 \u0627\u0644\u0645\u064a\u0627\u0647',
                    '\u0627\u0633\u062a\u0643\u0634\u0627\u0641 \u0645\u0635\u0627\u062f\u0631 \u0645\u064a\u0627\u0647 \u062c\u0648\u0641\u064a\u0629 \u062c\u062f\u064a\u062f\u0629',
                ]
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(w_actions, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': f'\u062a\u0631\u0627\u062c\u0639 \u0641\u064a \u0645\u0624\u0634\u0631\u0627\u062a \u0627\u0644\u0645\u064a\u0627\u0647 \u0641\u064a {gov} \u2014 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%',
                    'detail': cau,
                    'actions': w_actions
                })
        elif ind_key in ('\u0625\u0646\u062a\u0627\u062c_\u0627\u0644\u0632\u064a\u062a\u0648\u0646', '\u0627\u0644\u062b\u0631\u0648\u0629_\u0627\u0644\u062d\u064a\u0648\u0627\u0646\u064a\u0629'):
            tid = 'agri_decline'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                a_ctx = ctx.get("agri_context", "\u0638\u0631\u0648\u0641 \u0632\u0631\u0627\u0639\u064a\u0629 \u0645\u062a\u0646\u0648\u0639\u0629")
                agri_actions = [
                    f'\u062a\u0642\u062f\u064a\u0645 \u062f\u0639\u0645 \u0641\u0646\u064a \u0648\u0645\u0627\u0644\u064a \u0644\u0644\u0645\u0632\u0627\u0631\u0639\u064a\u0646 \u0641\u064a {gov} \u0645\u0639 \u0645\u0631\u0627\u0639\u0627\u0629 {a_ctx}',
                    '\u062a\u0637\u0648\u064a\u0631 \u062a\u0642\u0646\u064a\u0627\u062a \u0627\u0644\u0631\u064a \u0627\u0644\u062d\u062f\u064a\u062b\u0629 \u0628\u0645\u0627 \u064a\u062a\u0646\u0627\u0633\u0628 \u0645\u0639 \u0627\u0644\u062a\u0636\u0627\u0631\u064a\u0633',
                    '\u0625\u0646\u0634\u0627\u0621 \u0645\u0631\u0627\u0643\u0632 \u062a\u062c\u0645\u064a\u0639 \u0648\u062a\u0633\u0648\u064a\u0642 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0632\u0631\u0627\u0639\u064a\u0629',
                    '\u062a\u0637\u0648\u064a\u0631 \u0628\u0631\u0627\u0645\u062c \u0627\u0644\u062a\u0623\u0645\u064a\u0646 \u0627\u0644\u0632\u0631\u0627\u0639\u064a',
                    '\u0631\u0628\u0637 \u0627\u0644\u0645\u0632\u0627\u0631\u0639\u064a\u0646 \u0628\u0627\u0644\u0623\u0633\u0648\u0627\u0642 \u0627\u0644\u0645\u062d\u0644\u064a\u0629 \u0648\u0627\u0644\u062a\u0635\u062f\u064a\u0631\u064a\u0629'
                ]
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(agri_actions, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': f'\u062a\u0631\u0627\u062c\u0639 \u0641\u064a \u0627\u0644\u0625\u0646\u062a\u0627\u062c \u0627\u0644\u0632\u0631\u0627\u0639\u064a \u0641\u064a {gov} \u2014 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%',
                    'detail': cau,
                    'actions': agri_actions
                })
        elif ind_key == '\u0627\u0644\u0633\u0643\u0627\u0646':
            tid = 'pop_decline'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                pop_actions = [
                    '\u0625\u062c\u0631\u0627\u0621 \u062f\u0631\u0627\u0633\u0629 \u062f\u064a\u0645\u0648\u063a\u0631\u0627\u0641\u064a\u0629 \u0644\u062a\u062d\u062f\u064a\u062f \u0623\u0633\u0628\u0627\u0628 \u062a\u0628\u0627\u0637\u0624 \u0627\u0644\u0646\u0645\u0648',
                    '\u062a\u0648\u0641\u064a\u0631 \u0641\u0631\u0635 \u0639\u0645\u0644 \u0645\u062d\u0644\u064a\u0629 \u0644\u062e\u0641\u0636 \u0645\u0639\u062f\u0644\u0627\u062a \u0627\u0644\u0647\u062c\u0631\u0629',
                    '\u062a\u062d\u0633\u064a\u0646 \u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0639\u0627\u0645\u0629 \u0648\u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0644\u062c\u0630\u0628 \u0627\u0644\u0633\u0643\u0627\u0646',
                    '\u0625\u0637\u0644\u0627\u0642 \u062d\u0648\u0627\u0641\u0632 \u0644\u0644\u0623\u0633\u0631 \u0627\u0644\u0634\u0627\u0628\u0629 \u0644\u0644\u0627\u0633\u062a\u0642\u0631\u0627\u0631 \u0641\u064a \u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629'
                ]
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(pop_actions, cs)
                recs.append({'type': '\u062a\u062f\u062e\u0644_\u062a\u0646\u0645\u0648\u064a', 'icon': '\u26a0\ufe0f',
                    'title': f'\u062a\u0628\u0627\u0637\u0624 \u0627\u0644\u0646\u0645\u0648 \u0627\u0644\u0633\u0643\u0627\u0646\u064a \u0641\u064a {gov}',
                    'detail': cau,
                    'actions': pop_actions
                })
        else:
            tid = 'generic_decline'
            if not is_template_used(gov, tid):
                template_key(gov, tid)
                cau = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
                gen_actions = [
                    f'\u0645\u0631\u0627\u062c\u0639\u0629 \u0627\u0644\u0633\u064a\u0627\u0633\u0627\u062a \u0627\u0644\u0642\u0637\u0627\u0639\u064a\u0629 \u0641\u064a {sector}',
                    '\u0631\u0635\u062f \u0645\u064a\u0632\u0627\u0646\u064a\u0629 \u0637\u0627\u0631\u0626\u0629 \u0644\u0645\u0639\u0627\u0644\u062c\u0629 \u0627\u0644\u062a\u0631\u0627\u062c\u0639',
                    '\u062a\u0634\u0643\u064a\u0644 \u0641\u0631\u064a\u0642 \u0639\u0645\u0644 \u0645\u062a\u062e\u0635\u0635 \u0644\u062f\u0631\u0627\u0633\u0629 \u0627\u0644\u0623\u0633\u0628\u0627\u0628',
                    '\u0648\u0636\u0639 \u0645\u0624\u0634\u0631\u0627\u062a \u0623\u062f\u0627\u0621 \u0631\u0628\u0639 \u0633\u0646\u0648\u064a\u0629 \u0644\u0644\u0645\u062a\u0627\u0628\u0639\u0629'
                ]
                cs = crisis_solutions(ind_key, cf)
                prepend_crisis_solutions(gen_actions, cs)
                recs.append({'type': urgency, 'icon': icon,
                    'title': f'\u062a\u0631\u0627\u062c\u0639 \u0641\u064a {label} \u2014 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%',
                    'detail': cau,
                    'actions': gen_actions
                })

    elif tc in ('\u062a\u062d\u0633\u0646_\u0645\u0644\u062d\u0648\u0638', '\u062a\u062d\u0633\u0646_\u062a\u062f\u0631\u064a\u062c\u064a') and gap > 5:
        tid = 'strength_invest'
        if not is_template_used(gov, tid):
            template_key(gov, tid)
            opp_actions = [
                f'\u062a\u0639\u0632\u064a\u0632 \u0627\u0644\u0627\u0633\u062a\u062b\u0645\u0627\u0631 \u0641\u064a \u0642\u0637\u0627\u0639 {sector} \u0644\u0644\u062d\u0641\u0627\u0638 \u0639\u0644\u0649 \u0627\u0644\u0631\u064a\u0627\u062f\u0629',
                f'\u062a\u062d\u0648\u064a\u0644 {gov} \u0625\u0644\u0649 \u0646\u0645\u0648\u0630\u062c \u0648\u0637\u0646\u064a \u0641\u064a {sector}',
                '\u0627\u0633\u062a\u0642\u0637\u0627\u0628 \u0627\u0633\u062a\u062b\u0645\u0627\u0631\u0627\u062a \u0625\u0636\u0627\u0641\u064a\u0629 \u062a\u0633\u062a\u0641\u064a\u062f \u0645\u0646 \u0647\u0630\u0647 \u0627\u0644\u0645\u064a\u0632\u0629',
                '\u062a\u0648\u062b\u064a\u0642 \u0623\u0633\u0628\u0627\u0628 \u0627\u0644\u0646\u062c\u0627\u062d \u0648\u0645\u0623\u0633\u0633\u062a\u0647\u0627 \u0641\u064a \u062e\u0637\u0637 \u0627\u0644\u0639\u0645\u0644'
            ]
            cs_str = crisis_solutions(ind_key, cf)
            prepend_crisis_solutions(opp_actions, cs_str)
            recs.append({'type': '\u0627\u0633\u062a\u062b\u0645\u0627\u0631_\u0645\u064a\u0632\u0629', 'icon': '\U0001f680',
                'title': f'\u0627\u0633\u062a\u062b\u0645\u0627\u0631 \u0627\u0644\u0645\u064a\u0632\u0629 \u0627\u0644\u062a\u0646\u0627\u0641\u0633\u064a\u0629 \u0641\u064a {label} \u2014 \u062a\u0642\u062f\u0645 {gap_abs:.1f} {unit}',
                'detail': f'{gov} \u062a\u062a\u0642\u062f\u0645 \u0639\u0644\u0649 \u0627\u0644\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0648\u0637\u0646\u064a \u0628ـ {gap_abs:.1f} {unit} \u0641\u064a {label} \u0628\u0646\u0633\u0628\u0629 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%. \u0627\u0644\u0627\u062a\u062c\u0627\u0647 \u0625\u064a\u062c\u0627\u0628\u064a \u0628\u0645\u0639\u062f\u0644 \u0646\u0645\u0648 {cagr_str}. \u064a\u0645\u0643\u0646 \u0627\u0633\u062a\u062b\u0645\u0627\u0631 \u0647\u0630\u0627 \u0627\u0644\u062a\u0642\u062f\u0645 \u0644\u062a\u0639\u0632\u064a\u0632 \u0627\u0644\u062a\u0646\u0645\u064a\u0629 \u0627\u0644\u0645\u062d\u0644\u064a\u0629.',
                'actions': opp_actions
            })

    elif tc == '\u0645\u0633\u062a\u0642\u0631' and gap < -5:
        tid = 'stagnant_gap'
        if not is_template_used(gov, tid):
            template_key(gov, tid)
            cau_stag = causal_detail(ind_key, gov, gap_pct_of_nat, cf, ctx.get('terrain', ''))
            stag_actions = [
                f'\u0643\u0633\u0631 \u062d\u0627\u0644\u0629 \u0627\u0644\u0631\u0643\u0648\u062f \u0628\u0645\u0628\u0627\u062f\u0631\u0629 \u062a\u0646\u0645\u0648\u064a\u0629 \u062c\u062f\u064a\u062f\u0629 \u0641\u064a {sector}',
                '\u0645\u0631\u0627\u062c\u0639\u0629 \u0627\u0644\u0639\u0648\u0627\u0626\u0642 \u0627\u0644\u0647\u064a\u0643\u0644\u064a\u0629 \u0627\u0644\u062a\u064a \u062a\u0645\u0646\u0639 \u0627\u0644\u062a\u062d\u0633\u0646',
                '\u0627\u0644\u0627\u0633\u062a\u0641\u0627\u062f\u0629 \u0645\u0646 \u062a\u062c\u0627\u0631\u0628 \u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0627\u062a \u0627\u0644\u0645\u062a\u0642\u062f\u0645\u0629 \u0641\u064a \u0647\u0630\u0627 \u0627\u0644\u0645\u0624\u0634\u0631',
                '\u062a\u062e\u0635\u064a\u0635 \u062c\u0632\u0621 \u0645\u0646 \u0627\u0644\u0645\u0648\u0627\u0632\u0646\u0629 \u0627\u0644\u0645\u062d\u0644\u064a\u0629 \u0644\u0645\u0639\u0627\u0644\u062c\u0629 \u0647\u0630\u0647 \u0627\u0644\u0641\u062c\u0648\u0629'
            ]
            cs_stag = crisis_solutions(ind_key, cf)
            prepend_crisis_solutions(stag_actions, cs_stag)
            recs.append({'type': '\u062a\u062f\u062e\u0644_\u062a\u0646\u0645\u0648\u064a', 'icon': '\U0001f527',
                'title': f'\u0631\u0643\u0648\u062f \u0645\u0639 \u0641\u062c\u0648\u0629 \u0633\u0644\u0628\u064a\u0629 \u0641\u064a {label} \u2014 \u0641\u062c\u0648\u0629 {gap_pct_of_nat}%',
                'detail': cau_stag,
                'actions': stag_actions
            })

    return recs


def merge_related_recs(recs, gov):
    """Merge recommendations from related sectors (e.g., water + agriculture)."""
    merged = []
    used_types = set()
    for s1, s2, merged_title in SECTOR_RELATIONS:
        r1 = [r for r in recs if s1 in r.get('title', '')]
        r2 = [r for r in recs if s2 in r.get('title', '')]
        if r1 and r2:
            # Remove the individual ones, add merged
            key = (s1, s2)
            if key not in used_types:
                used_types.add(key)
                ctx = GOV_CONTEXT.get(gov, {})
                cf = CAUSAL_FACTORS.get(gov, {})
                inc_ref, ref_band = refugee_band(gov)
                merged_detail = (f'يُعزى التراجع المشترك في قطاعي {s1} و{s2} في {gov} إلى تداخل عوامل '
                                 f'اقتصادية (تضخم وفقر) ')
                if inc_ref:
                    merged_detail += f'مع ضغوط ديموغرافية ناتجة عن {ref_band}'
                else:
                    merged_detail += 'مع محدودية الموارد التنموية'
                merged_detail += '، مضافاً إليها آثار التعافي البطيء من أزمة كورونا.'
                merged_actions = [
                    'تشكيل لجنة تنسيقية مشتركة بين القطاعين',
                    'تطوير خطة استثمارية متكاملة تعالج الفجوتين معاً',
                    'تعزيز شبكات الحماية الاجتماعية لمواجهة الصدمات المستقبلية',
                    'عقد ورش عمل مجتمعية بمشاركة المزارعين والمواطنين',
                    'رصد ميزانية موحدة للتدخل المشترك'
                ]
                merged.append({
                    'type': 'تدخل_تنموي',
                    'icon': '🔄',
                    'title': merged_title,
                    'detail': merged_detail,
                    'actions': merged_actions
                })
                # Remove the individual recs
                recs = [r for r in recs if r not in r1 and r not in r2]
    return merged + recs

# ===== PROCESS ALL GOVERNORATES =====
print('\nProcessing governorates...')
output_govs = {}

for gov in GOVS:
    gov_result = {
        'name': gov, 'indicators': {}, 'risk_summary': {},
        'recommendations': [], 'overall_risk_score': 0, 'trend_narrative': ''
    }
    total_risk = 0; risk_wt = 0
    all_recs = []
    sector_risks = {}

    for ind_key, ind_meta in INDICATORS.items():
        ind_data = ind_meta['data']
        if gov not in ind_data: continue
        gov_vals = ind_data[gov]
        years = ind_meta['years']
        values = [gov_vals.get(yr) for yr in years]
        valid_vals = [v for v in values if v is not None]
        if not valid_vals: continue

        cur = valid_vals[-1]
        # National average for this indicator
        nat_vals = [ind_data[g].get(years[-1]) for g in GOVS if g in ind_data and ind_data[g].get(years[-1]) is not None]
        nat_avg = round(np.mean(nat_vals), 2) if nat_vals else cur
        ind_gap = round(cur - nat_avg, 2)

        slope, r2, forecast = linear_trend(years, values)
        tc, ti = trend_class(slope, ind_meta['lower_better'], cur)
        rs = risk(tc, ind_gap)
        f2028 = forecast.get(2028, cur)

        # Compute CAGR for this indicator
        local_cagr = 0.0
        if len(valid_vals) >= 2:
            first_v = valid_vals[0]
            last_v = valid_vals[-1]
            if first_v and first_v != 0:
                local_cagr = (last_v / first_v) ** (1.0 / (len(valid_vals) - 1)) - 1

        recs = make_recs(gov, ind_key, tc, slope, cur, nat_avg, f2028, ind_meta['lower_better'], ind_meta['sector'], ind_gap, local_cagr)
        all_recs.extend(recs)

        gov_result['indicators'][ind_key] = {
            'label': ind_meta['label'], 'unit': ind_meta['unit'],
            'sector': ind_meta['sector'], 'lower_better': ind_meta['lower_better'],
            'values': {str(yr): v for yr,v in zip(years, values)},
            'current': round(cur, 2), 'national_avg': nat_avg,
            'gap': ind_gap, 'slope': slope, 'r2': r2,
            'trend_class': tc, 'trend_icon': ti, 'risk_score': rs,
            'forecast': {str(k): v for k,v in forecast.items()}
        }

        sec = ind_meta['sector']
        sector_risks.setdefault(sec, []).append(rs * ind_meta['weight'])
        total_risk += rs * ind_meta['weight']
        risk_wt += ind_meta['weight']

    overall = round(total_risk / risk_wt, 1) if risk_wt > 0 else 0
    gov_result['overall_risk_score'] = overall

    for sec, scores in sector_risks.items():
        avg = round(np.mean(scores), 1)
        level = 'عالي' if avg >= 60 else ('متوسط' if avg >= 35 else 'منخفض')
        color = '#ef4444' if avg >= 60 else ('#f59e0b' if avg >= 35 else '#22c55e')
        gov_result['risk_summary'][sec] = {'score': avg, 'level': level, 'color': color}

    # Smart merge related sector recs (e.g. water + agriculture)
    all_recs = merge_related_recs(all_recs, gov)

    priority = {'استباقي_عاجل':0,'تدخل_تنموي':1,'استثمار_ميزة':2,'تعزيز_مستمر':3}
    all_recs.sort(key=lambda r: priority.get(r['type'],9))
    gov_result['recommendations'] = all_recs[:8]

    cf_narr = CAUSAL_FACTORS.get(gov, {})
    inc_ref_narr, ref_narr = refugee_band(gov)
    urgent = [r for r in all_recs if r['type']=='استباقي_عاجل']
    invest = [r for r in all_recs if r['type']=='استثمار_ميزة']
    if urgent:
        demog_part = f"ضغوط ديموغرافية ناتجة عن {ref_narr}" if inc_ref_narr else "محدودية الموارد التنموية"
        gov_result['trend_narrative'] = f"تواجه {gov} {len(urgent)} مؤشر(ات) في مسار تراجع يستوجب تدخلاً استباقياً عاجلاً، أبرزها: {urgent[0]['title']}. تُعزى هذه الفجوات إلى تداخل عوامل اقتصادية مع {demog_part}، مضافاً إليها آثار التعافي البطيء من أزمة كورونا."
    elif invest:
        gov_result['trend_narrative'] = f"تتمتع {gov} بمؤشرات إيجابية في {len(invest)} قطاع(ات) تمثل فرصاً للاستثمار، أبرزها: {invest[0]['title']}."
    else:
        gov_result['trend_narrative'] = f"تسير {gov} في مسار تنموي مستقر مع فرص للتحسين في عدة قطاعات."

    output_govs[gov] = gov_result
    print(f'  {gov}: Risk={overall} | Indicators={len(gov_result["indicators"])} | Recs={len(all_recs)}')

# Save
output = {
    'governorates': output_govs,
    'years': [str(y) for y in [2021,2022,2023,2024,2025]],
    'forecast_years': [str(y) for y in FORECAST_YEARS],
    'indicators_meta': {k: {'label':v['label'],'unit':v['unit'],'sector':v['sector'],'lower_better':v['lower_better']} for k,v in INDICATORS.items()},
    'generated_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
}
with open('src/predictive_data.json','w',encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\nDone. predictive_data.json saved.')
print(f'Governorates: {len(output_govs)} | Indicators: {len(INDICATORS)}')
