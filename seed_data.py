# seed_data.py - Version améliorée avec données génériques robustes
from app import app, db
from database import User, Expense
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import numpy as np

# Catégories de dépenses (10+ catégories différentes)
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

def seed_database():
    """Génère des données de test complètes pour la démo"""
    
    with app.app_context():
        # Nettoyer les données existantes
        db.drop_all()
        db.create_all()
        print("✅ Base de données réinitialisée")
        
        # 1. Créer l'utilisateur ADMIN avec données génériques
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            email='admin@finance.com',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin créé: admin/admin123")
        
        # 2. Créer 3 utilisateurs de test
        test_users = [
            {'username': 'jean_dupont', 'email': 'jean@email.com'},
            {'username': 'marie_martin', 'email': 'marie@email.com'},
            {'username': 'pierre_durand', 'email': 'pierre@email.com'},
        ]
        
        users_created = []
        for u in test_users:
            user = User(
                username=u['username'],
                password=generate_password_hash('test123'),
                email=u['email'],
                is_admin=False
            )
            db.session.add(user)
            users_created.append(user)
        
        db.session.commit()
        users_created.append(admin)
        print(f"✅ {len(users_created)} utilisateurs créés")
        
        # 3. Générer des dépenses pour chaque utilisateur (3 mois de données)
        start_date = datetime.now() - timedelta(days=90)
        
        total_expenses = 0
        
        for user in users_created:
            # Nombre de dépenses: entre 50 et 200 par utilisateur
            num_expenses = random.randint(50, 200)
            
            for i in range(num_expenses):
                # Date aléatoire sur les 90 derniers jours
                random_days = random.randint(0, 90)
                expense_date = start_date + timedelta(days=random_days, hours=random.randint(8, 22))
                
                # Choisir une catégorie (distribution variée)
                if user.username == 'admin':
                    # L'admin a une distribution équilibrée
                    category = random.choice(CATEGORIES)
                elif user.username == 'jean_dupont':
                    # Jean: alimentation + transport
                    weights = [0.25, 0.20, 0.10, 0.05, 0.10, 0.10, 0.05, 0.05, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
                    category = random.choices(CATEGORIES, weights=weights)[0]
                elif user.username == 'marie_martin':
                    # Marie: shopping + loisirs
                    weights = [0.15, 0.05, 0.20, 0.05, 0.25, 0.05, 0.05, 0.05, 0.05, 0.03, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
                    category = random.choices(CATEGORIES, weights=weights)[0]
                else:
                    # Pierre: factures + santé
                    weights = [0.15, 0.05, 0.05, 0.20, 0.05, 0.25, 0.05, 0.05, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
                    category = random.choices(CATEGORIES, weights=weights)[0]
                
                # Montant réaliste selon catégorie
                amount = generate_realistic_amount(category)
                
                # Ajouter une tendance temporelle (légère augmentation)
                if random_days > 60:
                    amount = amount * 1.15
                elif random_days > 30:
                    amount = amount * 1.05
                
                # Description pertinente
                desc_list = DESCRIPTIONS.get(category, ['Dépense courante', 'Achat quotidien', 'Dépense diverses'])
                description = random.choice(desc_list)
                
                expense = Expense(
                    amount=round(amount, 2),
                    category=category,
                    description=f"{description} - {expense_date.strftime('%d/%m')}",
                    date=expense_date,
                    user_id=user.id
                )
                db.session.add(expense)
                total_expenses += 1
                
                # Commit par lots
                if total_expenses % 100 == 0:
                    db.session.commit()
                    print(f"   💰 {total_expenses} dépenses créées...")
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("📊 STATISTIQUES DES DONNÉES GÉNÉRÉES")
        print("="*50)
        
        # Vérification des comptes
        admin_check = User.query.filter_by(username='admin').first()
        print(f"\n👤 ADMIN: {admin_check.username} (mdp: admin123)")
        print(f"   - {len(admin_check.expenses)} dépenses")
        
        # Stats par utilisateur
        for user in users_created:
            expenses = Expense.query.filter_by(user_id=user.id).all()
            categories_used = set(e.category for e in expenses)
            total = sum(e.amount for e in expenses)
            print(f"\n👤 {user.username} (test123):")
            print(f"   - {len(expenses)} dépenses")
            print(f"   - Total: {total:.2f}€")
            print(f"   - Moyenne: {total/len(expenses):.2f}€")
            print(f"   - Catégories: {len(categories_used)}/{len(CATEGORIES)}")
        
        print("\n" + "="*50)
        print("✅ INITIALISATION TERMINÉE !")
        print("="*50)
        print("\n🔑 COMPTES DE TEST:")
        print("   - admin / admin123 (toutes les catégories)")
        print("   - jean_dupont / test123 (alimentation + transport)")
        print("   - marie_martin / test123 (shopping + loisirs)")
        print("   - pierre_durand / test123 (factures + santé)")

if __name__ == '__main__':
    seed_database()