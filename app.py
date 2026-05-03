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
    

# Ajout des routes d'analyse utilisateur
from user_analysis import UserDataAnalyzer

@app.route('/my_analysis')
@login_required
def my_analysis():
    """Page d'analyse personnelle pour l'utilisateur connecté"""
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    
    stats = UserDataAnalyzer.get_statistics(expenses)
    
    return render_template('my_analysis.html', 
                         user=user, 
                         stats=stats,
                         has_data=len(expenses) > 0,
                         expenses_count=len(expenses))

@app.route('/api/my_analysis/simple_regression')
@login_required
def my_simple_regression():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.linear_regression_simple(expenses)
    return jsonify(result)

@app.route('/api/my_analysis/multiple_regression')
@login_required
def my_multiple_regression():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.linear_regression_multiple(expenses)
    return jsonify(result)

@app.route('/api/my_analysis/pca')
@login_required
def my_pca():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.pca_analysis(expenses)
    return jsonify(result)

@app.route('/api/my_analysis/supervised')
@login_required
def my_supervised():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.supervised_classification(expenses)
    return jsonify(result)

@app.route('/api/my_analysis/unsupervised')
@login_required
def my_unsupervised():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.unsupervised_classification(expenses)
    return jsonify(result)

@app.route('/api/my_analysis/advice')
@login_required
def my_advice():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.get_forecast_advice(expenses)
    return jsonify(result)

@app.route('/api/my_analysis/stats')
@login_required
def my_stats():
    user = User.query.get(session['user_id'])
    expenses = Expense.query.filter_by(user_id=user.id).all()
    result = UserDataAnalyzer.get_statistics(expenses)
    return jsonify(result)


# Routes API pour analyses utilisateur (VERSION CORRIGÉE)
@app.route('/api/my_analysis/simple_regression')
@login_required
def my_simple_regression():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.linear_regression_simple(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/my_analysis/multiple_regression')
@login_required
def my_multiple_regression():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.linear_regression_multiple(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/my_analysis/pca')
@login_required
def my_pca():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.pca_analysis(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/my_analysis/supervised')
@login_required
def my_supervised():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.supervised_classification(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/my_analysis/unsupervised')
@login_required
def my_unsupervised():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.unsupervised_classification(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/my_analysis/advice')
@login_required
def my_advice():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.get_forecast_advice(expenses)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'advice': []})

@app.route('/api/my_analysis/stats')
@login_required
def my_stats():
    try:
        user = User.query.get(session['user_id'])
        expenses = Expense.query.filter_by(user_id=user.id).all()
        result = UserDataAnalyzer.get_statistics(expenses)
        return jsonify(result if result else {'error': 'Pas de données'})
    except Exception as e:
        return jsonify({'error': str(e)})
    
    
# Création des tables et données de test
with app.app_context():
    db.create_all()
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            email='admin@finance.com',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            username='testuser',
            password=generate_password_hash('test123'),
            email='test@email.com',
            is_admin=False
        )
        db.session.add(test_user)
        db.session.commit()
        
        categories_list = ['Alimentation', 'Transport', 'Loisirs', 'Santé', 'Shopping', 'Factures']
        for i in range(50):
            expense = Expense(
                amount=10 + (i * 5) % 150,
                category=categories_list[i % len(categories_list)],
                description=f'Dépense test {i+1}',
                date=datetime.now() - timedelta(days=i),
                user_id=test_user.id
            )
            db.session.add(expense)
        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)