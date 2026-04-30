import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, silhouette_score
from database import db, Expense, User

class DataAnalyzer:
    
    @staticmethod
    def get_expense_dataframe(user_id=None):
        """Récupère les dépenses sous forme de DataFrame"""
        if user_id:
            expenses = Expense.query.filter_by(user_id=user_id).all()
        else:
            expenses = Expense.query.all()
        
        data = []
        for exp in expenses:
            data.append({
                'id': exp.id,
                'amount': exp.amount,
                'category': exp.category,
                'description': exp.description,
                'date': exp.date,
                'user_id': exp.user_id,
                'day_of_week': exp.date.strftime('%A'),
                'month': exp.date.month,
                'day': exp.date.day,
                'hour': exp.date.hour if hasattr(exp.date, 'hour') else 12
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def linear_regression_simple(user_id=None):
        """Régression linéaire simple: prédire montant vs jour du mois"""
        df = DataAnalyzer.get_expense_dataframe(user_id)
        if len(df) < 3:
            return None
        
        # Préparation des données
        X = df['day'].values.reshape(-1, 1)
        y = df['amount'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        predictions = model.predict(X)
        
        return {
            'coefficient': model.coef_[0],
            'intercept': model.intercept_,
            'r2_score': model.score(X, y),
            'predictions': predictions.tolist()[-10:],
            'actual': y[-10:].tolist()
        }
    
    @staticmethod
    def linear_regression_multiple(user_id=None):
        """Régression linéaire multiple: prédire montant avec plusieurs variables"""
        df = DataAnalyzer.get_expense_dataframe(user_id)
        if len(df) < 5:
            return None
        
        # Encodage des variables catégorielles
        le_category = LabelEncoder()
        df['category_encoded'] = le_category.fit_transform(df['category'])
        
        le_day = LabelEncoder()
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        # Features: categorie, jour, mois, jour_semaine
        features = ['category_encoded', 'day_encoded', 'month', 'day']
        X = df[features].values
        y = df['amount'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        return {
            'coefficients': dict(zip(features, model.coef_.tolist())),
            'intercept': model.intercept_,
            'r2_score': model.score(X, y),
            'feature_importance': dict(zip(features, model.coef_.tolist()))
        }
    
    @staticmethod
    def pca_analysis(user_id=None):
        """Analyse en composantes principales"""
        df = DataAnalyzer.get_expense_dataframe(user_id)
        if len(df) < 5:
            return None
        
        # Préparation des données numériques
        le_category = LabelEncoder()
        le_day = LabelEncoder()
        
        df['category_encoded'] = le_category.fit_transform(df['category'])
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        features = ['amount', 'category_encoded', 'day_encoded', 'month', 'day']
        X = df[features].values
        
        # Standardisation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # PCA
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        return {
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'components': pca.components_.tolist(),
            'transformed_data': X_pca.tolist()[:20],
            'cumulative_variance': np.cumsum(pca.explained_variance_ratio_).tolist()
        }
    
    @staticmethod
    def supervised_classification(user_id=None):
        """Classification supervisée: prédire catégorie de dépense"""
        df = DataAnalyzer.get_expense_dataframe(user_id)
        if len(df) < 10:
            return None
        
        # Préparation
        le_category = LabelEncoder()
        y = le_category.fit_transform(df['category'])
        
        le_day = LabelEncoder()
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        features = ['amount', 'day_encoded', 'month', 'day']
        X = df[features].values
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        return {
            'accuracy': accuracy,
            'feature_importance': dict(zip(features, model.feature_importances_.tolist())),
            'n_samples': len(df),
            'n_categories': len(le_category.classes_),
            'categories': le_category.classes_.tolist()
        }
    
    @staticmethod
    def unsupervised_classification(user_id=None):
        """Classification non-supervisée: clustering des dépenses"""
        df = DataAnalyzer.get_expense_dataframe(user_id)
        if len(df) < 10:
            return None
        
        # Préparation
        le_category = LabelEncoder()
        df['category_encoded'] = le_category.fit_transform(df['category'])
        
        le_day = LabelEncoder()
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        features = ['amount', 'category_encoded', 'day_encoded', 'month', 'day']
        X = df[features].values
        
        # Standardisation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # KMeans clustering
        n_clusters = min(3, len(df) // 3)
        if n_clusters < 2:
            n_clusters = 2
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        silhouette = silhouette_score(X_scaled, clusters) if len(set(clusters)) > 1 else 0
        
        return {
            'n_clusters': n_clusters,
            'silhouette_score': silhouette,
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'cluster_distribution': np.bincount(clusters).tolist()
        }