// static/js/charts.js
// Bibliothèque de fonctions pour les graphiques avancés

class FinanceCharts {
    constructor() {
        this.colors = {
            violet: ['#6a1b9a', '#9c27b0', '#ce93d8', '#e1bee7', '#f3e5f5'],
            green: ['#2e7d32', '#66bb6a', '#a5d6a7', '#c8e6c9', '#e8f5e9'],
            mix: ['#6a1b9a', '#2e7d32', '#9c27b0', '#66bb6a', '#ce93d8']
        };
    }
    
    // Graphique en camembert
    createPieChart(elementId, data, title = 'Distribution') {
        const trace = {
            values: Object.values(data),
            labels: Object.keys(data),
            type: 'pie',
            marker: {
                colors: this.colors.violet,
                line: { color: 'white', width: 2 }
            },
            textinfo: 'label+percent',
            textposition: 'auto',
            hoverinfo: 'label+value+percent',
            hole: 0.4
        };
        
        const layout = {
            title: {
                text: title,
                font: { size: 18, family: 'Segoe UI, sans-serif', color: '#6a1b9a' }
            },
            showlegend: true,
            legend: { x: 1, y: 0.5, bgcolor: 'rgba(255,255,255,0.8)' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            annotations: [{
                text: `Total: ${Object.values(data).reduce((a,b) => a+b, 0).toFixed(0)}Fcfa`,
                showarrow: false,
                font: { size: 14, color: '#6a1b9a' }
            }]
        };
        
        Plotly.newPlot(elementId, [trace], layout, { responsive: true });
    }
    
    // Graphique en barres
    createBarChart(elementId, data, title = 'Analyse', xLabel = 'Catégories', yLabel = 'Montant (Fcfa)') {
        const trace = {
            x: Object.keys(data),
            y: Object.values(data),
            type: 'bar',
            marker: {
                color: this.colors.mix,
                line: { color: 'white', width: 1.5 }
            },
            text: Object.values(data).map(v => v.toFixed(2) + 'Fcfa'),
            textposition: 'auto',
            textfont: { color: '#333', size: 11 }
        };
        
        const layout = {
            title: {
                text: title,
                font: { size: 18, color: '#6a1b9a' }
            },
            xaxis: {
                title: xLabel,
                tickangle: -45,
                gridcolor: '#e0e0e0'
            },
            yaxis: {
                title: yLabel,
                gridcolor: '#e0e0e0',
                zerolinecolor: '#6a1b9a'
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            bargap: 0.3
        };
        
        Plotly.newPlot(elementId, [trace], layout, { responsive: true });
    }
    
    // Graphique linéaire (évolution temporelle)
    createLineChart(elementId, dates, values, title = 'Évolution', yLabel = 'Montant (Fcfa)') {
        const trace = {
            x: dates,
            y: values,
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: '#6a1b9a',
                width: 3,
                shape: 'spline'
            },
            marker: {
                color: '#2e7d32',
                size: 8,
                symbol: 'circle'
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(106, 27, 154, 0.1)'
        };
        
        const layout = {
            title: {
                text: title,
                font: { size: 18, color: '#6a1b9a' }
            },
            xaxis: {
                title: 'Date',
                gridcolor: '#e0e0e0',
                type: 'date'
            },
            yaxis: {
                title: yLabel,
                gridcolor: '#e0e0e0',
                zerolinecolor: '#6a1b9a'
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            hovermode: 'closest'
        };
        
        Plotly.newPlot(elementId, [trace], layout, { responsive: true });
    }
    
    // Graphique de clustering (PCA)
    createPCAPlot(elementId, points, clusters = null) {
        let trace;
        
        if (clusters) {
            // Points colorés par cluster
            const uniqueClusters = [...new Set(clusters)];
            const traces = uniqueClusters.map(cluster => {
                const indices = clusters.map((c, idx) => c === cluster ? idx : -1).filter(i => i !== -1);
                return {
                    x: indices.map(i => points[i][0]),
                    y: indices.map(i => points[i][1]),
                    mode: 'markers',
                    type: 'scatter',
                    name: `Cluster ${cluster}`,
                    marker: {
                        size: 10,
                        colors: this.colors.mix[cluster % this.colors.mix.length]
                    }
                };
            });
            Plotly.newPlot(elementId, traces, this.getPCALayout());
        } else {
            trace = {
                x: points.map(p => p[0]),
                y: points.map(p => p[1]),
                mode: 'markers',
                type: 'scatter',
                marker: {
                    size: 10,
                    color: points.map(p => p[0]),
                    colorscale: 'Viridis',
                    showscale: true,
                    colorbar: { title: 'Composante 1' }
                }
            };
            Plotly.newPlot(elementId, [trace], this.getPCALayout());
        }
    }
    
    getPCALayout() {
        return {
            title: 'Visualisation PCA - Réduction de dimensionnalité',
            xaxis: { title: 'Première composante principale', gridcolor: '#e0e0e0' },
            yaxis: { title: 'Deuxième composante principale', gridcolor: '#e0e0e0' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            hovermode: 'closest'
        };
    }
    
    // Graphique de prédiction vs réel
    createPredictionChart(elementId, actual, predicted) {
        const trace1 = {
            x: Array.from({ length: actual.length }, (_, i) => i + 1),
            y: actual,
            name: 'Valeurs réelles',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#2e7d32', width: 2 },
            marker: { color: '#2e7d32', size: 6 }
        };
        
        const trace2 = {
            x: Array.from({ length: predicted.length }, (_, i) => i + 1),
            y: predicted,
            name: 'Prédictions',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#6a1b9a', width: 2, dash: 'dash' },
            marker: { color: '#9c27b0', size: 6 }
        };
        
        const layout = {
            title: 'Régression - Prédictions vs Réalité',
            xaxis: { title: 'Échantillon', gridcolor: '#e0e0e0' },
            yaxis: { title: 'Montant (Fcfa)', gridcolor: '#e0e0e0' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            legend: { x: 0.02, y: 0.98, bgcolor: 'rgba(255,255,255,0.8)' }
        };
        
        Plotly.newPlot(elementId, [trace1, trace2], layout, { responsive: true });
    }
    
    // Dashboard heatmap (corrélations)
    createHeatmap(elementId, data, categories) {
        const trace = {
            z: data,
            x: categories,
            y: categories,
            type: 'heatmap',
            colorscale: [
                [0, '#e8f5e9'],
                [0.5, '#ce93d8'],
                [1, '#6a1b9a']
            ],
            showscale: true,
            colorbar: { title: 'Corrélation' }
        };
        
        const layout = {
            title: 'Matrice de corrélation des dépenses',
            xaxis: { title: 'Catégories', tickangle: -45 },
            yaxis: { title: 'Catégories' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            width: 600,
            height: 500
        };
        
        Plotly.newPlot(elementId, [trace], layout, { responsive: true });
    }
    
    // Export graphique en image
    exportChart(elementId, format = 'png') {
        Plotly.downloadImage(elementId, {
            format: format,
            width: 1200,
            height: 800,
            filename: `finance_chart_${Date.now()}`
        });
    }
}

// Initialisation globale
const financeCharts = new FinanceCharts();

// Fonctions utilitaires pour l'administration
function loadCategoryChart() {
    $.get('/api/categories_stats', function(data) {
        financeCharts.createBarChart('categoryChart', data, 'Distribution des dépenses par catégorie');
    });
}

function loadUserComparison() {
    $.get('/api/users_stats', function(data) {
        const userTotals = {};
        data.forEach(user => {
            userTotals[user.username] = user.total_amount;
        });
        financeCharts.createBarChart('userComparison', userTotals, 'Comparaison des dépenses par utilisateur', 'Utilisateurs', 'Total dépenses (Fcfa)');
    });
}

// Auto-initialisation au chargement de la page
$(document).ready(function() {
    console.log('Finance Charts initialized');
    
    // Ajouter un loader personnalisé
    $('body').append('<div class="loading-overlay" id="loadingOverlay"><div class="loader"></div></div>');
    setTimeout(() => {
        $('#loadingOverlay').remove();
    }, 2000);
});