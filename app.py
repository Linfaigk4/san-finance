from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import json
import plotly
import plotly.express as px
from database import db, User, Expense
from models import DataAnalyzer
from user_analysis import UserDataAnalyzer
import random  # Ajouter cet import
from seed_data import CATEGORIES, DESCRIPTIONS, generate_realistic_amount  # Importer les fonctions du seed

app = Flask(__name__)

# Configuration pour Render
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre-cle-secrete-ici-changez-en-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///expenses.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Accès administrateur requis', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.template_global()
def now():
    return datetime.now()

# Routes
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nom d\'utilisateur déjà pris', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password, email=email, is_admin=False)
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie ! Connectez-vous', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'Bienvenue {username} !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants invalides', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnecté', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date.desc()).all()
    
    total_expenses = sum(e.amount for e in expenses)
    avg_expense = total_expenses / len(expenses) if expenses else 0
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount
    
    graph_json = None
    graph2_json = None
    
    if expenses and len(expenses) > 0:
        try:
            fig = px.pie(
                values=list(categories.values()), 
                names=list(categories.keys()), 
                title="Dépenses par catégorie", 
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            graph_json = fig.to_json()
            
            from collections import defaultdict
            daily_totals = defaultdict(float)
            for e in expenses:
                date_str = e.date.strftime('%Y-%m-%d')
                daily_totals[date_str] += e.amount
            
            dates = sorted(daily_totals.keys())
            amounts = [daily_totals[d] for d in dates]
            
            if dates:
                fig2 = px.line(
                    x=dates, 
                    y=amounts, 
                    title="Évolution des dépenses", 
                    labels={'x': 'Date', 'y': 'Montant (€)'}
                )
                fig2.update_traces(line_color='#9b59b6')
                graph2_json = fig2.to_json()
        except Exception as e:
            print(f"Erreur création graphique: {e}")
    
    return render_template('dashboard.html', 
                         user=user, 
                         expenses=expenses[:10],
                         total_expenses=total_expenses,
                         avg_expense=avg_expense,
                         categories=categories,
                         graph_json=graph_json,
                         graph2_json=graph2_json)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']
        date_str = request.form.get('date')
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        expense = Expense(
            amount=amount,
            category=category,
            description=description,
            date=date,
            user_id=session['user_id']
        )
        db.session.add(expense)
        db.session.commit()
        
        flash('Dépense ajoutée avec succès !', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_expense.html')

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/api/analysis/simple_regression')
@admin_required
def simple_regression():
    result = DataAnalyzer.linear_regression_simple()
    return jsonify(result if result else {'error': 'Pas assez de données'})

@app.route('/api/analysis/multiple_regression')
@admin_required
def multiple_regression():
    result = DataAnalyzer.linear_regression_multiple()
    return jsonify(result if result else {'error': 'Pas assez de données'})

@app.route('/api/analysis/pca')
@admin_required
def pca_analysis():
    result = DataAnalyzer.pca_analysis()
    return jsonify(result if result else {'error': 'Pas assez de données'})

@app.route('/api/analysis/supervised')
@admin_required
def supervised_classification():
    result = DataAnalyzer.supervised_classification()
    return jsonify(result if result else {'error': 'Pas assez de données'})

@app.route('/api/analysis/unsupervised')
@admin_required
def unsupervised_classification():
    result = DataAnalyzer.unsupervised_classification()
    return jsonify(result if result else {'error': 'Pas assez de données'})

@app.route('/analysis')
@admin_required
def analysis():
    return render_template('analysis.html')

@app.route('/api/users_stats')
@admin_required
def users_stats():
    users = User.query.all()
    stats = []
    for user in users:
        expenses = Expense.query.filter_by(user_id=user.id).all()
        total = sum(e.amount for e in expenses)
        stats.append({
            'username': user.username,
            'expenses_count': len(expenses),
            'total_amount': total,
            'avg_amount': total / len(expenses) if expenses else 0
        })
    return jsonify(stats)

@app.route('/api/categories_stats')
@admin_required
def categories_stats():
    expenses = Expense.query.all()
    categories = {}
    for exp in expenses:
        categories[exp.category] = categories.get(exp.category, 0) + 1
    return jsonify(categories)

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
# ============ ROUTES D'ANALYSE POUR UTILISATEUR ============

@app.route('/my_analysis')
@login_required
def my_analysis():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        return render_template('my_analysis.html', 
                             user=user, 
                             has_data=len(expenses) > 0,
                             expenses_count=len(expenses))
    except Exception as e:
        flash('Erreur lors du chargement des analyses', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/api/my_analysis/simple_regression')
@login_required
def my_simple_regression():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.linear_regression_simple(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

@app.route('/api/my_analysis/multiple_regression')
@login_required
def my_multiple_regression():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.linear_regression_multiple(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

@app.route('/api/my_analysis/pca')
@login_required
def my_pca():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.pca_analysis(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

@app.route('/api/my_analysis/supervised')
@login_required
def my_supervised():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.supervised_classification(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

@app.route('/api/my_analysis/unsupervised')
@login_required
def my_unsupervised():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.unsupervised_classification(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

@app.route('/api/my_analysis/advice')
@login_required
def my_advice():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.get_forecast_advice(expenses)
        return jsonify(result if result else [])
    except Exception as e:
        return jsonify([])

@app.route('/api/my_analysis/stats')
@login_required
def my_stats():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.get_statistics(expenses)
        return jsonify(result if result else {})
    except Exception as e:
        return jsonify({})
    

# Création des tables et données de test
# ============ CRÉATION AUTOMATIQUE DES DONNÉES DE TEST ============
with app.app_context():
    # Créer toutes les tables si elles n'existent pas
    db.create_all()
    
    # Vérifier si la base est vide ou si admin n'existe pas
    admin_exists = User.query.filter_by(username='admin').first()
    
    if not admin_exists:
        print("=" * 50)
        print("📦 INITIALISATION DE LA BASE DE DONNÉES AVEC DONNÉES GÉNÉRIQUES")
        print("=" * 50)
        
        # Importer les catégories et fonctions du seed
        from seed_data import CATEGORIES, DESCRIPTIONS, generate_realistic_amount
        
        # 1. Créer l'utilisateur ADMIN
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            email='admin@finance.com',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin créé: admin / admin123")
        
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
        
        # 3. Générer des dépenses pour chaque utilisateur
        start_date = datetime.now() - timedelta(days=90)
        total_expenses = 0
        
        for user in users_created:
            # Nombre de dépenses: entre 50 et 150 par utilisateur
            num_expenses = random.randint(50, 150)
            
            # Distribution des catégories selon l'utilisateur
            if user.username == 'admin':
                category_weights = None  # Toutes égales
            elif user.username == 'jean_dupont':
                category_weights = [0.25, 0.20, 0.10, 0.05, 0.10, 0.10, 0.05, 0.05, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
            elif user.username == 'marie_martin':
                category_weights = [0.15, 0.05, 0.20, 0.05, 0.25, 0.05, 0.05, 0.05, 0.05, 0.03, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
            else:
                category_weights = [0.15, 0.05, 0.05, 0.20, 0.05, 0.25, 0.05, 0.05, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
            
            for i in range(num_expenses):
                random_days = random.randint(0, 90)
                expense_date = start_date + timedelta(days=random_days, hours=random.randint(8, 22))
                
                # Sélection de la catégorie
                if category_weights:
                    category = random.choices(CATEGORIES, weights=category_weights)[0]
                else:
                    category = random.choice(CATEGORIES)
                
                # Montant réaliste
                amount = generate_realistic_amount(category) if 'generate_realistic_amount' in dir() else random.uniform(10, 100)
                
                # Description
                desc_list = DESCRIPTIONS.get(category, ['Dépense courante'])
                description = random.choice(desc_list)
                
                expense = Expense(
                    amount=round(amount, 2),
                    category=category,
                    description=f"{description}",
                    date=expense_date,
                    user_id=user.id
                )
                db.session.add(expense)
                total_expenses += 1
        
        db.session.commit()
        
        print(f"\n✅ DONNÉES GÉNÉRÉES AVEC SUCCÈS !")
        print(f"   - {len(users_created)} utilisateurs")
        print(f"   - {total_expenses} dépenses créées")
        print("\n🔑 COMPTES DE TEST:")
        print("   - admin / admin123")
        print("   - jean_dupont / test123")
        print("   - marie_martin / test123")
        print("   - pierre_durand / test123")
        print("=" * 50)
    else:
        print("✅ Base de données déjà initialisée")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)