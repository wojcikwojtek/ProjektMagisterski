import numpy as np
import matplotlib.pyplot as plt

def simulate_collision_trajectory():
    # --- PARAMETRY SYMULACJI ---
    N = 3.0          # Efektywna stała nawigacyjna (musi być N > 2 dla zachowania stabilności)
    dt = 0.01        # Krok czasowy symulacji [s]
    max_time = 15.0  # Maksymalny czas trwania symulacji [s]
    
    # --- WARUNKI POCZĄTKOWE (Układ Inercjalny) ---
    # Początkowe położenie i prędkość pocisku (M)
    r_M = np.array([0.0, 0.0, 0.0])       # [m]
    v_M = np.array([400.0, 50.0, 0.0])    # [m/s] (szybki pocisk lecący głównie wzdłuż osi X)
    
    # Początkowe położenie i prędkość celu (T)
    r_T = np.array([3000.0, 800.0, 200.0]) # [m] (cel oddalony w 3D)
    v_T = np.array([-100.0, -30.0, 10.0])  # [m/s] (cel poruszający się w stronę pocisku z lekkim manewrem uniku)
    
    # Listy do rejestracji trajektorii (do późniejszego wykresu)
    history_r_M = [r_M.copy()]
    history_r_T = [r_T.copy()]
    history_time = [0.0]
    
    t = 0.0
    intercepted = False
    
    print("Rozpoczęcie pętli naprowadzania...")
    
    while t < max_time:
        # =========================================================================
        # KROK 1: Definicja geometrii i kinematyki względnej
        # =========================================================================
        # Wektor położenia względnego celu względem pocisku: r = r_T - r_M
        r = r_T - r_M
        R = np.linalg.norm(r)  # Fizyczna odległość (zasięg) między obiektami
        
        # Warunek zakończenia sukcesem: zbliżenie się na odległość strefy rażenia (np. 1.5 metra)
        if R < 1.5:
            intercepted = True
            print(f" Sukces! Przechwycenie celu w czasie t = {t:.2f} s. Finałowy miss distance: {R:.4f} m")
            break
            
        # Wektor jednostkowy wzdłuż Linii Widzenia (Line-of-Sight - LOS)
        r_1 = r / R
        
        # =========================================================================
        # KROK 2: Wyznaczenie prędkości względnej i prędkości zbliżania
        # =========================================================================
        # Wektor prędkości względnej celu względem pocisku: v = v_T - v_M
        v = v_T - v_M
        
        # Prędkość zbliżania (Closing Velocity) V_c = -R_dot. 
        # R_dot to rzut prędkości względnej na wektor jednostkowy LOS.
        R_dot = np.dot(v, r_1)
        V_c = -R_dot
        
        # Matematyczny warunek konieczny kolizji: obiekty muszą fizycznie zbliżać się do siebie (V_c > 0)
        if V_c <= 0:
            print(f" Brak kolizji w t = {t:.2f} s (V_c = {V_c:.2f} m/s). Pocisk minął cel lub cel ucieka.")
            break
            
        # =========================================================================
        # KROK 3: Obliczenie prędkości kątowej obrotu Linii Widzenia (LOS Rate)
        # =========================================================================
        # Wektor prędkości kątowej obrotu układu współrzędnych LOS w przestrzeni inercjalnej:
        # omega_LOS = (r x v) / R^2
        omega_LOS = np.cross(r, v) / (R**2)
        
        # Prędkość zmiany kierunku samego wektora jednostkowego LOS w czasie: n_dot = omega_LOS x 1_r
        n_dot = np.cross(omega_LOS, r_1)
        
        # =========================================================================
        # KROK 4: Obliczenie komendy przyspieszenia (Nawigacja Proporcjonalna)
        # =========================================================================
        # Zgodnie z True Proportional Navigation (TPN), komenda przyspieszenia pocisku 
        # jest prostopadła do osi LOS i proporcjonalna do V_c oraz obrotu LOS:
        a_M_command = N * V_c * n_dot
        
        # --- Ograniczenie fizyczne (Saturacja strukturalna/aerodynamiczna) ---
        # Pociski mają limit maksymalnego przeciążenia (np. max 25G), którego nie mogą przekroczyć
        max_g = 25 * 9.81  # 25G wyrażone w m/s^2
        a_M_magnitude = np.linalg.norm(a_M_command)
        if a_M_magnitude > max_g:
            a_M_command = (a_M_command / a_M_magnitude) * max_g
            
        # =========================================================================
        # KROK 5: Aktualizacja stanów dynamicznych obiektów (Integracja numeryczna)
        # =========================================================================
        # Stosujemy metodę Eulera do wyznaczenia nowej trajektorii.
        # W podstawowym modelu przyjmuje się natychmiastową reakcję pocisku na komendę (no-lag)
        v_M += a_M_command * dt  # Przyspieszenie zmienia wektor prędkości pocisku
        r_M += v_M * dt          # Prędkość zmienia pozycję pocisku
        
        # Aktualizacja pozycji celu (zakładamy ruch ze stałą prędkością v_T)
        r_T += v_T * dt
        
        # Zapis do historii
        t += dt
        history_r_M.append(r_M.copy())
        history_r_T.append(r_T.copy())
        history_time.append(t)
        
    if not intercepted:
        print(" Koniec czasu symulacji. Nie udało się przechwycić celu.")
        
    # Konwersja historii do tablic numpy w celu wygenerowania wykresu
    history_r_M = np.array(history_r_M)
    history_r_T = np.array(history_r_T)
    
    # --- WIZUALIZACJA TRAJEKTORII 3D ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(history_r_M[:, 0], history_r_M[:, 1], history_r_M[:, 2], label='Trajektoria pocisku (M)', color='blue', linewidth=2)
    ax.plot(history_r_T[:, 0], history_r_T[:, 1], history_r_T[:, 2], label='Trajektoria celu (T)', color='red', linestyle='--', linewidth=2)
    
    # Oznaczenie punktów kluczowych
    ax.scatter(history_r_M[0, 0], history_r_M[0, 1], history_r_M[0, 2], color='blue', marker='o', s=100, label='Start Pocisku')
    ax.scatter(history_r_T[0, 0], history_r_T[0, 1], history_r_T[0, 2], color='red', marker='X', s=100, label='Start Celu')
    ax.scatter(history_r_M[-1, 0], history_r_M[-1, 1], history_r_M[-1, 2], color='green', marker='*', s=150, label='Punkt Przechwycenia')
    
    ax.set_title('Symulacja Trajektorii Kolizyjnej (Proportional Navigation)', fontsize=14)
    ax.set_xlabel('Oś X [m]')
    ax.set_ylabel('Oś Y [m]')
    ax.set_zlabel('Oś Z [m]')
    ax.legend()
    ax.grid(True)
    plt.show()

# Uruchomienie skryptu
if __name__ == "__main__":
    simulate_collision_trajectory()