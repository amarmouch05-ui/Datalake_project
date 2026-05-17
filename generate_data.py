import json
import random
import csv
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION GÉNÉRALE
# ============================================================
random.seed(42)  # Pour avoir les mêmes données à chaque génération

# ============================================================
# DONNÉES DE BASE
# ============================================================

VILLES = [
    # Volontairement avec des variantes sales (comme dans la vraie vie)
    "Casablanca", "CASABLANCA", "casa", "Casablanca ", "casablanca",
    "Rabat", "RABAT", "Rabat ", "rabat",
    "Tanger", "TANGER", "Tanger ", "tanger",
    "Marrakech", "MARRAKECH", "marrakech",
    "Fès", "FES", "Fes", "fès",
    "Agadir", "AGADIR", "agadir",
    "Meknès", "MEKNES", "meknes",
    "Oujda", "OUJDA",
    "Tétouan", "TETOUAN",
    "Kenitra", "KENITRA"
]

# Probabilité par ville (Casablanca est la plus représentée)
VILLES_POIDS = [
    10, 8, 6, 5, 4,   # Casablanca variants
    8, 6, 5, 4,        # Rabat variants
    5, 4, 3, 2,        # Tanger variants
    4, 3, 2,           # Marrakech variants
    3, 2, 2, 2,        # Fès variants
    2, 2, 1,           # Agadir variants
    1, 1, 1,           # Meknès variants
    1, 1,              # Oujda variants
    1, 1,              # Tétouan variants
    1, 1               # Kenitra variants
]

SOURCES = ["rekrute", "marocannonce", "linkedin"]

TITRES_POSTES = [
    # Data Engineering (variantes sales)
    "Data Engineer", "Data Eng.", "Ingénieur Data", "Dev Data",
    "Ingénieur Big Data", "Data Engineer Junior", "Senior Data Engineer",
    "Ingénieur ETL", "Pipeline Developer", "Data Engineering",

    # Data Analysis
    "Data Analyst", "Analyste Data", "Business Intelligence Analyst",
    "Développeur BI", "Ingénieur BI", "Analyste BI",
    "Reporting Analyst", "Data Analytics",

    # Data Science
    "Data Scientist", "Machine Learning Engineer", "ML Engineer",
    "Ingénieur IA", "Deep Learning Engineer", "NLP Engineer",

    # Dev Web
    "Développeur Full Stack", "Full Stack Developer", "Fullstack Dev",
    "Développeur Backend", "Backend Developer",
    "Développeur Frontend", "Frontend Developer",
    "Développeur Mobile", "iOS Developer", "Android Developer",

    # Infrastructure
    "DevOps Engineer", "SRE", "Cloud Engineer",
    "Administrateur Systèmes", "Ingénieur Réseau",

    # Cyber
    "Ingénieur Cybersécurité", "Pentester", "SOC Analyst",

    # Management
    "Chef de Projet IT", "Scrum Master", "Architecte Data",
    "Architecte Cloud", "Architecte Logiciel"
]

TYPES_CONTRAT = [
    # Variantes sales
    "CDI", "cdi", "Contrat à durée indéterminée", "Permanent",
    "CDD", "cdd", "Contrat à durée déterminée",
    "Freelance", "freelance", "Mission freelance",
    "Stage", "stage", "Internship"
]

EXPERIENCES = [
    "0-1 ans", "Débutant accepté", "Junior", "Sans expérience",
    "1-2 ans", "1 à 2 ans", "min 1 an",
    "2-3 ans", "2 à 3 ans",
    "3-5 ans", "3 à 5 ans", "min 3 ans",
    "5-7 ans", "5 à 7 ans", "Senior (5+ ans)",
    "7-10 ans", "Senior (7+ ans)", "Expert",
    None
]

NIVEAUX_ETUDES = ["Bac+2", "Bac+3", "Bac+5", "Bac+5 (Master/Ingénieur)", "Doctorat", None]

SECTEURS = [
    "Informatique / Télécom", "Banque / Finance", "Conseil / SSII",
    "E-commerce", "Industrie", "Santé", "Education", "Logistique"
]

TELETRAVAIL = ["Présentiel", "Hybride", "Télétravail complet", "Remote", None]

LANGUES = [
    ["Français"], ["Français", "Anglais"], ["Arabe", "Français"],
    ["Français", "Anglais", "Arabe"], ["Anglais"], ["Arabe", "Français", "Anglais"]
]

ENTREPRISES = [
    "TechMaroc SARL", "Capgemini Maroc", "CGI Maroc", "IBM Maroc",
    "Oracle Maroc", "Microsoft Maroc", "OCP Digital", "Maroc Telecom",
    "Inwi", "Orange Maroc", "HPS", "BMCE Bank IT", "CIH Bank Digital",
    "Attijariwafa Tech", "Al Barid Bank", "Decathlon Maroc",
    "Jumia Maroc", "Glovo Maroc", "Lydec Digital", "ONCF Digital",
    "RAM IT", "LafargeHolcim Maroc", "TotalEnergies Maroc",
    "Sanlam Maroc", "AXA Tech Maroc", "CNIA Assurance",
    "Sopra HR Software", "Intelcia", "Webhelp Maroc",
    "DataTech Solutions", "CloudMaroc", "DigitalFactory",
    "NearShore Technology", "Devoteam Maroc", "Accenture Maroc",
    "Deloitte Digital Maroc", "PwC Digital", "EY Tech Maroc",
    "Tanger Free Zone IT", "Technopark Casablanca"
]

COMPETENCES_PAR_PROFIL = {
    "data": [
        "Python", "SQL", "Spark", "Kafka", "Airflow", "dbt",
        "Hadoop", "Power BI", "Tableau", "AWS", "GCP", "Azure",
        "pandas", "scikit-learn", "TensorFlow", "Docker", "Git",
        "PostgreSQL", "MongoDB", "Elasticsearch", "Looker", "Metabase"
    ],
    "web": [
        "React", "Node.js", "Angular", "Django", "Spring Boot",
        "JavaScript", "TypeScript", "Java", "Python", "PHP",
        "MySQL", "PostgreSQL", "Docker", "Git", "REST API",
        "GraphQL", "AWS", "CSS", "HTML"
    ],
    "devops": [
        "Docker", "Kubernetes", "Jenkins", "Terraform", "Ansible",
        "AWS", "GCP", "Azure", "Python", "Bash", "Git",
        "Prometheus", "Grafana", "Linux"
    ],
    "cyber": [
        "Python", "Kali Linux", "Metasploit", "Wireshark", "SIEM",
        "ISO 27001", "OWASP", "Nmap", "Burp Suite", "Splunk"
    ]
}

DESCRIPTIONS_TEMPLATES = [
    "Nous recherchons un {titre} expérimenté pour rejoindre notre équipe. "
    "Le candidat devra maîtriser {comp1} et {comp2}. "
    "Une connaissance de {comp3} serait un plus. "
    "Vous travaillerez en méthode Agile avec une équipe de {n} personnes. "
    "Expérience requise : {exp}.",

    "Dans le cadre de notre croissance, nous recrutons un {titre}. "
    "Compétences requises : {comp1}, {comp2}, {comp3}. "
    "Vous serez responsable de la conception et du développement de solutions data. "
    "Bonne maîtrise du français et de l'anglais souhaitée.",

    "Poste : {titre} basé à notre siège. "
    "Stack technique : {comp1}, {comp2}, {comp3}, {comp4}. "
    "Vous intégrerez une équipe dynamique et contribuerez aux projets stratégiques. "
    "Formation : Bac+5 en informatique ou équivalent.",

    "Notre client, leader dans son secteur, recherche un {titre} senior. "
    "Vous maîtrisez parfaitement {comp1} et {comp2}. "
    "La connaissance de {comp3} et {comp4} est indispensable. "
    "Poste en CDI, package attractif selon profil."
]

# ============================================================
# FORMATS DE SALAIRES (intentionnellement variés et sales)
# ============================================================

def generer_salaire(profil_type):
    """Génère un salaire avec différents formats, certains sales."""

    # Fourchettes réalistes selon le profil (en MAD)
    fourchettes = {
        "data_senior": (18000, 45000),
        "data_junior": (8000, 18000),
        "web_senior": (12000, 30000),
        "web_junior": (6000, 14000),
        "devops": (15000, 40000),
        "manager": (20000, 50000)
    }

    profil = random.choice(list(fourchettes.keys()))
    sal_min, sal_max = fourchettes[profil]

    # Valeur réelle
    val_min = random.randint(sal_min, sal_max - 2000)
    val_max = val_min + random.randint(2000, 8000)

    # 20% des offres : salaire non communiqué
    if random.random() < 0.20:
        return random.choice(["Selon profil", "Confidentiel", None, "À négocier"])

    # 10% : format en K
    if random.random() < 0.10:
        return f"{val_min//1000}K-{val_max//1000}K"

    # 5% : en EUR (offres internationales)
    if random.random() < 0.05:
        val_eur_min = round(val_min / 10.8)
        val_eur_max = round(val_max / 10.8)
        return f"{val_eur_min}-{val_eur_max} EUR"

    # Format normal
    return f"{val_min}-{val_max} MAD"


# ============================================================
# GÉNÉRATION DES OFFRES D'EMPLOI
# ============================================================

def generer_offres(nb_offres=5000):
    """Génère nb_offres offres d'emploi avec des données réalistes et sales."""

    offres = []
    date_debut = datetime(2023, 1, 1)
    date_fin = datetime(2024, 11, 30)

    for i in range(nb_offres):
        source = random.choice(SOURCES)

        # ID selon la source
        if source == "rekrute":
            id_offre = f"RK-{random.randint(2023,2024)}-{random.randint(10000,99999)}"
        elif source == "marocannonce":
            id_offre = f"MA-{random.randint(100000,999999)}"
        else:
            id_offre = f"LI-{random.randint(1000000,9999999)}"

        # Titre et compétences
        titre = random.choice(TITRES_POSTES)

        # Choisir les compétences selon le profil du titre
        if any(x in titre.lower() for x in ["data", "bi", "machine", "ml", "ia"]):
            pool = COMPETENCES_PAR_PROFIL["data"]
        elif any(x in titre.lower() for x in ["devops", "cloud", "sre", "système", "réseau"]):
            pool = COMPETENCES_PAR_PROFIL["devops"]
        elif any(x in titre.lower() for x in ["cyber", "sécurité", "soc", "pent"]):
            pool = COMPETENCES_PAR_PROFIL["cyber"]
        else:
            pool = COMPETENCES_PAR_PROFIL["web"]

        nb_comp = random.randint(3, 8)
        competences = random.sample(pool, min(nb_comp, len(pool)))

        # Date de publication
        delta = date_fin - date_debut
        date_pub = date_debut + timedelta(days=random.randint(0, delta.days))

        # Date expiration (normalement +30 jours, parfois incohérente)
        if random.random() < 0.05:  # 5% de dates incohérentes
            date_exp = date_pub - timedelta(days=random.randint(1, 10))
        else:
            date_exp = date_pub + timedelta(days=random.randint(20, 60))

        # Description avec compétences intégrées
        template = random.choice(DESCRIPTIONS_TEMPLATES)
        description = template.format(
            titre=titre,
            comp1=competences[0] if len(competences) > 0 else "Python",
            comp2=competences[1] if len(competences) > 1 else "SQL",
            comp3=competences[2] if len(competences) > 2 else "Git",
            comp4=competences[3] if len(competences) > 3 else "Docker",
            n=random.randint(3, 20),
            exp=random.choice(EXPERIENCES) or "non précisée"
        )

        # Ville avec variantes sales
        ville = random.choices(VILLES, weights=VILLES_POIDS, k=1)[0]

        # Type contrat avec variantes sales
        type_contrat = random.choice(TYPES_CONTRAT)

        offre = {
            "id_offre": id_offre,
            "source": source,
            "titre_poste": titre,
            "description": description,
            "competences_brut": ", ".join(competences),
            "entreprise": random.choice(ENTREPRISES),
            "ville": ville,
            "type_contrat": type_contrat,
            "experience_requise": random.choice(EXPERIENCES),
            "salaire_brut": generer_salaire(titre),
            "niveau_etudes": random.choice(NIVEAUX_ETUDES),
            "secteur": random.choice(SECTEURS),
            "date_publication": date_pub.strftime("%Y-%m-%d"),
            "date_expiration": date_exp.strftime("%Y-%m-%d"),
            "nb_postes": random.choice([1, 1, 1, 2, 3]),
            "teletravail": random.choice(TELETRAVAIL),
            "langue_requise": random.choice(LANGUES)
        }

        offres.append(offre)

    return offres


# ============================================================
# GÉNÉRATION DU RÉFÉRENTIEL DE COMPÉTENCES
# ============================================================

def generer_referentiel():
    """Génère le fichier referentiel_competences_it.json"""

    referentiel = {
        "familles": {
            "langages": {
                "python": ["python", "python3", "py"],
                "javascript": ["javascript", "js", "node.js", "nodejs", "node"],
                "java": ["java", "java8", "java11", "java17"],
                "sql": ["sql", "mysql", "postgresql", "postgres", "oracle", "tsql"],
                "r": ["r", "rlang", "r-studio"],
                "php": ["php", "php7", "php8"],
                "typescript": ["typescript", "ts"],
                "scala": ["scala"],
                "bash": ["bash", "shell", "bash scripting"]
            },
            "frameworks_web": {
                "react": ["react", "reactjs", "react.js"],
                "angular": ["angular", "angularjs"],
                "django": ["django", "django rest"],
                "spring": ["spring", "spring boot", "springboot"],
                "vuejs": ["vue", "vuejs", "vue.js"],
                "laravel": ["laravel"],
                "fastapi": ["fastapi", "fast api"],
                "flask": ["flask"]
            },
            "data_engineering": {
                "spark": ["spark", "apache spark", "pyspark"],
                "kafka": ["kafka", "apache kafka"],
                "airflow": ["airflow", "apache airflow"],
                "dbt": ["dbt", "data build tool"],
                "hadoop": ["hadoop", "hdfs", "mapreduce"],
                "pandas": ["pandas"],
                "numpy": ["numpy"],
                "flink": ["flink", "apache flink"]
            },
            "cloud": {
                "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
                "gcp": ["gcp", "google cloud", "bigquery", "cloud storage"],
                "azure": ["azure", "microsoft azure", "synapse"]
            },
            "bi_analytics": {
                "power_bi": ["power bi", "powerbi", "pbi"],
                "tableau": ["tableau", "tableau desktop"],
                "metabase": ["metabase"],
                "looker": ["looker", "looker studio"],
                "qlik": ["qlik", "qlikview", "qliksense"]
            },
            "devops_outils": {
                "docker": ["docker", "docker-compose"],
                "kubernetes": ["kubernetes", "k8s"],
                "git": ["git", "github", "gitlab"],
                "jenkins": ["jenkins", "ci/cd"],
                "terraform": ["terraform"],
                "ansible": ["ansible"]
            },
            "bases_de_donnees": {
                "postgresql": ["postgresql", "postgres"],
                "mongodb": ["mongodb", "mongo"],
                "elasticsearch": ["elasticsearch", "elastic"],
                "redis": ["redis"],
                "mysql": ["mysql"],
                "oracle_db": ["oracle database", "oracle db"]
            },
            "machine_learning": {
                "scikit_learn": ["scikit-learn", "sklearn"],
                "tensorflow": ["tensorflow", "tf"],
                "pytorch": ["pytorch", "torch"],
                "keras": ["keras"],
                "mlflow": ["mlflow"],
                "huggingface": ["huggingface", "transformers"]
            }
        }
    }
    return referentiel


# ============================================================
# GÉNÉRATION DES ENTREPRISES
# ============================================================

def generer_entreprises():
    """Génère le fichier entreprises_it_maroc.csv"""

    entreprises = [
        ("Capgemini Maroc", "Conseil / SSII", "Grande Entreprise", "Casablanca", "capgemini.com/ma", "Conseil"),
        ("CGI Maroc", "Conseil / SSII", "Grande Entreprise", "Casablanca", "cgi.com", "SSII"),
        ("IBM Maroc", "Informatique", "Grande Entreprise", "Casablanca", "ibm.com/ma", "Produit"),
        ("Oracle Maroc", "Informatique", "Grande Entreprise", "Casablanca", "oracle.com/ma", "Produit"),
        ("Microsoft Maroc", "Informatique", "Grande Entreprise", "Casablanca", "microsoft.com/ma", "Produit"),
        ("OCP Digital", "Industrie", "Grande Entreprise", "Casablanca", "ocpgroup.ma", "Autre"),
        ("Maroc Telecom", "Telecom", "Grande Entreprise", "Rabat", "iam.ma", "Telecom"),
        ("Inwi", "Telecom", "Grande Entreprise", "Casablanca", "inwi.ma", "Telecom"),
        ("Orange Maroc", "Telecom", "Grande Entreprise", "Casablanca", "orange.ma", "Telecom"),
        ("HPS", "Fintech", "ETI", "Casablanca", "hps-worldwide.com", "Produit"),
        ("BMCE Bank IT", "Banque", "Grande Entreprise", "Casablanca", "bmcebank.ma", "Banque"),
        ("Attijariwafa Tech", "Banque", "Grande Entreprise", "Casablanca", "attijariwafabank.com", "Banque"),
        ("CIH Bank Digital", "Banque", "ETI", "Rabat", "cihbank.ma", "Banque"),
        ("Jumia Maroc", "E-commerce", "ETI", "Casablanca", "jumia.ma", "Produit"),
        ("Glovo Maroc", "Logistique", "PME", "Casablanca", "glovoapp.com", "Produit"),
        ("Intelcia", "Conseil / SSII", "Grande Entreprise", "Casablanca", "intelcia.com", "SSII"),
        ("Webhelp Maroc", "Conseil", "Grande Entreprise", "Rabat", "webhelp.com", "Conseil"),
        ("Devoteam Maroc", "Conseil / SSII", "ETI", "Casablanca", "devoteam.com", "Conseil"),
        ("Accenture Maroc", "Conseil / SSII", "Grande Entreprise", "Casablanca", "accenture.com", "Conseil"),
        ("Deloitte Digital Maroc", "Conseil", "Grande Entreprise", "Casablanca", "deloitte.ma", "Conseil"),
        ("DataTech Solutions", "Data / IA", "Startup", "Casablanca", "datatech.ma", "Produit"),
        ("CloudMaroc", "Cloud", "Startup", "Rabat", "cloudmaroc.ma", "Produit"),
        ("NearShore Technology", "SSII", "ETI", "Tanger", "nearshore.ma", "SSII"),
        ("Tanger Free Zone IT", "Informatique", "ETI", "Tanger", "tangerfreeezone.com", "SSII"),
        ("TechMaroc SARL", "Informatique", "PME", "Casablanca", "techmaroc.ma", "Produit"),
        ("DigitalFactory", "Digital", "Startup", "Casablanca", "digitalfactory.ma", "Produit"),
        ("Sopra HR Software", "RH Tech", "ETI", "Casablanca", "soprahrsoft.com", "Produit"),
        ("RAM IT", "Transport", "Grande Entreprise", "Casablanca", "royalairmaroc.com", "Autre"),
        ("ONCF Digital", "Transport", "Grande Entreprise", "Rabat", "oncf.ma", "Autre"),
        ("PwC Digital Maroc", "Conseil", "Grande Entreprise", "Casablanca", "pwc.com/ma", "Conseil"),
    ]
    return entreprises


# ============================================================
# SAUVEGARDE DES FICHIERS
# ============================================================

def sauvegarder_fichiers():
    print("🚀 Génération des données en cours...")

    # 1. Offres d'emploi
    print("   📝 Génération de 5000 offres d'emploi...")
    offres = generer_offres(5000)
    data_offres = {"offres": offres}

    with open("offres_emploi_it_maroc.json", "w", encoding="utf-8") as f:
        json.dump(data_offres, f, ensure_ascii=False, indent=2)
    print(f"   ✅ offres_emploi_it_maroc.json créé ({len(offres)} offres)")

    # 2. Référentiel de compétences
    print("   📚 Génération du référentiel de compétences...")
    referentiel = generer_referentiel()

    with open("referentiel_competences_it.json", "w", encoding="utf-8") as f:
        json.dump(referentiel, f, ensure_ascii=False, indent=2)
    print("   ✅ referentiel_competences_it.json créé")

    # 3. Entreprises
    print("   🏢 Génération des entreprises...")
    entreprises = generer_entreprises()

    with open("entreprises_it_maroc.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nom_entreprise", "secteur", "taille", "ville_siege", "site_web", "type"])
        writer.writerows(entreprises)
    print("   ✅ entreprises_it_maroc.csv créé")

    # Statistiques rapides
    print("\n📊 Statistiques des données générées :")
    sources = {}
    villes_count = {}
    for offre in offres:
        s = offre["source"]
        sources[s] = sources.get(s, 0) + 1
        v = offre["ville"]
        villes_count[v] = villes_count.get(v, 0) + 1

    print("   Sources :")
    for s, count in sources.items():
        print(f"      - {s}: {count} offres")

    print("\n✅ TERMINÉ ! Les 3 fichiers de données sont prêts.")
    print("   Fichiers créés dans :", __import__('os').getcwd())


# ============================================================
# LANCEMENT
# ============================================================
if __name__ == "__main__":
    sauvegarder_fichiers()