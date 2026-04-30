from app import app, db
from database import User, Expense
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import numpy as np

def seed_database():
    """Génère des données de test réalistes pour la démo"""
    
    with app.app_context():
        # Nettoyer les données existantes
        db.drop_all()
        db.create_all()
        
        # Catégories de dépenses
        categories = ['Alimentation', 'Transport', 'Loisirs', 'Santé', 'Shopping', 'Factures', 'Éducation', 'Restaurant']
        
        # Utilisateurs de test
        users_data = [
            {'username': 'admin', 'password': 'admin123', 'email': 'admin@finance.com', 'is_admin': True},
            {'username': 'jean_dupont', 'password': 'test123', 'email': 'jean@email.com', 'is_admin': False},
            {'username': 'marie_martin', 'password': 'test123', 'email': 'marie@email.com', 'is_admin': False},
            {'username': 'pierre_durand', 'password': 'test123', 'email': 'pierre@email.com', 'is_admin': False},
            {'username': 'sophie_bernard', 'password': 'test123', 'email': 'sophie@email.com', 'is_admin': False},
            {'username': 'lucas_leroy', 'password': 'test123', 'email': 'lucas@email.com', 'is_admin': False},
        ]
        
        users = []
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                password=generate_password_hash(user_data['password']),
                email=user_data['email'],
                is_admin=user_data['is_admin']
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        
        # Générer des dépenses pour chaque utilisateur (3 mois de données)
        start_date = datetime.now() - timedelta(days=90)
        
        descriptions = [
            "Courses supermarché", "Restaurant", "Cinéma", "Essence voiture", 
            "Shopping en ligne", "Facture électricité", "Consultation médecin",
            "Abonnement Netflix", "Achat livres", "Café", "Taxi", "Sport",
            "Téléphone mobile", "Internet", "Vêtements", "Chaussures",
            "Médicaments", "Frais bancaires", "Cadeau", "Loisirs"
        ]
        
        for user in users:
            # Chaque utilisateur a entre 50 et 150 dépenses
            num_expenses = random.randint(50, 150)
            
            for i in range(num_expenses):
                # Date aléatoire sur les 90 derniers jours
                random_days = random.randint(0, 90)
                expense_date = start_date + timedelta(days=random_days, hours=random.randint(0, 23))
                
                # Catégorie avec probabilités différentes selon l'utilisateur
                if user.username == 'jean_dupont':
                    # Jean dépense beaucoup en alimentation et transport
                    weights = [0.35, 0.25, 0.1, 0.05, 0.1, 0.1, 0.03, 0.02]
                elif user.username == 'marie_martin':
                    # Marie dépense en shopping et loisirs
                    weights = [0.2, 0.1, 0.2, 0.05, 0.25, 0.1, 0.05, 0.05]
                elif user.username == 'pierre_durand':
                    # Pierre dépense en factures et santé
                    weights = [0.15, 0.05, 0.1, 0.25, 0.05, 0.3, 0.05, 0.05]
                elif user.username == 'sophie_bernard':
                    # Sophie dépense en éducation et restaurant
                    weights = [0.2, 0.2, 0.1, 0.05, 0.1, 0.1, 0.2, 0.05]
                elif user.username == 'lucas_leroy':
                    # Lucas dépense en loisirs et shopping
                    weights = [0.15, 0.15, 0.3, 0.02, 0.2, 0.08, 0.05, 0.05]
                else:
                    weights = [0.2, 0.15, 0.15, 0.1, 0.15, 0.1, 0.05, 0.1]
                
                category = random.choices(categories, weights=weights)[0]
                
                # Montant selon la catégorie
                if category == 'Alimentation':
                    amount = random.uniform(15, 120)
                elif category == 'Transport':
                    amount = random.uniform(5, 60)
                elif category == 'Loisirs':
                    amount = random.uniform(10, 80)
                elif category == 'Santé':
                    amount = random.uniform(20, 150)
                elif category == 'Shopping':
                    amount = random.uniform(25, 200)
                elif category == 'Factures':
                    amount = random.uniform(30, 250)
                elif category == 'Éducation':
                    amount = random.uniform(15, 100)
                else:  # Restaurant
                    amount = random.uniform(20, 90)
                
                # Tendance temporelle: les dépenses augmentent légèrement avec le temps
                amount = amount * (1 + (random_days / 90) * 0.2)
                
                expense = Expense(
                    amount=round(amount, 2),
                    category=category,
                    description=random.choice(descriptions),
                    date=expense_date,
                    user_id=user.id
                )
                db.session.add(expense)
                
                # Commit toutes les 50 dépenses pour éviter les timeout
                if i % 50 == 0:
                    db.session.commit()
        
        db.session.commit()
        print(f"✅ Base de données initialisée avec succès!")
        print(f"   - {len(users)} utilisateurs créés")
        print(f"   - {Expense.query.count()} dépenses générées")
        
        # Afficher quelques statistiques
        from models import DataAnalyzer
        df = DataAnalyzer.get_expense_dataframe()
        print(f"\n📊 Statistiques des données générées:")
        print(f"   - Montant moyen: {df['amount'].mean():.2f}Fcfa")
        print(f"   - Montant total: {df['amount'].sum():.2f}Fcfa")
        print(f"   - Dépense max: {df['amount'].max():.2f}Fcfa")
        print(f"   - Dépense min: {df['amount'].min():.2f}Fcfa")

def reset_database():
    """Réinitialise complètement la base de données"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Base de données réinitialisée")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_database()
    else:
        seed_database()