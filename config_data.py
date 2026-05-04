# config_data.py - Données génériques pour les catégories
import random

# Catégories de dépenses (20 catégories différentes)
CATEGORIES = [
    'Alimentation', 'Transport', 'Loisirs', 'Santé', 'Shopping',
    'Factures', 'Éducation', 'Restaurant', 'Habillement', 'Sport',
    'Divertissement', 'Café', 'Abonnements', 'Animaux', 'Cadeaux',
    'Voyages', 'Technologie', 'Maison', 'Assurance', 'Impôts'
]

# Descriptions variées
DESCRIPTIONS = {
    'Alimentation': ['Courses supermarché', 'Fruits et légumes', 'Boucherie', 'Boulangerie', 'Épicerie fine'],
    'Transport': ['Essence', 'Taxi', 'Transports en commun', 'Réparation voiture', 'Parking'],
    'Loisirs': ['Cinéma', 'Théâtre', 'Concert', 'Parc d\'attractions', 'Jeux vidéo'],
    'Santé': ['Consultation médecin', 'Dentiste', 'Médicaments', 'Optique', 'Pharmacie'],
    'Shopping': ['Vêtements', 'Chaussures', 'Accessoires', 'Téléphone', 'Tablette'],
    'Factures': ['Électricité', 'Eau', 'Gaz', 'Internet', 'Téléphone fixe'],
    'Éducation': ['Livres', 'Cours en ligne', 'Fournitures scolaires', 'Formation', 'Inscription'],
    'Restaurant': ['Dîner au restaurant', 'Fast-food', 'Food truck', 'Livraison repas', 'Brunch'],
    'Habillement': ['Jean', 'Chemise', 'Robe', 'Veste', 'Accessoires mode'],
    'Sport': ['Salle de sport', 'Équipement sportif', 'Abonnement yoga', 'Course à pied', 'Natation'],
    'Divertissement': ['Netflix', 'Disney+', 'Amazon Prime', 'Spotify', 'Jeux en ligne'],
    'Café': ['Café du matin', 'Pause café', 'Thé', 'Viennoiserie', 'Sandwich'],
    'Abonnements': ['Abonnement salle', 'Magazine', 'Application', 'Streaming', 'Cloud'],
    'Animaux': ['Nourriture chien/chat', 'Vétérinaire', 'Accessoires', 'Toilettage', 'Pension'],
    'Cadeaux': ['Anniversaire', 'Noël', 'Fête', 'Mariage', 'Naissance'],
    'Voyages': ['Billet d\'avion', 'Hôtel', 'Location voiture', 'Visites', 'Restaurant voyage'],
    'Technologie': ['Smartphone', 'Ordinateur', 'Casque audio', 'Enceinte', 'Accessoires tech'],
    'Maison': ['Meubles', 'Décoration', 'Jardinage', 'Bricolage', 'Électroménager'],
    'Assurance': ['Assurance voiture', 'Assurance habitation', 'Assurance santé', 'Assurance vie', 'Assurance scolaire'],
    'Impôts': ['Taxe foncière', 'Taxe d\'habitation', 'Impôt sur le revenu', 'Taxe poubelle', 'CFE']
}

def generate_realistic_amount(category):
    """Génère un montant réaliste selon la catégorie"""
    amounts = {
        'Alimentation': (20, 150),
        'Transport': (5, 80),
        'Loisirs': (10, 100),
        'Santé': (15, 200),
        'Shopping': (25, 300),
        'Factures': (40, 250),
        'Éducation': (10, 150),
        'Restaurant': (15, 120),
        'Habillement': (20, 200),
        'Sport': (10, 100),
        'Divertissement': (5, 60),
        'Café': (2, 15),
        'Abonnements': (5, 50),
        'Animaux': (10, 80),
        'Cadeaux': (20, 150),
        'Voyages': (100, 800),
        'Technologie': (50, 1000),
        'Maison': (30, 300),
        'Assurance': (50, 200),
        'Impôts': (100, 1000)
    }
    min_amt, max_amt = amounts.get(category, (10, 100))
    return round(random.uniform(min_amt, max_amt), 2)