import json, os, re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════
# CHEMINS — automatiques, compatibles Windows/Linux
# ══════════════════════════════════════════════════
BASE      = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_LAKE = BASE / "data_lake"

OFFRES_JSON      = BASE / "offres_emploi_it_maroc.json"
REFERENTIEL_JSON = BASE / "referentiel_competences_it.json"

# ══════════════════════════════════════════════════
# BRONZE
# ══════════════════════════════════════════════════
def ingerer_bronze(filepath_source, data_lake_root):
    filepath_source = Path(filepath_source)
    data_lake_root  = Path(data_lake_root)

    with open(filepath_source, 'r', encoding='utf-8') as f:
        data = json.load(f)
    offres = data.get('offres', [])

    partitions = {}
    for offre in offres:
        source   = offre.get('source', 'inconnu').lower().replace(' ', '_')
        date_pub = offre.get('date_publication', '')
        try:
            mois_partition = datetime.strptime(date_pub[:7], '%Y-%m').strftime('%Y_%m')
        except Exception:
            mois_partition = 'date_inconnue'
        cle = f"{source}/{mois_partition}"
        partitions.setdefault(cle, []).append(offre)

    for partition, offres_p in partitions.items():
        chemin_dir = data_lake_root / 'bronze' / Path(partition)
        chemin_dir.mkdir(parents=True, exist_ok=True)
        with open(chemin_dir / 'offres_raw.json', 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'source_fichier': str(filepath_source),
                    'date_ingestion': datetime.now().isoformat(),
                    'partition': partition,
                    'nb_offres': len(offres_p)
                },
                'offres': offres_p
            }, f, ensure_ascii=False, indent=2)

    print(f"[BRONZE] {len(offres)} offres → {len(partitions)} partitions")
    return len(offres)

# ══════════════════════════════════════════════════
# SILVER — Nettoyage
# ══════════════════════════════════════════════════
def charger_bronze(data_lake_root):
    data_lake_root = Path(data_lake_root)
    all_offres = []
    for json_file in (data_lake_root / 'bronze').rglob('offres_raw.json'):
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)
        all_offres.extend(data.get('offres', []))
    df = pd.DataFrame(all_offres)
    print(f"[SILVER] {len(df)} offres chargées depuis Bronze")
    return df

def normaliser_villes(df):
    mapping = {
        r'casablanca|^casa$': 'Casablanca',
        r'^rabat':            'Rabat',
        r'^tanger':           'Tanger',
        r'^marrakech':        'Marrakech',
        r'^f[eè]s?$':        'Fès',
        r'^agadir':           'Agadir',
        r'^oujda':            'Oujda',
        r'^mekn':             'Meknès',
        r'^kenitra':          'Kénitra',
        r'^t[eé]touan':      'Tétouan',
    }
    region = {
        'Casablanca': 'Grand Casablanca-Settat',
        'Rabat':      'Rabat-Salé-Kénitra',
        'Tanger':     'Tanger-Tétouan-Al Hoceima',
        'Marrakech':  'Marrakech-Safi',
        'Fès':        'Fès-Meknès',
        'Agadir':     'Souss-Massa',
        'Oujda':      'Oriental',
        'Meknès':     'Fès-Meknès',
        'Kénitra':    'Rabat-Salé-Kénitra',
        'Tétouan':    'Tanger-Tétouan-Al Hoceima',
    }
    def mapper(v):
        if pd.isna(v): return 'Autre', 'Inconnue'
        v2 = str(v).strip().lower()
        for pat, std in mapping.items():
            if re.search(pat, v2):
                return std, region.get(std, 'Autre')
        return str(v).strip().title(), 'Autre'
    df[['ville_std', 'region_admin']] = pd.DataFrame(
        df['ville'].apply(mapper).tolist(), index=df.index
    )
    return df

def normaliser_contrats(df):
    def mapper(v):
        if pd.isna(v): return 'Non précisé'
        v2 = str(v).lower()
        if re.search(r'cdi|indéterminée|permanent',    v2): return 'CDI'
        if re.search(r'cdd|déterminée|temporaire',     v2): return 'CDD'
        if re.search(r'freelance|indépendant|mission',  v2): return 'Freelance'
        if re.search(r'stage|intern|pfe',               v2): return 'Stage'
        return str(v).strip()
    df['type_contrat_std'] = df['type_contrat'].apply(mapper)
    return df

def normaliser_titres(df):
    mapping = {
        r'data\s*eng|ingénieur\s+data|dev\s+data|etl\s*dev|pipeline\s*dev|big\s*data': 'Data Engineer',
        r'data\s*anal|analyste?\s+data|bi\s+anal|business\s+intel|reporting\s+anal|ingénieur\s+bi|développeur\s+bi': 'Data Analyst',
        r'data\s*sci|machine\s*learn|ml\s*eng|ia\s*eng|deep\s*learn|nlp\s*eng': 'Data Scientist',
        r'full\s*stack|fullstack':                     'Développeur Full Stack',
        r'back[\s-]*end|backend':                      'Développeur Backend',
        r'front[\s-]*end|frontend':                    'Développeur Frontend',
        r'devops|sre|site\s*reliab':                   'DevOps / SRE',
        r'cloud\s*(arch|eng|admin)|aws\s+eng|gcp\s+eng|azure\s+eng': 'Cloud Engineer',
        r'cyber|sécurité\s+info|pentester|soc\s+anal': 'Cybersécurité',
        r'chef\s+de\s+proj|project\s+man|scrum\s*master': 'Chef de Projet IT',
        r'architect': 'Architecte IT',
    }
    df['profil_normalise'] = 'Autre IT'
    src = df['titre_poste'].str.lower().str.strip().fillna('')
    for pat, profil in mapping.items():
        mask = src.str.contains(pat, regex=True, na=False)
        df.loc[mask & (df['profil_normalise'] == 'Autre IT'), 'profil_normalise'] = profil
    return df

def normaliser_salaires(df):
    TAUX = 10.8
    def parser(v):
        if pd.isna(v) or str(v).lower() in ['null', 'confidentiel', 'selon profil', '']:
            return None, None, False
        s = str(v).lower().replace(' ', '').replace('\u202f', '')
        est_eur = 'eur' in s or '€' in s
        s = re.sub(r'[a-z€]', '', s)
        s = re.sub(r'(\d+(?:\.\d+)?)k',
                   lambda m: str(int(float(m.group(1)) * 1000)), s)
        nombres = re.findall(r'\d+(?:\.\d+)?', s)
        if not nombres: return None, None, False
        montants = [float(n) for n in nombres]
        if est_eur: montants = [m * TAUX for m in montants]
        if len(montants) >= 2:
            mn, mx = min(montants[:2]), max(montants[:2])
        else:
            mn = mx = montants[0]
        if mn < 3000 or mx > 100000: return None, None, False
        return mn, mx, True
    res = df['salaire_brut'].apply(
        lambda x: pd.Series(parser(x),
                             index=['salaire_min_mad', 'salaire_max_mad', 'salaire_connu'])
    )
    df = pd.concat([df, res], axis=1)
    df['salaire_median_mad'] = (df['salaire_min_mad'] + df['salaire_max_mad']) / 2
    print(f"[SILVER] Salaires : {df['salaire_connu'].mean()*100:.1f}% renseignés")
    return df

def normaliser_experience(df):
    def parser(v):
        if pd.isna(v): return None, None
        s = str(v).lower()
        if any(m in s for m in ['débutant', 'junior', 'stage', 'sans expérience']): return 0, 2
        if any(m in s for m in ['senior', 'confirmé', 'expert', 'lead']): return 5, None
        f = re.search(r'(\d+)\s*[-àa]\s*(\d+)', s)
        if f: return int(f.group(1)), int(f.group(2))
        m = re.search(r'(\d+)\s*(?:ans?|years?)', s)
        if m: return int(m.group(1)), None
        return None, None
    res = df['experience_requise'].apply(
        lambda x: pd.Series(parser(x),
                             index=['experience_min_ans', 'experience_max_ans'])
    )
    df = pd.concat([df, res], axis=1)
    return df

def normaliser_dates(df):
    df['date_publication'] = pd.to_datetime(df['date_publication'], errors='coerce')
    df['date_expiration']  = pd.to_datetime(df['date_expiration'],  errors='coerce')
    mask = df['date_expiration'] < df['date_publication']
    df.loc[mask, 'date_expiration'] = pd.NaT
    df['annee'] = df['date_publication'].dt.year.astype('Int64').astype(str)
    df['mois']  = df['date_publication'].dt.month.astype('Int64').astype(str).str.zfill(2)
    return df

def deduplication(df):
    avant = len(df)
    df = df.drop_duplicates(subset='id_offre', keep='first')
    print(f"[SILVER] Déduplication : {avant - len(df)} doublons supprimés → {len(df)} offres")
    return df

def transformer_silver(data_lake_root):
    data_lake_root = Path(data_lake_root)
    df = charger_bronze(data_lake_root)
    df = deduplication(df)
    df = normaliser_villes(df)
    df = normaliser_contrats(df)
    df = normaliser_titres(df)
    df = normaliser_salaires(df)
    df = normaliser_experience(df)
    df = normaliser_dates(df)
    out = data_lake_root / 'silver' / 'offres_clean'
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / 'offres_clean.parquet', index=False, compression='snappy')
    print(f"[SILVER] offres_clean.parquet → {len(df)} lignes")
    return df

# ══════════════════════════════════════════════════
# SILVER NLP — Extraction compétences
# ══════════════════════════════════════════════════
def extraire_competences(df, referentiel_path, data_lake_root):
    referentiel_path = Path(referentiel_path)
    data_lake_root   = Path(data_lake_root)

    with open(referentiel_path, encoding='utf-8') as f:
        ref = json.load(f)

    dict_comp = {}
    for famille, comps in ref['familles'].items():
        for nom, aliases in comps.items():
            for alias in aliases:
                dict_comp[alias.lower()] = {'competence': nom, 'famille': famille}

    aliases_tries = sorted(dict_comp.keys(), key=len, reverse=True)
    resultats = []

    for _, offre in df.iterrows():
        texte = ' '.join(filter(None, [
            str(offre.get('competences_brut', '') or ''),
            str(offre.get('description', '')      or '')
        ])).lower()
        trouvees = set()
        for alias in aliases_tries:
            pat = r'\b' + re.escape(alias) + r'\b'
            if re.search(pat, texte):
                info = dict_comp[alias]
                cle  = info['competence']
                if cle not in trouvees:
                    trouvees.add(cle)
                    resultats.append({
                        'id_offre':   offre['id_offre'],
                        'profil':     offre.get('profil_normalise'),
                        'ville':      offre.get('ville_std'),
                        'competence': info['competence'],
                        'famille':    info['famille'],
                        'date_pub':   str(offre.get('date_publication', ''))[:10],
                        'annee':      offre.get('annee'),
                        'mois':       offre.get('mois'),
                    })
        if not trouvees:
            resultats.append({
                'id_offre':   offre['id_offre'],
                'profil':     offre.get('profil_normalise'),
                'ville':      offre.get('ville_std'),
                'competence': 'non_détecté',
                'famille':    'inconnu',
                'date_pub':   str(offre.get('date_publication', ''))[:10],
                'annee':      offre.get('annee'),
                'mois':       offre.get('mois'),
            })

    df_comp = pd.DataFrame(resultats)
    out = data_lake_root / 'silver' / 'competences_extraites'
    out.mkdir(parents=True, exist_ok=True)
    df_comp.to_parquet(out / 'competences.parquet', index=False, compression='snappy')
    print(f"[SILVER NLP] {len(df_comp)} lignes compétences extraites")
    return df_comp

# ══════════════════════════════════════════════════
# GOLD
# ══════════════════════════════════════════════════
def construire_gold(data_lake_root):
    data_lake_root = Path(data_lake_root)
    # as_posix() → forward-slashes, obligatoire pour DuckDB même sur Windows
    silver_offres = (data_lake_root / 'silver' / 'offres_clean' / 'offres_clean.parquet').as_posix()
    silver_comp   = (data_lake_root / 'silver' / 'competences_extraites' / 'competences.parquet').as_posix()
    gold = data_lake_root / 'gold'
    gold.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()

    # Gold 1 — Top compétences par profil
    df1 = con.execute(f"""
        SELECT profil, famille, competence,
               COUNT(DISTINCT id_offre) AS nb_offres_mentionnent,
               ROUND(COUNT(DISTINCT id_offre)*100.0 /
                     (SELECT COUNT(DISTINCT id_offre) FROM '{silver_offres}'), 2) AS pct_offres_total,
               RANK() OVER (PARTITION BY profil ORDER BY COUNT(DISTINCT id_offre) DESC) AS rang_dans_profil
        FROM '{silver_comp}'
        WHERE competence != 'non_détecté'
        GROUP BY profil, famille, competence
        ORDER BY profil, rang_dans_profil
    """).df()
    df1.to_parquet(gold / 'top_competences.parquet', index=False)
    print(f"[GOLD] top_competences : {len(df1)} lignes")

    # Gold 2 — Salaires par profil et ville
    df2 = con.execute(f"""
        SELECT profil_normalise AS profil, ville_std AS ville, type_contrat_std AS type_contrat,
               COUNT(*) AS nb_offres,
               COUNT(*) FILTER (WHERE salaire_connu) AS nb_offres_avec_salaire,
               ROUND(MEDIAN(salaire_median_mad)     FILTER (WHERE salaire_connu), 0) AS salaire_median_mad,
               ROUND(AVG(salaire_median_mad)        FILTER (WHERE salaire_connu), 0) AS salaire_moyen_mad,
               ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salaire_median_mad)
                     FILTER (WHERE salaire_connu), 0) AS salaire_q1_mad,
               ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salaire_median_mad)
                     FILTER (WHERE salaire_connu), 0) AS salaire_q3_mad,
               ROUND(MIN(salaire_min_mad) FILTER (WHERE salaire_connu), 0) AS salaire_min_observe,
               ROUND(MAX(salaire_max_mad) FILTER (WHERE salaire_connu), 0) AS salaire_max_observe
        FROM '{silver_offres}'
        GROUP BY profil_normalise, ville_std, type_contrat_std
        HAVING COUNT(*) >= 3
        ORDER BY nb_offres DESC
    """).df()
    df2.to_parquet(gold / 'salaires_par_profil.parquet', index=False)
    print(f"[GOLD] salaires_par_profil : {len(df2)} lignes")

    # Gold 3 — Volume offres par ville
    df3 = con.execute(f"""
        SELECT ville_std AS ville, region_admin, profil_normalise AS profil, annee, mois,
               COUNT(*) AS nb_offres,
               COUNT(*) FILTER (WHERE teletravail ILIKE '%télétravail%'
                                   OR teletravail ILIKE '%remote%'
                                   OR teletravail ILIKE '%hybride%') AS nb_offres_remote,
               ROUND(COUNT(*) FILTER (WHERE teletravail ILIKE '%télétravail%'
                                         OR teletravail ILIKE '%remote%'
                                         OR teletravail ILIKE '%hybride%')
                     * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_remote
        FROM '{silver_offres}'
        GROUP BY ville_std, region_admin, profil_normalise, annee, mois
        ORDER BY nb_offres DESC
    """).df()
    df3.to_parquet(gold / 'offres_par_ville.parquet', index=False)
    print(f"[GOLD] offres_par_ville : {len(df3)} lignes")

    # Gold 4 — Entreprises recruteurs
    df4 = con.execute(f"""
        SELECT entreprise, ville_std AS ville,
               COUNT(*) AS nb_offres_publiees,
               COUNT(DISTINCT profil_normalise) AS nb_profils_differents,
               ROUND(AVG(salaire_median_mad) FILTER (WHERE salaire_connu), 0) AS salaire_moyen_propose,
               MIN(date_publication) AS premiere_offre,
               MAX(date_publication) AS derniere_offre
        FROM '{silver_offres}'
        WHERE entreprise IS NOT NULL AND entreprise != ''
        GROUP BY entreprise, ville_std
        HAVING COUNT(*) >= 2
        ORDER BY nb_offres_publiees DESC
        LIMIT 100
    """).df()
    df4.to_parquet(gold / 'entreprises_recruteurs.parquet', index=False)
    print(f"[GOLD] entreprises_recruteurs : {len(df4)} lignes")

    # Gold 5 — Tendances mensuelles
    df5 = con.execute(f"""
        SELECT annee, mois, profil_normalise AS profil,
               COUNT(*) AS nb_offres,
               ROUND(AVG(salaire_median_mad) FILTER (WHERE salaire_connu), 0) AS salaire_moyen_mois,
               LAG(COUNT(*)) OVER (PARTITION BY profil_normalise ORDER BY annee, mois)
                   AS nb_offres_mois_precedent
        FROM '{silver_offres}'
        GROUP BY annee, mois, profil_normalise
        ORDER BY profil_normalise, annee, mois
    """).df()
    df5.to_parquet(gold / 'tendances_mensuelles.parquet', index=False)
    print(f"[GOLD] tendances_mensuelles : {len(df5)} lignes")

    con.close()
    print(f"\n[GOLD] 5 tables Gold construites dans {gold}")

# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"Dossier projet : {BASE}")
    print(f"Data Lake      : {DATA_LAKE}\n")

    print("=== BRONZE ===")
    ingerer_bronze(OFFRES_JSON, DATA_LAKE)

    print("\n=== SILVER ===")
    df_silver = transformer_silver(DATA_LAKE)

    print("\n=== SILVER NLP ===")
    extraire_competences(df_silver, REFERENTIEL_JSON, DATA_LAKE)

    print("\n=== GOLD ===")
    construire_gold(DATA_LAKE)

    print("\n✅ Pipeline complet terminé !")
