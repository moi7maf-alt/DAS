"""
generate_data.py
Reads Excel files from Data/input/ and generates src/data.json
with composite sector scores for all 12 Jordan governorates.
"""

import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GOVERNORATES = [
    "العاصمة", "البلقاء", "الزرقاء", "مأدبا",
    "إربد", "المفرق", "جرش", "عجلون",
    "الكرك", "الطفيلة", "معان", "العقبة",
]

# Canonical name → all known variants found in the files
NAME_MAP = {
    "العاصمة": ["العاصمة", "عمان", "محافظة العاصمة", "العاصمة (عمان)"],
    "البلقاء":  ["البلقاء", "محافظة البلقاء"],
    "الزرقاء":  ["الزرقاء", "محافظة الزرقاء"],
    "مأدبا":    ["مأدبا", "مادبا", "محافظة مادبا"],
    "إربد":     ["إربد", "اربد", "محافظة إربد", "اربد"],
    "المفرق":   ["المفرق", "محافظة المفرق"],
    "جرش":      ["جرش", "محافظة جرش"],
    "عجلون":    ["عجلون", "محافظة عجلون"],
    "الكرك":    ["الكرك", "محافظة الكرك"],
    "الطفيلة":  ["الطفيلة", "محافظة الطفيلة"],
    "معان":     ["معان", "محافظة معان"],
    "العقبة":   ["العقبة", "محافظة العقبة"],
}

# Reverse lookup: variant → canonical
REVERSE_MAP = {}
for canonical, variants in NAME_MAP.items():
    for v in variants:
        REVERSE_MAP[v.strip()] = canonical

DATA_DIR = "Data/input"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_name(name):
    """Return canonical governorate name, or None if not recognised."""
    if not isinstance(name, str):
        return None
    name = name.strip()
    return REVERSE_MAP.get(name)


def safe_float(val, default=0.0):
    """Convert a value to float, returning default on failure."""
    try:
        if isinstance(val, str):
            val = val.replace("%", "").replace(",", "").strip()
        f = float(val)
        return f if np.isfinite(f) else default
    except (ValueError, TypeError):
        return default


def normalize_scores(series: pd.Series, clip: bool = True) -> pd.Series:
    """
    Winsorized Min-Max normalisation to 0-100.

    1. Clip extremes at 5th/95th percentile (Winsorization)
       to prevent outlier inflation.
    2. Min-Max scale to 0-100.
    3. All identical values → flat 50.
    """
    if clip:
        p5, p95 = series.quantile(0.05), series.quantile(0.95)
        series = series.clip(p5, p95)
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return (series - mn) / (mx - mn) * 100


def normalize_blended(series: pd.Series, pop: pd.Series, weight_abs: float = 0.75) -> pd.Series:
    """
    Blended normalisation: weighted average of absolute score (scale)
    and per-capita score (efficiency).
    Default 75-25 blend (abs-heavy) prevents small-population inflation;
    small governorates with few services get low absolute scores even
    if per-capita metrics are decent.
    """
    abs_score = normalize_scores(series)
    pc_score  = normalize_scores(series / pop.replace(0, np.nan) * 10000)
    return abs_score * weight_abs + pc_score * (1 - weight_abs)


def read_excel(filename, sheet=0):
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_excel(path, sheet_name=sheet)
    df.fillna(0, inplace=True)
    return df


def attach_canonical(df, col):
    """Add a 'canonical' column by mapping col through REVERSE_MAP."""
    df = df.copy()
    df["canonical"] = df[col].apply(normalize_name)
    return df


# ---------------------------------------------------------------------------
# Load each file
# ---------------------------------------------------------------------------

def load_master():
    df = read_excel("Governorates_Master_Base.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    return df.set_index("canonical")


def load_agriculture():
    df = read_excel("Agriculture2024.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    return df.set_index("canonical")


def load_unemployment():
    df = read_excel("Unemployment.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    # Keep only the 12 governorates (drop المملكة total row)
    df = df[df["canonical"].isin(GOVERNORATES)].copy()

    # معدل البطالة 2025 may be stored as string "21%5" for العاصمة
    col = "معدل البطالة 2025"
    df[col] = df[col].apply(lambda x: safe_float(str(x).replace("%", "").replace("5", "").strip()
                                                  if str(x).startswith("21%") else x))
    df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_health():
    df = read_excel("health.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    # Some cells contain "-" → already replaced by fillna(0) but let's be safe
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_education():
    df = read_excel("education_data.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_water():
    df = read_excel("Water and Sanitation.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical", "مستوى الضغط المائي"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_tourism():
    df = read_excel("Tourism.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_roads():
    df = read_excel("Road_Infrastructure_Length_by_Region_and_Category.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in ["طرق قروية", "طرق ثانوية", "طرق رئيسية"]:
        df[col] = df[col].apply(safe_float)
    df["total_road_length"] = df["طرق قروية"] + df["طرق ثانوية"] + df["طرق رئيسية"]
    return df.set_index("canonical")


def load_budget():
    df = read_excel("Governorate_Local_Budgets_Capital_2026.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    df["النفقات الرأسمالية 2026"] = df["النفقات الرأسمالية 2026"].apply(safe_float)
    return df.set_index("canonical")


def load_culture():
    df = read_excel("Culture_2024.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    # Total cultural centres
    df["total_culture"] = df[["المطابع", "دور النشرو التوزيع",
                               "الدعاية والإعلان", "مراكز الدراسات  والابحاث"]].sum(axis=1)
    return df.set_index("canonical")


def load_associations():
    df = read_excel("Associations.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    df["total_associations_2024"] = (
        df["الجمعيات الخيرية 2024"] +
        df["الجمعيات الثقافية 2024"] +
        df["الجمعيات البيئية 2024"]
    )
    return df.set_index("canonical")


# ---------------------------------------------------------------------------
# New data loaders — Economy, Investment & Infrastructure additions
# ---------------------------------------------------------------------------

def load_investment():
    """Investment distribution H1 2025 — total investment, employment, projects."""
    df = read_excel("Investment_Distribution_by_Standard_Governorate_Order_H1_2025..xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_economic_activity():
    """Economic participation rates — male, female, total."""
    df = read_excel("Economic_Activity_Rates.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_cooperatives():
    """Number of cooperatives by governorate 2024."""
    df = read_excel("Number_of_Cooperatives_by_Governorate_and_Kind_2024.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_postal():
    """Number of postal service centres 2024."""
    df = read_excel("Number_of_Postal_Service_Centers_by_Governorate_2024.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    df["العدد"] = df["العدد"].apply(safe_float)
    return df.set_index("canonical")


def load_road_accidents():
    """Road accidents and casualties 2024."""
    df = read_excel("Road_Accidents_by_Governorate_Type_and_Casualties_Statistics.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_poultry():
    """Poultry slaughterhouse capacity 2024."""
    df = read_excel("Actual_Production_Capacity_for_Poultry_Slaughterhouses_2024.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_agri_establishments():
    """Agricultural establishments (nurseries, exhibitions) 2024."""
    df = read_excel("Number_of_Agricultural_Establishments_2024.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    df = df[df["canonical"].isin(GOVERNORATES)].copy()
    for col in df.columns:
        if col not in ("المحافظة", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_social_dev():
    """
    Load social development indicators from NAF monthly assistance
    and Emergency aid data files.
    Returns DataFrame with aid recipient counts merged by governorate.
    Key metric: % of population receiving NAF monthly assistance.
    """
    naf = read_excel("National_Aid_Fund_NAF_Monthly_Assistance_by_Governorate.xlsx")
    naf = attach_canonical(naf, "\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629")
    naf = naf[naf["canonical"].notna()].copy()
    naf = naf[naf["canonical"].isin(GOVERNORATES)].copy()

    emergency = read_excel("SOC_DEV_Emergency_Aid_Stats_by_Region.xlsx")
    emergency = attach_canonical(emergency, "\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629")
    emergency = emergency[emergency["canonical"].notna()].copy()
    emergency = emergency[emergency["canonical"].isin(GOVERNORATES)].copy()

    df = naf.merge(emergency, on="canonical", suffixes=("_naf", "_emergency"))
    for col in df.columns:
        if col not in ("\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629_naf", "\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629_emergency", "canonical"):
            df[col] = df[col].apply(safe_float)
    return df.set_index("canonical")


def load_refugee_data():
    """Load Syrian refugee counts and percentages per governorate."""
    path = os.path.join(DATA_DIR, "Registered_Syrian_Refugees_In-Jordan-2026.xlsx")
    df = pd.read_excel(path)
    df["canonical"] = df[df.columns[0]].apply(normalize_name)
    df = df[df["canonical"].notna() & df["canonical"].isin(GOVERNORATES)].copy()
    df.set_index("canonical", inplace=True)
    return df


def load_income_distribution():
    """
    Load household income distribution and individual average income.
    Returns DataFrame with income bands as fractions.
    """
    hh = read_excel("Jordan_Household_Income_Distribution_Analysis.xlsx")
    hh = attach_canonical(hh, "\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629")
    hh = hh[hh["canonical"].notna() & hh["canonical"].isin(GOVERNORATES)].copy()
    for col in hh.columns:
        if col not in ("\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629", "canonical"):
            hh[col] = hh[col].apply(safe_float)
    hh.set_index("canonical", inplace=True)

    ind = read_excel("Jordan_Individual_Annual_Income_Analysis.xlsx")
    ind = attach_canonical(ind, "\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629")
    ind = ind[ind["canonical"].notna() & ind["canonical"].isin(GOVERNORATES)].copy()
    for col in ind.columns:
        if col not in ("\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629", "canonical"):
            ind[col] = ind[col].apply(safe_float)
    ind.set_index("canonical", inplace=True)

    # Drop overlapping columns before merge
    for df in (hh, ind):
        df.drop(columns=["\u0627\u0644\u0645\u062d\u0627\u0641\u0638\u0629"], inplace=True, errors="ignore")
    # Merge into single dataframe
    merged = hh.join(ind, how="left")
    return merged


def load_competitive_advantages():
    df = read_excel("Jordan_Governorates_Competitive_Advantages_Matrix.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    result = {}
    for _, row in df.iterrows():
        gov = row["canonical"]
        advantages = []
        for col in ["الميزة الأولى", "الميزة الثانية", "الميزة الثالثة", "الميزة الرابعة"]:
            val = str(row.get(col, "")).strip()
            if val and val != "0" and val != "nan":
                advantages.append(val)
        result[gov] = advantages
    return result


def load_tourism_attractions():
    df = read_excel("Jordan_Tourism_Attraction_Matrix.xlsx")
    df = attach_canonical(df, "المحافظة")
    df = df[df["canonical"].notna()].copy()
    result = {}
    for _, row in df.iterrows():
        gov = row["canonical"]
        attractions = []
        for col in [
            "ميزة الجذب (1): أثرية وتاريخية",
            "ميزة الجذب (2): طبيعية وبيئية",
            "ميزة الجذب (3): ترفيهية وعلاجية",
        ]:
            val = str(row.get(col, "")).strip()
            if val and val != "0" and val != "nan":
                attractions.append(val)
        result[gov] = attractions
    return result


# ---------------------------------------------------------------------------
# Sector score computation
# ---------------------------------------------------------------------------

def compute_education_scores(edu_df, pop):
    """
    Education sector — balances absolute scale with quality.
    Key ratios converted to absolute counts (teachers, sections)
    then blended so large-population governorates get fair credit.
    """
    df = edu_df.reindex(GOVERNORATES).fillna(0)
    p  = pop.reindex(GOVERNORATES).replace(0, np.nan)
    total_gov_schools = df["مدارس حكومية مملوكة"] + df["مدارس حكومية مستأجرة"]
    total_students    = df["عدد الطلبة الحكومي"] + df["عدد الطلبة الخاص"]

    # 20% — Teacher workforce: total_teachers = students / ratio (blended abs+pc)
    total_teachers = total_students / df["معدل طالب/معلم"].replace(0, np.nan)
    teachers_score = normalize_blended(total_teachers.fillna(0), p)

    # 20% — Class sections: total_sections = students / students-per-section (blended)
    total_sections = total_students / df["معدل طالب/شعبة"].replace(0, np.nan)
    sections_score = normalize_blended(total_sections.fillna(0), p)

    # 15% — Secondary enrollment rate (pure rate, Winsorized)
    enroll_sec = normalize_scores(df["نسبة الالتحاق في التعليم الثانوي"])

    # 10% — Pre-primary enrollment rate
    enroll_pre = normalize_scores(df["نسبة الالتحاق ما قبل الابتدائي"])

    # 10% — Schools (blended abs+pc)
    schools_score = normalize_blended(df["عدد المدارس الكلي"], p)

    # 15% — % double-shift schools inverted (rate-based, not absolute)
    pct_double = df["مدارس حكومية فترتين"] / total_gov_schools.replace(0, np.nan) * 100
    inv_double = normalize_scores(-pct_double.fillna(0))

    # 10% — % rented schools inverted (rate-based, not absolute)
    pct_rented = df["مدارس حكومية مستأجرة"] / total_gov_schools.replace(0, np.nan) * 100
    inv_rented = normalize_scores(-pct_rented.fillna(0))

    composite = (
        teachers_score * 0.20 +
        sections_score * 0.20 +
        enroll_sec     * 0.15 +
        enroll_pre     * 0.10 +
        schools_score  * 0.10 +
        inv_double     * 0.15 +
        inv_rented     * 0.10
    )
    return composite


def compute_health_scores(health_df, pop):
    """
    Health sector — balances absolute scale with per-capita access.
    Most components use blended abs+pc so large-population governorates
    with larger health workforces and infrastructure get fair credit.
    """
    df = health_df.reindex(GOVERNORATES).fillna(0)
    p  = pop.reindex(GOVERNORATES).replace(0, np.nan)

    # 25% — Specialist doctors (blended abs+pc)
    specialists = normalize_blended(df["أطباء الاختصاص بوزارة الصحة"], p)

    # 15% — Nurses (blended abs+pc)
    nurses = normalize_blended(df["ممرضون وممرضات في وزارة الصحة"], p)

    # 15% — Total hospitals (blended abs+pc)
    hospitals = normalize_blended(df["إجمالي المستشفيات"], p)

    # 15% — Beds per 10k (pure rate, Winsorized — already per‑capita)
    beds_pc = normalize_scores(df["الأسرّة في المستشفيات  لكل 10,000 مواطن"])

    # 10% — Pharmacies (blended abs+pc)
    pharmacies = normalize_blended(df["عدد الصيدليات"], p)

    # 10% — Private hospital beds (blended abs+pc)
    private_beds = normalize_blended(df["عدد أسرة المستشفيات في القطاع الخاص "], p)

    # 10% — Medicine factories (absolute — industrial depth)
    pharma_factories = normalize_scores(df["عدد مصانع الأدوية"])

    composite = (
        specialists      * 0.25 +
        nurses           * 0.15 +
        hospitals        * 0.15 +
        beds_pc          * 0.15 +
        pharmacies       * 0.10 +
        private_beds     * 0.10 +
        pharma_factories * 0.10
    )
    return composite


def compute_tourism_scores(tourism_df, pop):
    """
    Tourism employment (50-50 blend), hotels (50-50 blend).
    Blend of absolute (tourist scale) + per-capita (access per resident).
    """
    df = tourism_df.reindex(GOVERNORATES).fillna(0)
    p  = pop.reindex(GOVERNORATES).replace(0, np.nan)

    employment  = normalize_blended(df["مجموع العمالة"], p)
    hotels      = normalize_blended(df["الفنادق"], p)

    composite = (employment + hotels) / 2
    return composite


def compute_water_scores(water_df):
    """
    Water per capita (litres/day), sanitation network %.
    """
    df = water_df.reindex(GOVERNORATES).fillna(0)

    water_pc    = normalize_scores(df["حصة الفرد من المياه (لتر/يوم) 2024"])
    sanitation  = normalize_scores(df["نسبة استخدام خدمات شبكة الصرف الصحي"])

    composite = (water_pc + sanitation) / 2
    return composite


def compute_agriculture_scores_v2(agri_df, poultry_df, agri_est_df, pop):
    """
    Agricultural workers, livestock, irrigated area, poultry capacity,
    agri establishments — all 50-50 blend of absolute + per-capita.
    """
    df      = agri_df.reindex(GOVERNORATES).fillna(0)
    poultry = poultry_df.reindex(GOVERNORATES).fillna(0)
    est     = agri_est_df.reindex(GOVERNORATES).fillna(0)
    p       = pop.reindex(GOVERNORATES).replace(0, np.nan)

    workers      = normalize_blended(df["العمال الأردنييون العاملون في الزراعة "], p)
    livestock    = normalize_blended(df["إجمالي الثروة الحيوانية"], p)
    irrigated    = normalize_blended(df["مساحة الزراعة  المروية سطحي"], p)
    poultry_cap  = normalize_blended(poultry["عدد الطيور اللاحم"], p)
    agri_est_tot = normalize_blended(est["المجموع الكلي"], p)

    composite = (workers + livestock + irrigated + poultry_cap + agri_est_tot) / 5
    return composite


def compute_infrastructure_scores_v2(roads_df, master_df, postal_df, accidents_df):
    """
    Road length (50-50 blend), postal centres (50-50 blend),
    road safety (per-capita, inverted).
    """
    roads   = roads_df.reindex(GOVERNORATES).fillna(0)
    postal  = postal_df.reindex(GOVERNORATES).fillna(0)
    acc     = accidents_df.reindex(GOVERNORATES).fillna(0)
    pop     = master_df.reindex(GOVERNORATES)["السكان"].apply(safe_float).replace(0, np.nan)

    road_score      = normalize_blended(roads["total_road_length"], pop)
    postal_score    = normalize_blended(postal["العدد"], pop)
    # Road safety: fewer casualties per capita = better (inverted)
    casualties_pc   = acc["مجموع عدد المتضررين من حوادث الطرق 2024"] / pop.fillna(1) * 10000
    safety_score    = 100 - normalize_scores(casualties_pc.fillna(0))

    composite = (road_score + postal_score + safety_score) / 3
    return composite


def compute_economy_scores_v2(invest_df, econ_df, unemp_df, income_df):
    """
    المؤشرات الاقتصادية (Economic Indicators) sector score.

    المنهجية:
    - البطالة (معكوسة) — 10%: وزن منخفض لأن معدلات البطالة المرتفعة
      في المدن الصناعية تعكس كثافة سوق العمل لا ضعف الاقتصاد
    - الاستثمار + العمالة — 50%: مؤشر الجاذبية الاستثمارية (جذر تربيعي
      لتقليص هيمنة العاصمة)
    - متوسط الدخل الفردي — 40%: مؤشر الرفاه الاقتصادي
    """
    inv    = invest_df.reindex(GOVERNORATES).fillna(0)
    econ   = econ_df.reindex(GOVERNORATES).fillna(0)
    unemp  = unemp_df.reindex(GOVERNORATES).fillna(0)
    income = income_df.reindex(GOVERNORATES).fillna(0)

    inv_col  = "حجم الاستثمار الكلي المتوقع*"
    econ_col = "مجموع معدلات المشاركة الاقتصادية المنقحة للأردنيين (15 سنة فأكثر)"
    fem_col  = "معدلات المشاركة الاقتصادية المنقحة للأردنيين (15 سنة فأكثر) إناث"
    jobs_col = "حجم العمالة المتوقع"
    inc_col  = "متوسط إجمالي الدخل لأفراد الأسرة"

    # 10%: Inverted unemployment rate
    unemp_rate = unemp["معدل البطالة 2025"].apply(safe_float)
    unemp_score = 100 - normalize_scores(unemp_rate)

    # 50%: Investment + jobs composite (sqrt transform to compress capital dominance)
    total_invest = inv[inv_col].sum()
    raw_share = inv[inv_col] / total_invest * 100 if total_invest > 0 else inv[inv_col]
    invest_score = normalize_scores(np.sqrt(raw_share.clip(0)))

    total_jobs = inv[jobs_col].sum()
    raw_job_share = inv[jobs_col] / total_jobs * 100 if total_jobs > 0 else inv[jobs_col]
    jobs_score = normalize_scores(np.sqrt(raw_job_share.clip(0)))

    invest_composite = (invest_score + jobs_score) / 2

    # 40%: Average individual income
    income_score = normalize_scores(income[inc_col])

    composite = (
        unemp_score      * 0.10 +
        invest_composite * 0.50 +
        income_score     * 0.40
    )

    return composite


def compute_social_dev_scores(social_dev_df, master_df):
    """
    Social Development sector score.

    \u0627\u0644\u0645\u0646\u0647\u062c\u064a\u0629:
    - \u0646\u0633\u0628\u0629 \u0627\u0644\u0623\u0641\u0631\u0627\u062f \u0627\u0644\u0630\u064a\u0646 \u064a\u062a\u0644\u0642\u0648\u0646 \u0645\u0639\u0648\u0646\u0627\u062a \u0634\u0647\u0631\u064a\u0629 (\u0645\u0646 \u0635\u0646\u062f\u0648\u0642 \u0627\u0644\u0645\u0639\u0648\u0646\u0629 \u0627\u0644\u0648\u0637\u0646\u064a\u0629) \u0645\u0642\u0633\u0648\u0645\u0629 \u0639\u0644\u0649 \u0639\u062f\u062f \u0627\u0644\u0633\u0643\u0627\u0646
    - \u0646\u0633\u0628\u0629 \u0627\u0644\u0623\u0633\u0631 \u0627\u0644\u062a\u064a \u062a\u0644\u0642\u062a \u0645\u0639\u0648\u0646\u0627\u062a \u0637\u0627\u0631\u0626\u0629

    Lower dependency on aid = higher score (better social development).
    """
    df = social_dev_df.reindex(GOVERNORATES).fillna(0)
    pop = master_df.reindex(GOVERNORATES)["\u0627\u0644\u0633\u0643\u0627\u0646"].apply(safe_float).replace(0, np.nan)

    # Primary: % of population receiving NAF monthly assistance (lower = better)
    aid_pct = df["\u0639\u062f\u062f \u0627\u0644\u0623\u0641\u0631\u0627\u062f"] / pop * 100
    score_naf = 100 - normalize_scores(aid_pct.fillna(0))

    # Secondary: % receiving emergency aid (lower = better)
    emergency_pct = df["\u0639\u062f\u062f \u0627\u0644\u0623\u0633\u0631 \u0627\u0644\u062a\u064a \u062a\u0644\u0642\u062a \u0645\u0639\u0648\u0646\u0627\u062a \u0637\u0627\u0631\u0626\u0629"] / pop * 100
    score_emergency = 100 - normalize_scores(emergency_pct.fillna(0))

    composite = (score_naf + score_emergency) / 2
    return composite


# ---------------------------------------------------------------------------
# Status helper
# ---------------------------------------------------------------------------

def compute_status(gap: float, std: float) -> str:
    """
    3 فئات فقط:
    - متقدم:  gap > +0.5 * std
    - متوسط: -0.5 * std ≤ gap ≤ +0.5 * std
    - متأخر: gap < -0.5 * std
    """
    if std == 0:
        return "متوسط"
    if gap > 0.5 * std:
        return "متقدم"
    elif gap < -0.5 * std:
        return "متأخر"
    return "متوسط"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data files...")

    master      = load_master()
    agri        = load_agriculture()
    unemp       = load_unemployment()
    health      = load_health()
    edu         = load_education()
    water       = load_water()
    tourism     = load_tourism()
    roads       = load_roads()
    budget      = load_budget()
    culture     = load_culture()
    assoc       = load_associations()
    comp_adv    = load_competitive_advantages()
    tour_attr   = load_tourism_attractions()
    # New files
    invest      = load_investment()
    econ        = load_economic_activity()
    coop        = load_cooperatives()
    postal      = load_postal()
    accidents   = load_road_accidents()
    poultry     = load_poultry()
    agri_est    = load_agri_establishments()
    social_dev  = load_social_dev()
    refugee     = load_refugee_data()
    income      = load_income_distribution()

    # ---- Population vector ----
    pop_series  = master.reindex(GOVERNORATES)["السكان"].apply(safe_float).replace(0, np.nan)

    print("Computing sector scores...")

    sector_scores = {
        "التعليم":              compute_education_scores(edu, pop_series),
        "الصحة":                compute_health_scores(health, pop_series),
        "الزراعة":              compute_agriculture_scores_v2(agri, poultry, agri_est, pop_series),
        "السياحة":              compute_tourism_scores(tourism, pop_series),
        "البنية التحتية":       compute_infrastructure_scores_v2(roads, master, postal, accidents),
        "المياه والصرف الصحي":  compute_water_scores(water),
        "التنمية الاجتماعية":   compute_social_dev_scores(social_dev, master),
        "المؤشرات الاقتصادية":  compute_economy_scores_v2(invest, econ, unemp, income),
    }

    # الأوزان — الاقتصاد + التعليم + الصحة هي الأعلى وزنًا
    SECTOR_WEIGHTS = {
        "المؤشرات الاقتصادية":  0.30,
        "البنية التحتية":       0.15,
        "التعليم":              0.15,
        "الصحة":                0.15,
        "المياه والصرف الصحي":  0.08,
        "الزراعة":              0.07,
        "السياحة":              0.05,
        "التنمية الاجتماعية":   0.05,
    }

    # المتوسطات الوطنية — متوسط بسيط (غير مرجح سكانيًا)
    national_averages = {
        sector: round(float(scores.mean()), 2)
        for sector, scores in sector_scores.items()
    }

    # ---- المؤشر التنموي المركب ----
    composite_index = pd.Series(0.0, index=GOVERNORATES)
    for sector, weight in SECTOR_WEIGHTS.items():
        composite_index += sector_scores[sector] * weight
    composite_avg = round(float(composite_index.mean()), 2)
    composite_std = float(composite_index.std())

    print("Building governorate records...")

    governorates_list = []

    for gov in GOVERNORATES:
        # ---- Basic info ----
        gov_pop = int(safe_float(master.at[gov, "السكان"]))          if gov in master.index  else 0
        area    = safe_float(master.at[gov, "المساحة (كم2)"])        if gov in master.index  else 0.0
        bud     = safe_float(budget.at[gov, "النفقات الرأسمالية 2026"]) if gov in budget.index else 0.0

        # ---- Sectors ----
        sectors = {}
        for sector, scores in sector_scores.items():
            score      = round(float(scores.get(gov, 0.0)), 2)
            nat_avg    = national_averages[sector]
            gap        = round(score - nat_avg, 2)
            std_val    = float(sector_scores[sector].std())
            status     = compute_status(gap, std_val)
            sectors[sector] = {
                "score":        score,
                "national_avg": nat_avg,
                "gap":          gap,
                "status":       status,
            }

        # ---- Composite index ----
        comp_score = round(float(composite_index.get(gov, 0.0)), 2)

        # ---- Raw data ----
        raw_data = {}

        if gov in edu.index:
            raw_data["total_schools"]             = int(safe_float(edu.at[gov, "عدد المدارس الكلي"]))
            raw_data["total_students_gov"]        = int(safe_float(edu.at[gov, "عدد الطلبة الحكومي"]))
            raw_data["total_students_private"]    = int(safe_float(edu.at[gov, "عدد الطلبة الخاص"]))
            raw_data["schools_gov_owned"]         = int(safe_float(edu.at[gov, "مدارس حكومية مملوكة"]))
            raw_data["schools_gov_rented"]        = int(safe_float(edu.at[gov, "مدارس حكومية مستأجرة"]))
            raw_data["schools_gov_single_shift"]  = int(safe_float(edu.at[gov, "مدارس حكومية فترة واحدة"]))
            raw_data["schools_gov_double_shift"]  = int(safe_float(edu.at[gov, "مدارس حكومية فترتين"]))
            raw_data["students_per_section"]       = safe_float(edu.at[gov, "معدل طالب/شعبة"])
            raw_data["student_teacher_ratio"]      = safe_float(edu.at[gov, "معدل طالب/معلم"])
            raw_data["enrollment_secondary"]       = safe_float(edu.at[gov, "نسبة الالتحاق في التعليم الثانوي"])
            raw_data["enrollment_pre"]             = safe_float(edu.at[gov, "نسبة الالتحاق ما قبل الابتدائي"])

        if gov in health.index:
            raw_data["total_hospitals"]     = int(safe_float(health.at[gov, "إجمالي المستشفيات"]))
            raw_data["total_beds"]          = int(safe_float(health.at[gov, "إجمالي الأسرّة في المستشفيات"]))
            raw_data["beds_per_10k"]        = safe_float(health.at[gov, "الأسرّة في المستشفيات  لكل 10,000 مواطن"])
            raw_data["health_centers"]      = int(safe_float(health.at[gov, "المراكز الصحية"]))
            raw_data["specialist_doctors"]  = int(safe_float(health.at[gov, "أطباء الاختصاص بوزارة الصحة"]))
            raw_data["general_doctors"]     = int(safe_float(health.at[gov, "أطباء عامون في وزارة الصحة"]))
            raw_data["nurses"]              = int(safe_float(health.at[gov, "ممرضون وممرضات في وزارة الصحة"]))
            raw_data["pharmacies"]          = int(safe_float(health.at[gov, "عدد الصيدليات"]))
            raw_data["private_hospital_beds"] = int(safe_float(health.at[gov, "عدد أسرة المستشفيات في القطاع الخاص "]))
            raw_data["pharma_factories"]    = int(safe_float(health.at[gov, "عدد مصانع الأدوية"]))

        if gov in agri.index:
            raw_data["agri_workers"]        = int(safe_float(agri.at[gov, "العمال الأردنييون العاملون في الزراعة "]))
            raw_data["total_livestock"]     = int(safe_float(agri.at[gov, "إجمالي الثروة الحيوانية"]))
            raw_data["irrigated_area_dunum"]= safe_float(agri.at[gov, "مساحة الزراعة  المروية سطحي"])

        if gov in tourism.index:
            raw_data["tourism_employment"]  = int(safe_float(tourism.at[gov, "مجموع العمالة"]))
            raw_data["hotels"]              = int(safe_float(tourism.at[gov, "الفنادق"]))

        if gov in roads.index:
            raw_data["total_road_km"]       = safe_float(roads.at[gov, "total_road_length"])

        if gov in water.index:
            raw_data["water_per_capita_lpd"]= safe_float(water.at[gov, "حصة الفرد من المياه (لتر/يوم) 2024"])
            raw_data["sanitation_network_pct"]= safe_float(water.at[gov, "نسبة استخدام خدمات شبكة الصرف الصحي"])

        if gov in assoc.index:
            raw_data["total_associations_2024"]= int(safe_float(assoc.at[gov, "total_associations_2024"]))

        if gov in culture.index:
            raw_data["cultural_centers"]    = int(safe_float(culture.at[gov, "total_culture"]))

        # New raw indicators
        if gov in invest.index:
            raw_data["total_investment_m"]  = safe_float(invest.at[gov, "حجم الاستثمار الكلي المتوقع*"])
            raw_data["investment_jobs"]     = int(safe_float(invest.at[gov, "حجم العمالة المتوقع"]))
            raw_data["investment_projects"] = int(safe_float(invest.at[gov, "عدد المشاريع المستفيدة  من قانون البيئة االاستثمارية خلال النصف الأول من العام 2025"]))

        if gov in econ.index:
            raw_data["econ_participation_total"]  = safe_float(econ.at[gov, "مجموع معدلات المشاركة الاقتصادية المنقحة للأردنيين (15 سنة فأكثر)"])
            raw_data["econ_participation_female"] = safe_float(econ.at[gov, "معدلات المشاركة الاقتصادية المنقحة للأردنيين (15 سنة فأكثر) إناث"])
            raw_data["econ_participation_male"]   = safe_float(econ.at[gov, "معدلات المشاركة الاقتصادية المنقحة للأردنيين (15 سنة فأكثر) ذكور "])

        if gov in coop.index:
            raw_data["total_cooperatives"]  = int(safe_float(coop.at[gov, "المجموع"]))

        if gov in postal.index:
            raw_data["postal_centers"]      = int(safe_float(postal.at[gov, "العدد"]))

        if gov in accidents.index:
            raw_data["road_accidents_2024"] = int(safe_float(accidents.at[gov, "مجموع عدد حوادث السيارات 2024"]))
            raw_data["road_casualties_2024"]= int(safe_float(accidents.at[gov, "مجموع عدد المتضررين من حوادث الطرق 2024"]))
            raw_data["road_fatalities_2024"]= int(safe_float(accidents.at[gov, "عدد قتلى حوادث السيارات "]))

        if gov in poultry.index:
            raw_data["poultry_capacity"]    = int(safe_float(poultry.at[gov, "عدد الطيور اللاحم"]))
            raw_data["poultry_slaughterhouses"] = int(safe_float(poultry.at[gov, "عدد المسالخ المرخصة"]))

        if gov in social_dev.index:
            raw_data["naf_households"]     = int(safe_float(social_dev.at[gov, "عدد الأسر"]))
            raw_data["naf_individuals"]    = int(safe_float(social_dev.at[gov, "عدد الأفراد"]))
            raw_data["naf_monthly_amount"] = safe_float(social_dev.at[gov, "مبلغ المعونة الشهرية"])
            raw_data["emergency_households"] = int(safe_float(social_dev.at[gov, "عدد الأسر التي تلقت معونات طارئة"]))
            raw_data["emergency_amount"]   = safe_float(social_dev.at[gov, "المعونة الطارئة المقدمة للأسر المحتاجة بالدينار"])
            naf_indiv = safe_float(social_dev.at[gov, "عدد الأفراد"])
            raw_data["aid_pct"] = round(naf_indiv / gov_pop * 100, 2) if gov_pop > 0 else 0

        if gov in agri_est.index:
            raw_data["agri_establishments"] = int(safe_float(agri_est.at[gov, "المجموع الكلي"]))
            raw_data["agri_nurseries"]      = int(safe_float(agri_est.at[gov, "مجموع المشاتل"]))

        # ---- Contextual Drivers (not sectors, used for causal explanation) ----
        contextual_drivers = {}
        if gov in unemp.index:
            contextual_drivers["unemployment_rate"] = safe_float(unemp.at[gov, "\u0645\u0639\u062f\u0644 \u0627\u0644\u0628\u0637\u0627\u0644\u0629 2025"])
        if gov in master.index:
            contextual_drivers["population_density"] = safe_float(master.at[gov, "\u0627\u0644\u0643\u062b\u0627\u0641\u0629 \u0627\u0644\u0633\u0643\u0627\u0646\u064a\u0629"])
        if gov in refugee.index:
            contextual_drivers["refugee_count"] = int(safe_float(refugee.at[gov, refugee.columns[1]]))
            contextual_drivers["refugee_pct"] = round(safe_float(refugee.at[gov, refugee.columns[2]]) * 100, 2)
        if gov in income.index:
            contextual_drivers["avg_individual_income"] = safe_float(income.at[gov, "\u0645\u062a\u0648\u0633\u0637 \u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u062f\u062e\u0644 \u0644\u0623\u0641\u0631\u0627\u062f \u0627\u0644\u0623\u0633\u0631\u0629"])
            contextual_drivers["low_income_pct"] = round(safe_float(income.at[gov, "\u0627\u0644\u0623\u0633\u0631 \u0630\u0627\u062a \u0627\u0644\u062f\u062e\u0644 \u0627\u0644\u0633\u0646\u0648\u064a \u0627\u0644\u0645\u062a\u062f\u0646\u064a  \u0627\u0642\u0644 \u0645\u0646 5000 \u0633\u0646\u0648\u064a\u0627\u064b"]) * 100, 1)
            contextual_drivers["medium_income_pct"] = round(safe_float(income.at[gov, "\u0627\u0644\u0623\u0633\u0631 \u0630\u0627\u062a \u0627\u0644\u062f\u062e\u0644 \u0627\u0644\u0645\u062a\u0648\u0633\u0637 \u0645\u0646 5000 \u0625\u0644\u0649 12500 \u0633\u0646\u0648\u064a\u0627\u064b"]) * 100, 1)
            contextual_drivers["high_income_pct"] = round(safe_float(income.at[gov, "\u0627\u0644\u0623\u0633\u0631 \u0630\u0627\u062a \u0627\u0644\u062f\u062e\u0644 \u0627\u0644\u0645\u0631\u062a\u0641\u0639  \u0627\u0643\u062b\u0631 \u0645\u0646 12500"]) * 100, 1)
        if gov in econ.index:
            contextual_drivers["econ_participation_total"] = safe_float(econ.at[gov, "\u0645\u062c\u0645\u0648\u0639 \u0645\u0639\u062f\u0644\u0627\u062a \u0627\u0644\u0645\u0634\u0627\u0631\u0643\u0629 \u0627\u0644\u0627\u0642\u062a\u0635\u0627\u062f\u064a\u0629 \u0627\u0644\u0645\u0646\u0642\u062d\u0629 \u0644\u0644\u0623\u0631\u062f\u0646\u064a\u064a\u0646 (15 \u0633\u0646\u0629 \u0641\u0623\u0643\u062b\u0631)"])
            contextual_drivers["econ_participation_female"] = safe_float(econ.at[gov, "\u0645\u0639\u062f\u0644\u0627\u062a \u0627\u0644\u0645\u0634\u0627\u0631\u0643\u0629 \u0627\u0644\u0627\u0642\u062a\u0635\u0627\u062f\u064a\u0629 \u0627\u0644\u0645\u0646\u0642\u062d\u0629 \u0644\u0644\u0623\u0631\u062f\u0646\u064a\u064a\u0646 (15 \u0633\u0646\u0629 \u0641\u0623\u0643\u062b\u0631) \u0625\u0646\u0627\u062b"])
        if gov in social_dev.index:
            contextual_drivers["aid_recipient_pct"] = round(safe_float(social_dev.at[gov, "\u0639\u062f\u062f \u0627\u0644\u0623\u0641\u0631\u0627\u062f"]) / gov_pop * 100, 2) if gov_pop > 0 else 0

        # ---- Aggregated sectors for display ----
        adv_count = sum(1 for s in sectors.values() if s['status'] == 'متقدم')
        beh_count = sum(1 for s in sectors.values() if s['status'] == 'متأخر')

        governorates_list.append({
            "name":                  gov,
            "population":            gov_pop,
            "area":                  area,
            "budget_2026":           bud,
            "sectors":               sectors,
            "composite_index":       comp_score,
            "adv_sectors":           adv_count,
            "beh_sectors":           beh_count,
            "contextual_drivers":    contextual_drivers,
            "competitive_advantages": comp_adv.get(gov, []),
            "tourism_attractions":   tour_attr.get(gov, []),
            "raw_data":              raw_data,
        })

    # Sector-level standard deviations for reference
    sector_stds = {
        sector: round(float(scores.std()), 2)
        for sector, scores in sector_scores.items()
    }

    output = {
        "governorates":      governorates_list,
        "national_averages": national_averages,
        "composite_index":   {
            "national_avg":   composite_avg,
            "national_std":   round(composite_std, 2),
            "sector_weights": SECTOR_WEIGHTS,
        },
        "metadata": {
            "generated_at":  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_govs":    len(governorates_list),
            "methodology":  "Winsorized Min-Max 5-95% | Quantity: blended 75%abs+25%pc | Quality/access: pc or % weighted by sector | Economic 20% / Edu 18% / Health 18% / Infra 14% / Water 12% / SocDev 8% / Agri 7% / Tourism 3% | Simple natl avg | 3-status",
        },
    }

    out_path = os.path.join("src", "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Done. Written to {out_path}")
    print(f"  Governorates: {len(governorates_list)}")
    print(f"  National averages: OK ({len(national_averages)} sectors)")


if __name__ == "__main__":
    main()
