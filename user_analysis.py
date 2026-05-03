# user_analysis.py
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, silhouette_score, r2_score, mean_squared_error
from datetime import datetime
import traceback

class UserDataAnalyzer:
    
    @staticmethod
    def get_user_dataframe(expenses):
        """Convertit les dépenses d'un utilisateur en DataFrame"""
        if not expenses or len(expenses) == 0:
            return pd.DataFrame()
        
        data = []
        for exp in expenses:
            try:
                data.append({
                    'id': exp.id,
                    'amount': float(exp.amount),
                    'category': str(exp.category),
                    'date': exp.date.strftime('%Y-%m-%d'),
                    'date_obj': exp.date,
                    'day_of_week': exp.date.strftime('%A'),
                    'month': exp.date.month,
                    'day': exp.date.day,
                    'week': exp.date.isocalendar()[1],
                    'is_weekend': 1 if exp.date.weekday() >= 5 else 0
                })
            except Exception as e:
                print(f"Erreur sur dépense {exp.id}: {e}")
                continue
        
        return pd.DataFrame(data)
    
    @staticmethod
    def get_statistics(expenses):
        """Statistiques descriptives de base"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if df.empty:
            return None
        
        try:
            stats = {
                'total_expenses': float(df['amount'].sum()),
                'average_expense': float(df['amount'].mean()),
                'max_expense': float(df['amount'].max()),
                'min_expense': float(df['amount'].min()),
                'std_deviation': float(df['amount'].std()),
                'median_expense': float(df['amount'].median()),
                'total_count': len(df),
                'categories_count': int(df['category'].nunique()),
            }
            
            # Dépenses par catégorie
            category_stats = df.groupby('category')['amount'].agg(['sum', 'mean', 'count']).to_dict()
            stats['category_stats'] = {
                str(cat): {
                    'total': float(vals['sum']),
                    'average': float(vals['mean']),
                    'count': int(vals['count'])
                }
                for cat, vals in category_stats.items()
            }
            
            return stats
        except Exception as e:
            print(f"Erreur stats: {e}")
            return None
    
    @staticmethod
    def linear_regression_simple(expenses):
        """Régression linéaire simple"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 3:
            return {'error': 'Pas assez de données (minimum 3 dépenses requis)'}
        
        try:
            df_sorted = df.sort_values('date_obj')
            X = np.arange(len(df_sorted)).reshape(-1, 1)
            y = df_sorted['amount'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            predictions = model.predict(X)
            r2 = r2_score(y, predictions)
            rmse = np.sqrt(mean_squared_error(y, predictions))
            
            future_X = np.arange(len(df_sorted), len(df_sorted) + 7).reshape(-1, 1)
            future_predictions = model.predict(future_X)
            
            trend = "hausse" if model.coef_[0] > 0 else "baisse" if model.coef_[0] < 0 else "stable"
            
            return {
                'success': True,
                'coefficient': float(model.coef_[0]),
                'intercept': float(model.intercept_),
                'r2_score': float(r2),
                'rmse': float(rmse),
                'trend': trend,
                'predictions': [float(p) for p in predictions[-10:]],
                'actual': [float(a) for a in y[-10:]],
                'future_predictions': [float(p) for p in future_predictions],
                'data_points': len(df),
                'x_values': [int(i) for i in range(len(y))],
                'x_values_future': [int(i) for i in range(len(y), len(y) + 7)]
            }
        except Exception as e:
            print(f"Erreur regression simple: {e}")
            traceback.print_exc()
            return {'error': f'Erreur analyse: {str(e)}'}
    
    @staticmethod
    def linear_regression_multiple(expenses):
        """Régression linéaire multiple"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 5:
            return {'error': 'Pas assez de données (minimum 5 dépenses requis)'}
        
        try:
            df['day_num'] = df['date_obj'].dt.weekday
            df['month_num'] = df['date_obj'].dt.month
            
            features = ['day_num', 'month_num', 'is_weekend']
            X = df[features].values
            y = df['amount'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            predictions = model.predict(X)
            r2 = r2_score(y, predictions)
            rmse = np.sqrt(mean_squared_error(y, predictions))
            
            feature_importance = {features[i]: float(model.coef_[i]) for i in range(len(features))}
            
            return {
                'success': True,
                'coefficients': feature_importance,
                'intercept': float(model.intercept_),
                'r2_score': float(r2),
                'rmse': float(rmse),
                'feature_names': features,
                'feature_values': [float(c) for c in model.coef_]
            }
        except Exception as e:
            return {'error': f'Erreur: {str(e)}'}
    
    @staticmethod
    def pca_analysis(expenses):
        """Analyse PCA"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 5:
            return {'error': 'Pas assez de données (minimum 5 dépenses requis)'}
        
        try:
            df['day_num'] = df['date_obj'].dt.weekday
            df['month_num'] = df['date_obj'].dt.month
            
            # Encodage des catégories
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            df['category_encoded'] = le.fit_transform(df['category'])
            
            features = ['amount', 'category_encoded', 'day_num', 'month_num', 'is_weekend']
            X = df[features].values
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            return {
                'success': True,
                'explained_variance_ratio': [float(v) for v in pca.explained_variance_ratio_],
                'points': [[float(x), float(y)] for x, y in X_pca],
                'categories': df['category'].tolist()
            }
        except Exception as e:
            return {'error': f'Erreur: {str(e)}'}
    
    @staticmethod
    def supervised_classification(expenses):
        """Classification supervisée"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 10:
            return {'error': 'Pas assez de données (minimum 10 dépenses requis)'}
        
        if df['category'].nunique() < 2:
            return {'error': 'Besoin d\'au moins 2 catégories différentes'}
        
        try:
            df['day_num'] = df['date_obj'].dt.weekday
            df['month_num'] = df['date_obj'].dt.month
            
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            y = le.fit_transform(df['category'])
            
            features = ['amount', 'day_num', 'month_num', 'is_weekend']
            X = df[features].values
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            importance = {features[i]: float(model.feature_importances_[i]) for i in range(len(features))}
            
            return {
                'success': True,
                'accuracy': float(accuracy),
                'feature_importance': importance,
                'feature_names': features,
                'importance_values': [float(v) for v in model.feature_importances_]
            }
        except Exception as e:
            return {'error': f'Erreur: {str(e)}'}
    
    @staticmethod
    def unsupervised_classification(expenses):
        """Classification non-supervisée"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 10:
            return {'error': 'Pas assez de données (minimum 10 dépenses requis)'}
        
        try:
            df['day_num'] = df['date_obj'].dt.weekday
            df['month_num'] = df['date_obj'].dt.month
            
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            df['category_encoded'] = le.fit_transform(df['category'])
            
            features = ['amount', 'category_encoded', 'day_num', 'month_num', 'is_weekend']
            X = df[features].values
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            n_clusters = min(3, max(2, len(df) // 5))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            silhouette = silhouette_score(X_scaled, clusters) if len(set(clusters)) > 1 else 0
            
            # Analyse des clusters
            cluster_stats = []
            for i in range(n_clusters):
                mask = clusters == i
                cluster_stats.append({
                    'id': i,
                    'size': int(np.sum(mask)),
                    'avg_amount': float(df[mask]['amount'].mean()),
                    'percentage': float(np.mean(mask) * 100)
                })
            
            return {
                'success': True,
                'n_clusters': n_clusters,
                'silhouette_score': float(silhouette),
                'clusters': [int(c) for c in clusters],
                'cluster_stats': cluster_stats,
                'points': [[float(x[0]), float(x[1])] for x in X_scaled[:, :2]]
            }
        except Exception as e:
            return {'error': f'Erreur: {str(e)}'}