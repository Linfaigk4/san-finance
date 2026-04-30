# reset_db.py
from app import app
from database import db, User, Expense
from werkzeug.security import generate_password_hash

with app.app_context():
    # Supprimer toutes les tables
    db.drop_all()
    print("✅ Tables supprimées")
    
    # Recréer les tables
    db.create_all()
    print("✅ Tables recréées")
    
    # Créer l'utilisateur admin
    admin = User(
        username='admin',
        password=generate_password_hash('admin123'),
        email='admin@finance.com',
        is_admin=True
    )
    db.session.add(admin)
    print("✅ Admin créé: admin / admin123")
    
    # Créer l'utilisateur test
    test_user = User(
        username='testuser',
        password=generate_password_hash('test123'),
        email='test@email.com',
        is_admin=False
    )
    db.session.add(test_user)
    print("✅ Test user créé: testuser / test123")
    
    db.session.commit()
    
    # Vérifier
    admin_check = User.query.filter_by(username='admin').first()
    test_check = User.query.filter_by(username='testuser').first()
    
    print("\n📋 Vérification:")
    print(f"Admin: {admin_check.username if admin_check else 'NON TROUVÉ'}")
    print(f"Test: {test_check.username if test_check else 'NON TROUVÉ'}")