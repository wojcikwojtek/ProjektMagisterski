import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Przygotowanie danych (przykład dla Scenariusza: Pościg, Start: 10 km na wschód)
# "None" oznacza brak kolizji (Nie dogonił / Ominął)
data = {
    'Metoda': [
        'Pure Pursuit', 'Pure Pursuit', 'Pure Pursuit', 'Pure Pursuit',
        'Predictive Interceptive Point', 'Predictive Interceptive Point', 'Predictive Interceptive Point', 'Predictive Interceptive Point',
        'Proportional Navigation', 'Proportional Navigation', 'Proportional Navigation', 'Proportional Navigation'
    ],
    'Prędkość': ['600', '1000', '1500', '2000', '600', '1000', '1500', '2000', '600', '1000', '1500', '2000'],
    'Czas': [
        573.63, 374.02, 261.13, 213.12,      # Pursuit
        561.82, 372.83, 267.15, 206.55,     # PIP
        563.89, 371.07, 260.49, 200.72            # ProNav (None = Nie dogonił)
    ],
    'Dystans': [
        343.62, 372.81, 391.13, 425.45,        # Pursuit
        336.93, 372.66, 398.35, 412.60,       # PIP
        337.94, 370.17, 390.28, 401.26          # ProNav
    ]
}

df = pd.DataFrame(data)

# 2. Ustawienia stylu wykresów
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 1, figsize=(10, 12))
fig.suptitle('Porównanie metod naprowadzania - Scenariusz: Rakieta (Punkt pierwszy)', fontsize=16)

# Kolorystyka dla metod
palette = {
    'Pure Pursuit': '#e74c3c', 
    'Predictive Interceptive Point': '#f39c12', 
    'Proportional Navigation': '#2980b9'
}

# 3. Wykres Czasu
# sns.barplot(
#     ax=axes, data=df, 
#     x='Prędkość', y='Czas', hue='Metoda', 
#     palette=palette
# )
# axes.set_title('Czas do kolizji w zależności od prędkości obiektu', fontsize=14)
# axes.set_xlabel('Prędkość [m/s]')
# axes.set_ylabel('Czas (s)')

# 4. Wykres Dystansu
sns.barplot(
    ax=axes, data=df, 
    x='Prędkość', y='Dystans', hue='Metoda', 
    palette=palette
)
axes.set_title('Przebyty dystans w zależności od prędkości obiektu', fontsize=14)
axes.set_xlabel('Prędkość [m/s]')
axes.set_ylabel('Dystans')

# Dopracowanie układu
plt.tight_layout()
plt.subplots_adjust(top=0.92)
plt.show()