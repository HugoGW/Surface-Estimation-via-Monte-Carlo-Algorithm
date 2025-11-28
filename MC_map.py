import pygame
import numpy as np
from numba import jit, prange
import math

# Initialisation de Pygame
pygame.init()

# Chargement de l'image de la carte
image_path = "/home/hugo-alexandre/pCloudDrive/Python/code_python_1m2p/MC_map/France_map.png"
image = pygame.image.load(image_path)

# Création de la fenêtre
screen = pygame.display.set_mode(image.get_size())
pygame.display.set_caption("Carte interactive")

# Police pour l'affichage des valeurs de l'échelle
font = pygame.font.Font(None, 36)

# Distance à partir de laquelle on masque l'encart d'instruction
INSTRUCTION_HIDE_DISTANCE = 150

# Variables globales
traces = []
current_trace = []
scale_lines = []
scale_labels = []
measuring = False
measure_start = None
input_active = False
input_text = ""
latest_distance = None
scale_ratio = None
estimated_area_km2 = None
current_step = "draw_contour"  # Étapes: draw_contour, set_scale, calculating, done


@jit(nopython=True)
def ccw(ax, ay, bx, by, cx, cy):
    """Test de sens trigonométrique optimisé"""
    return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)


@jit(nopython=True)
def segments_intersect_numba(p1x, p1y, p2x, p2y, q1x, q1y, q2x, q2y):
    """Vérifie si deux segments s'intersectent (optimisé Numba)"""
    return (ccw(p1x, p1y, q1x, q1y, q2x, q2y) != ccw(p2x, p2y, q1x, q1y, q2x, q2y) and
            ccw(p1x, p1y, p2x, p2y, q1x, q1y) != ccw(p1x, p1y, p2x, p2y, q2x, q2y))


@jit(nopython=True)
def check_intersection_numba(segments):
    """Vérifie les intersections entre segments (parallélisé)"""
    n = len(segments)
    for i in range(n):
        for j in range(i + 1, n):
            if segments_intersect_numba(
                segments[i, 0, 0], segments[i, 0, 1],
                segments[i, 1, 0], segments[i, 1, 1],
                segments[j, 0, 0], segments[j, 0, 1],
                segments[j, 1, 0], segments[j, 1, 1]
            ):
                return True
    return False


@jit(nopython=True, parallel=True)
def point_in_polygon_batch(points_x, points_y, polygon):
    """Teste si des points sont dans un polygone (parallélisé avec Numba)"""
    n_points = len(points_x)
    n_vertices = len(polygon)
    results = np.zeros(n_points, dtype=np.bool_)
    
    for idx in prange(n_points):
        x, y = points_x[idx], points_y[idx]
        inside = False
        
        j = n_vertices - 1
        for i in range(n_vertices):
            xi, yi = polygon[i, 0], polygon[i, 1]
            xj, yj = polygon[j, 0], polygon[j, 1]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        results[idx] = inside
    
    return results


@jit(nopython=True, parallel=True)
def estimate_area_monte_carlo(min_x, max_x, min_y, max_y, polygon, num_samples, seed=42):
    """Estimation de surface par Monte Carlo (parallélisé)"""
    np.random.seed(seed)
    
    # Génération de tous les points aléatoires en une fois
    x_coords = np.random.randint(min_x, max_x + 1, num_samples)
    y_coords = np.random.randint(min_y, max_y + 1, num_samples)
    
    # Test parallélisé
    inside = point_in_polygon_batch(x_coords, y_coords, polygon)
    
    points_inside = np.sum(inside)
    bounding_box_area = (max_x - min_x) * (max_y - min_y)
    estimated_area = (points_inside / num_samples) * bounding_box_area
    
    return estimated_area, points_inside


def is_mouse_near_rect(pos, rect, distance):
    """Renvoie True si la souris est à moins de `distance` pixels du rectangle."""
    expanded = rect.inflate(distance * 2, distance * 2)
    return expanded.collidepoint(pos)


def draw():
    """Fonction d'affichage optimisée"""
    screen.blit(image, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    
    # Dessiner tous les tracés
    for trace in traces:
        if len(trace) > 1:
            pygame.draw.lines(screen, (255, 0, 0), False, trace, 2)
    
    if len(current_trace) > 1:
        pygame.draw.lines(screen, (255, 0, 0), False, current_trace, 2)
    
    # Dessiner les lignes d'échelle
    for i, line in enumerate(scale_lines):
        pygame.draw.line(screen, (0, 255, 0), line[0], line[1], 2)
        text_surface = font.render(scale_labels[i], True, (0, 0, 0))
        mid_x = (line[0][0] + line[1][0]) // 2
        mid_y = (line[0][1] + line[1][1]) // 2 - 40
        screen.blit(text_surface, (mid_x - text_surface.get_width() // 2, mid_y))
    
    # Affichage des instructions selon l'étape
    instruction_text = ""
    instruction_color = (0, 0, 0)
    
    if current_step == "draw_contour":
        instruction_text = "ÉTAPE 1 : Dessinez le contour puis appuyez sur ENTRÉE"
        instruction_color = (255, 100, 0)
    elif current_step == "set_scale":
        if measure_start is None:
            instruction_text = "ÉTAPE 2 : Cliquez sur le DÉBUT de la ligne d'échelle"
            instruction_color = (0, 150, 0)
        else:
            instruction_text = "ÉTAPE 2 : Cliquez sur la FIN de la ligne d'échelle"
            instruction_color = (0, 150, 0)
    elif current_step == "calculating":
        instruction_text = "CALCUL EN COURS... Veuillez patienter"
        instruction_color = (200, 0, 200)
    elif current_step == "done":
        instruction_text = "Calcul Terminé... (Appuyez sur DELETE pour recommencer)"
        instruction_color = (0, 100, 200)
    
    # Affichage de l'instruction principale
    if instruction_text:
        inst_surface = font.render(instruction_text, True, instruction_color)
        inst_bg_rect = pygame.Rect(10, 10, inst_surface.get_width() + 20, inst_surface.get_height() + 10)
        # Masque l'encart si la souris est trop proche pour libérer la vue
        if not is_mouse_near_rect(mouse_pos, inst_bg_rect, INSTRUCTION_HIDE_DISTANCE):
            pygame.draw.rect(screen, (255, 255, 255), inst_bg_rect)
            pygame.draw.rect(screen, instruction_color, inst_bg_rect, 3)
            screen.blit(inst_surface, (inst_bg_rect.x + 10, inst_bg_rect.y + 5))
    
    # Interface de saisie de la distance
    if input_active:
        input_surface = font.render(f"Distance réelle (km) : {input_text}", True, (0, 0, 0))
        input_bg_rect = pygame.Rect(10, 70, input_surface.get_width() + 20, input_surface.get_height() + 10)
        pygame.draw.rect(screen, (255, 255, 255), input_bg_rect)
        pygame.draw.rect(screen, (0, 150, 0), input_bg_rect, 3)
        screen.blit(input_surface, (input_bg_rect.x + 10, input_bg_rect.y + 5))
    
    # Affichage de la surface
    if estimated_area_km2 is not None:
        area_surface = font.render(f"Surface estimée : {estimated_area_km2:.2f} km²", True, (0, 100, 200))
        area_bg_rect = pygame.Rect(10, 130, area_surface.get_width() + 20, area_surface.get_height() + 10)
        pygame.draw.rect(screen, (255, 255, 255), area_bg_rect)
        pygame.draw.rect(screen, (0, 100, 200), area_bg_rect, 3)
        screen.blit(area_surface, (area_bg_rect.x + 10, area_bg_rect.y + 5))
    
    pygame.display.flip()


def check_intersection():
    """Vérifie les intersections avec conversion pour Numba"""
    global current_step
    
    if not traces:
        return False
    
    # Conversion des traces en array NumPy pour Numba
    all_segments = []
    for trace in traces:
        for i in range(len(trace) - 1):
            all_segments.append([trace[i], trace[i+1]])
    
    if len(all_segments) < 2:
        return False
    
    segments_array = np.array(all_segments, dtype=np.float64)
    
    if check_intersection_numba(segments_array):
        print("Contour fermé trouvé !")
        current_step = "set_scale"
        estimate_area()
        return True
    
    return False


def estimate_area():
    """Estimation de la surface avec affichage progressif"""
    global estimated_area_km2, current_step
    
    if not traces or scale_ratio is None:
        return
    
    # Conversion du polygone en array NumPy
    all_points = [point for trace in traces for point in trace]
    polygon = np.array(all_points, dtype=np.float64)
    
    min_x = int(np.min(polygon[:, 0]))
    max_x = int(np.max(polygon[:, 0]))
    min_y = int(np.min(polygon[:, 1]))
    max_y = int(np.max(polygon[:, 1]))
    
    # Calcul par batch pour affichage progressif
    total_samples = 50000000  # Augmenté pour plus de précision
    batch_size = int(total_samples/100)
    total_inside = 0
    total_processed = 0
    
    for batch_num in range(0, total_samples, batch_size):
        current_batch = min(batch_size, total_samples - batch_num)
        
        estimated_area_px, points_inside = estimate_area_monte_carlo(
            min_x, max_x, min_y, max_y, polygon, current_batch, seed=42 + batch_num
        )
        
        total_inside += points_inside
        total_processed += current_batch
        
        # Calcul de la surface totale
        bounding_box_area = (max_x - min_x) * (max_y - min_y)
        estimated_area_px = (total_inside / total_processed) * bounding_box_area
        estimated_area_km2 = estimated_area_px * (scale_ratio ** 2)
        
        draw()  # Mise à jour visuelle
    
    print(f"Surface finale estimée : {estimated_area_km2:.2f} km² ({total_samples} échantillons)")
    current_step = "done"
    draw()


# Boucle principale
running = True
mouse_pressed = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
            elif event.key == pygame.K_DELETE:
                if traces:
                    traces.pop()
                    estimated_area_km2 = None
                    current_step = "draw_contour"
                    scale_lines.clear()
                    scale_labels.clear()
                    scale_ratio = None
            
            elif event.key == pygame.K_RETURN:
                if measuring and input_active:
                    try:
                        real_distance_km = float(input_text)
                        scale_ratio = real_distance_km / latest_distance
                        scale_labels[-1] = f"{scale_ratio:.3f} km/px"
                        current_step = "calculating"
                        draw()
                        # Lancer le calcul de la surface
                        estimate_area()
                    except ValueError:
                        scale_labels[-1] = "Erreur: Entrée invalide"
                    input_active = False
                    input_text = ""
                elif check_intersection():
                    measuring = True
            
            elif input_active and event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            
            elif input_active:
                input_text += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if measuring:
                    if measure_start is None:
                        measure_start = event.pos
                    else:
                        scale_lines.append((measure_start, event.pos))
                        latest_distance = math.dist(measure_start, event.pos)
                        scale_labels.append(f"{latest_distance:.2f} px")
                        measure_start = None
                        input_active = True
                else:
                    mouse_pressed = True
                    current_trace = [event.pos]
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
                if len(current_trace) > 1:
                    traces.append(current_trace)
                current_trace = []
        
        elif event.type == pygame.MOUSEMOTION and mouse_pressed:
            current_trace.append(event.pos)
    
    draw()

pygame.quit()
