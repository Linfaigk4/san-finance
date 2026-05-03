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
from datetime import datetime, timedelta
import json

class UserDataAnalyzer:
    
    @staticmethod
    def get_user_dataframe(expenses):
        """Convertit les dépenses d'un utilisateur en DataFrame"""
        if not expenses:
            return pd.DataFrame()
        
        data = []
        for exp in expenses:
            data.append({
                'id': exp.id,
                'amount': exp.amount,
                'category': exp.category,
                'description': exp.description,
                'date': exp.date.strftime('%Y-%m-%d'),
                'date_obj': exp.date,
                'day_of_week': exp.date.strftime('%A'),
                'day_num': exp.date.weekday(),
                'month': exp.date.month,
                'day': exp.date.day,
                'hour': exp.date.hour if hasattr(exp.date, 'hour') else 12,
                'week': exp.date.isocalendar()[1],
                'is_weekend': 1 if exp.date.weekday() >= 5 else 0
            })
        
        df = pd.DataFrame(data)
        return df
    
    @staticmethod
    def get_statistics(expenses):
        """Statistiques descriptives de base"""
        if not expenses:
            return None
        
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        
        stats = {
            'total_expenses': df['amount'].sum(),
            'average_expense': df['amount'].mean(),
            'max_expense': df['amount'].max(),
            'min_expense': df['amount'].min(),
            'std_deviation': df['amount'].std(),
            'median_expense': df['amount'].median(),
            'total_count': len(df),
            'categories_count': df['category'].nunique(),
            'period_days': (datetime.now() - pd.to_datetime(df['date']).min()).days if len(df) > 0 else 0,
            'daily_average': df['amount'].sum() / max(1, (datetime.now() - pd.to_datetime(df['date']).min()).days)
        }
        
        # Dépenses par catégorie
        category_stats = df.groupby('category')['amount'].agg(['sum', 'mean', 'count']).to_dict()
        stats['category_stats'] = {
            cat: {
                'total': float(vals['sum']),
                'average': float(vals['mean']),
                'count': int(vals['count'])
            }
            for cat, vals in category_stats.items()
        }
        
        # Dépenses par jour de semaine
        weekday_stats = df.groupby('day_of_week')['amount'].sum().to_dict()
        stats['weekday_stats'] = weekday_stats
        
        return stats
    
    @staticmethod
    def linear_regression_simple(expenses):
        """Régression linéaire simple: prédire montant vs jour"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 3:
            return {'error': 'Pas assez de données (minimum 3 dépenses requis)'}
        
        # Préparation des données
        df_sorted = df.sort_values('date_obj')
        X = np.arange(len(df_sorted)).reshape(-1, 1)
        y = df_sorted['amount'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        predictions = model.predict(X)
        
        # Métriques
        r2 = r2_score(y, predictions)
        rmse = np.sqrt(mean_squared_error(y, predictions))
        
        # Prévisions pour les 7 prochains jours
        future_X = np.arange(len(df_sorted), len(df_sorted) + 7).reshape(-1, 1)
        future_predictions = model.predict(future_X)
        
        # Détection de tendance
        trend = "📈 En hausse" if model.coef_[0] > 0 else "📉 En baisse" if model.coef_[0] < 0 else "➡️ Stable"
        
        return {
            'coefficient': float(model.coef_[0]),
            'intercept': float(model.intercept_),
            'r2_score': float(r2),
            'rmse': float(rmse),
            'trend': trend,
            'predictions': [float(p) for p in predictions[-10:]],
            'actual': [float(a) for a in y[-10:]],
            'future_predictions': [float(p) for p in future_predictions],
            'data_points': len(df),
            'interpretation': f"Chaque jour, vos dépenses {trend.lower()} de {abs(model.coef_[0]):.2f}€ en moyenne."
        }
    
    @staticmethod
    def linear_regression_multiple(expenses):
        """Régression linéaire multiple avec plusieurs variables"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 5:
            return {'error': 'Pas assez de données (minimum 5 dépenses requis)'}
        
        # Encodage des variables
        le_day = LabelEncoder()
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        # Features: jour_semaine, mois, jour_du_mois, weekend
        features = ['day_encoded', 'month', 'day', 'is_weekend']
        X = df[features].values
        y = df['amount'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        predictions = model.predict(X)
        r2 = r2_score(y, predictions)
        rmse = np.sqrt(mean_squared_error(y, predictions))
        
        # Importance des features
        feature_importance = dict(zip(features, model.coef_.tolist()))
        
        # Analyse des facteurs influents
        insights = []
        for feature, coef in feature_importance.items():
            if abs(coef) > 0.1:
                direction = "augmente" if coef > 0 else "diminue"
                insights.append(f"• {feature}: {direction} vos dépenses de {abs(coef):.2f}€")
        
        return {
            'coefficients': feature_importance,
            'intercept': float(model.intercept_),
            'r2_score': float(r2),
            'rmse': float(rmse),
            'predictions': [float(p) for p in predictions[-10:]],
            'actual': [float(a) for a in y[-10:]],
            'insights': insights,
            'top_factor': max(feature_importance, key=feature_importance.get),
            'model_quality': "Excellent" if r2 > 0.7 else "Bon" if r2 > 0.5 else "Moyen" if r2 > 0.3 else "À améliorer"
        }
    
    @staticmethod
    def pca_analysis(expenses):
        """Analyse en composantes principales - Réduction de dimensionnalité"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 5:
            return {'error': 'Pas assez de données (minimum 5 dépenses requis)'}
        
        # Préparation des features
        le_category = LabelEncoder()
        le_day = LabelEncoder()
        
        df['category_encoded'] = le_category.fit_transform(df['category'])
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        features = ['amount', 'category_encoded', 'day_encoded', 'month', 'day', 'is_weekend']
        X = df[features].values
        
        # Standardisation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # PCA avec toutes les composantes
        pca_full = PCA()
        pca_full.fit(X_scaled)
        
        # PCA pour visualisation (2D)
        pca_2d = PCA(n_components=2)
        X_pca_2d = pca_2d.fit_transform(X_scaled)
        
        # PCA pour réduction (3D)
        pca_3d = PCA(n_components=3)
        X_pca_3d = pca_3d.fit_transform(X_scaled)
        
        # Variance expliquée
        explained_variance = pca_full.explained_variance_ratio_.tolist()
        cumulative_variance = np.cumsum(explained_variance).tolist()
        
        # Nombre de composantes pour 95% de variance
        n_components_95 = np.argmax(cumulative_variance >= 0.95) + 1
        
        return {
            'explained_variance': explained_variance[:5],
            'cumulative_variance': cumulative_variance[:5],
            'n_components_95': int(n_components_95),
            'pca_2d': [[float(x), float(y)] for x, y in X_pca_2d],
            'pca_3d': [[float(x), float(y), float(z)] for x, y, z in X_pca_3d],
            'components': [comp.tolist() for comp in pca_2d.components_],
            'dimension_reduction': f"Réduction de {len(features)} dimensions à 2 dimensions avec {pca_2d.explained_variance_ratio_[0]*100:.1f}% de variance conservée",
            'optimal_components': f"Pour conserver 95% de l'information, utilisez {n_components_95} composantes au lieu de {len(features)}"
        }
    
    @staticmethod
    def supervised_classification(expenses):
        """Classification supervisée: prédire la catégorie de dépense"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 10:
            return {'error': 'Pas assez de données (minimum 10 dépenses requis)'}
        
        # Vérifier assez de catégories
        if df['category'].nunique() < 2:
            return {'error': 'Besoin d\'au moins 2 catégories différentes'}
        
        # Préparation
        le_category = LabelEncoder()
        y = le_category.fit_transform(df['category'])
        
        le_day = LabelEncoder()
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        features = ['amount', 'day_encoded', 'month', 'day', 'is_weekend']
        X = df[features].values
        
        # Split avec stratification
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Feature importance
        feature_importance = dict(zip(features, model.feature_importances_.tolist()))
        
        # Prédiction pour une nouvelle dépense
        sample_amount = df['amount'].mean()
        sample_day = df['day_encoded'].mode()[0] if len(df) > 0 else 0
        sample_month = datetime.now().month
        sample_day_num = datetime.now().day
        sample_weekend = 1 if datetime.now().weekday() >= 5 else 0
        
        sample_features = [[sample_amount, sample_day, sample_month, sample_day_num, sample_weekend]]
        predicted_category = le_category.inverse_transform(model.predict(sample_features))[0]
        
        return {
            'accuracy': float(accuracy),
            'feature_importance': feature_importance,
            'n_samples': len(df),
            'n_categories': len(le_category.classes_),
            'categories': le_category.classes_.tolist(),
            'predicted_category_example': predicted_category,
            'confidence': float(max(model.predict_proba(sample_features)[0])),
            'model_performance': "Très bon" if accuracy > 0.8 else "Bon" if accuracy > 0.6 else "À améliorer",
            'most_important_feature': max(feature_importance, key=feature_importance.get)
        }
    
    @staticmethod
    def unsupervised_classification(expenses):
        """Classification non-supervisée: clustering des dépenses"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 10:
            return {'error': 'Pas assez de données (minimum 10 dépenses requis)'}
        
        # Préparation
        le_category = LabelEncoder()
        df['category_encoded'] = le_category.fit_transform(df['category'])
        
        le_day = LabelEncoder()
        df['day_encoded'] = le_day.fit_transform(df['day_of_week'])
        
        features = ['amount', 'category_encoded', 'day_encoded', 'month', 'day', 'is_weekend']
        X = df[features].values
        
        # Standardisation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Déterminer le nombre optimal de clusters (Elbow method)
        inertias = []
        k_range = range(2, min(6, len(df) // 3 + 1))
        if len(k_range) == 0:
            k_range = [2]
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)
        
        # Meilleur k basé sur la difference entre inerties
        if len(inertias) > 1:
            diffs = np.diff(inertias)
            best_k = k_range[np.argmax(diffs) + 1] if len(diffs) > 0 else 2
        else:
            best_k = 2
        
        n_clusters = min(best_k, len(df) // 3)
        if n_clusters < 2:
            n_clusters = 2
        
        # KMeans final
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        silhouette = silhouette_score(X_scaled, clusters) if len(set(clusters)) > 1 else 0
        
        # Analyse des clusters
        df['cluster'] = clusters
        cluster_profiles = []
        for i in range(n_clusters):
            cluster_data = df[df['cluster'] == i]
            cluster_profiles.append({
                'cluster_id': i,
                'size': len(cluster_data),
                'avg_amount': float(cluster_data['amount'].mean()),
                'top_category': cluster_data['category'].mode()[0] if len(cluster_data) > 0 else 'N/A',
                'percentage': float(len(cluster_data) / len(df) * 100)
            })
        
        return {
            'n_clusters': n_clusters,
            'silhouette_score': float(silhouette),
            'cluster_profiles': cluster_profiles,
            'optimal_k': n_clusters,
            'quality': "Excellent" if silhouette > 0.7 else "Bon" if silhouette > 0.5 else "Acceptable" if silhouette > 0.3 else "Peu distinct",
            'inertia': float(kmeans.inertia_),
            'cluster_centers': [center.tolist() for center in kmeans.cluster_centers_]
        }
    
    @staticmethod
    def get_forecast_advice(expenses):
        """Génère des conseils personnalisés basés sur les analyses"""
        df = UserDataAnalyzer.get_user_dataframe(expenses)
        if len(df) < 5:
            return {'error': 'Pas assez de données pour des conseils'}
        
        advice = []
        
        # Analyse de tendance
        simple_reg = UserDataAnalyzer.linear_regression_simple(expenses)
        if 'error' not in simple_reg:
            if simple_reg['coefficient'] > 0:
                advice.append({
                    'type': 'warning',
                    'title': '📈 Tendance à la hausse',
                    'message': f'Vos dépenses augmentent de {simple_reg["coefficient"]:.2f}€ par jour. Essayez d\'identifier les causes.',
                    'action': 'Revoyez votre budget mensuel'
                })
            elif simple_reg['coefficient'] < 0:
                advice.append({
                    'type': 'success',
                    'title': '📉 Tendance à la baisse',
                    'message': f'Vos dépenses diminuent de {abs(simple_reg["coefficient"]):.2f}€ par jour. Continuez vos efforts !',
                    'action': 'Maintenez cette dynamique'
                })
        
        # Analyse des catégories
        category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        top_category = category_spending.index[0] if len(category_spending) > 0 else None
        top_percentage = (category_spending.iloc[0] / df['amount'].sum() * 100) if len(category_spending) > 0 else 0
        
        if top_percentage > 40:
            advice.append({
                'type': 'info',
                'title': '🎯 Concentration des dépenses',
                'message': f'{top_percentage:.1f}% de vos dépenses vont dans "{top_category}".',
                'action': f'Essayez de réduire les dépenses dans cette catégorie'
            })
        
        # Analyse des weekends
        weekend_avg = df[df['is_weekend'] == 1]['amount'].mean() if len(df[df['is_weekend'] == 1]) > 0 else 0
        weekday_avg = df[df['is_weekend'] == 0]['amount'].mean() if len(df[df['is_weekend'] == 0]) > 0 else 0
        
        if weekend_avg > weekday_avg * 1.5:
            advice.append({
                'type': 'warning',
                'title': '💰 Dépenses du weekend',
                'message': f'Vous dépensez {((weekend_avg/weekday_avg)-1)*100:.0f}% de plus le weekend.',
                'action': 'Planifiez vos activités du weekend à l\'avance'
            })
        
        # Prédiction pour demain
        if 'future_predictions' in simple_reg:
            tomorrow_pred = simple_reg['future_predictions'][0]
            avg_daily = df['amount'].mean()
            if tomorrow_pred > avg_daily * 1.3:
                advice.append({
                    'type': 'info',
                    'title': '🔮 Prédiction pour demain',
                    'message': f'Selon nos modèles, vous pourriez dépenser {tomorrow_pred:.2f}€ demain.',
                    'action': 'Préparez-vous à cette dépense prévue'
                })
        
        return advice