import pygame
from itertools import combinations
import math
import random

# Initialisation de Pygame
pygame.init()

# Chargement de l'image de la carte
image_path = "/home/hugo-alexandre/pCloudDrive/Python/code_python_1m2p/MC_map/flat_earth.png"  # Remplace par le chemin de ton image
image = pygame.image.load(image_path)

# Création de la fenêtre
screen = pygame.display.set_mode(image.get_size())
pygame.display.set_caption("Carte interactive")

# Police pour l'affichage des valeurs de l'échelle
font = pygame.font.Font(None, 36)  # Texte plus grand

# Liste pour stocker les tracés
traces = []
current_trace = []
scale_lines = []  # Liste pour stocker les traits de mesure
scale_labels = []  # Liste pour stocker les valeurs de l'échelle
measuring = False
measure_start = None
input_active = False
input_text = ""
latest_distance = None
scale_ratio = None  # Ratio km/px
estimated_area_km2 = None  # Stocker la surface estimée

# Fonction d'affichage
def draw():
    screen.blit(image, (0, 0))
    for trace in traces:
        if len(trace) > 1:
            pygame.draw.lines(screen, (255, 0, 0), False, trace, 2)
    if len(current_trace) > 1:
        pygame.draw.lines(screen, (255, 0, 0), False, current_trace, 2)
    for i, line in enumerate(scale_lines):
        pygame.draw.line(screen, (0, 255, 0), line[0], line[1], 2)
        text_surface = font.render(scale_labels[i], True, (0, 0, 0))  # Texte en noir
        mid_x = (line[0][0] + line[1][0]) // 2
        mid_y = (line[0][1] + line[1][1]) // 2 - 40  # Décale le texte au-dessus du trait
        screen.blit(text_surface, (mid_x - text_surface.get_width() // 2, mid_y))
    if input_active:
        input_surface = font.render(f"Distance réelle (km) : {input_text}", True, (0, 0, 0))
        input_bg_rect = pygame.Rect(10, 10, input_surface.get_width() + 10, input_surface.get_height() + 5)
        pygame.draw.rect(screen, (255, 255, 255), input_bg_rect)  # Fond blanc
        screen.blit(input_surface, (input_bg_rect.x + 5, input_bg_rect.y))
    
    if estimated_area_km2 is not None:
        area_surface = font.render(f"Surface estimée : {estimated_area_km2:.2f} km²", True, (0, 0, 0))
        area_bg_rect = pygame.Rect(10, 40, area_surface.get_width() + 10, area_surface.get_height() + 5)
        pygame.draw.rect(screen, (255, 255, 255), area_bg_rect)  # Fond blanc
        screen.blit(area_surface, (area_bg_rect.x + 5, area_bg_rect.y))

    pygame.display.flip()

# Autres fonctions inchangées...

def segments_intersect(p1, p2, q1, q2):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

def check_intersection():
    all_segments = [(trace[i], trace[i+1]) for trace in traces for i in range(len(trace)-1)]
    for (p1, p2), (q1, q2) in combinations(all_segments, 2):
        if segments_intersect(p1, p2, q1, q2):
            print("Contour fermé trouvé !")
            estimate_area()
            return True
        #print("Le contour n'est pas fermé.")
    return False

def estimate_area():
    global estimated_area_km2
    if not traces or scale_ratio is None:
        return
    
    min_x = min(point[0] for trace in traces for point in trace)
    max_x = max(point[0] for trace in traces for point in trace)
    min_y = min(point[1] for trace in traces for point in trace)
    max_y = max(point[1] for trace in traces for point in trace)
    
    bounding_box_area_px = (max_x - min_x) * (max_y - min_y)
    
    num_samples = 100000
    points_inside = 0
    
    for i in range(num_samples):
        x_rand = random.randint(min_x, max_x)
        y_rand = random.randint(min_y, max_y)
        
        inside = False
        for trace in traces:
            for j in range(len(trace) - 1):
                p1, p2 = trace[j], trace[j+1]
                if (p1[1] > y_rand) != (p2[1] > y_rand) and \
                   (x_rand < (p2[0] - p1[0]) * (y_rand - p1[1]) / (p2[1] - p1[1]) + p1[0]):
                    inside = not inside
        if inside:
            points_inside += 1
        
        # Mise à jour de l'affichage tous les 500 points
        if (i + 1) % 500 == 0 or i == num_samples - 1:
            estimated_area_px = (points_inside / (i + 1)) * bounding_box_area_px
            estimated_area_km2 = (estimated_area_px * (scale_ratio ** 2))
            draw()  # Met à jour l'affichage

    print(f"Surface finale estimée : {estimated_area_km2:.2f} km²")

    

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
            elif event.key == pygame.K_RETURN:
                if measuring and input_active:
                    try:
                        real_distance_km = float(input_text)
                        scale_ratio = real_distance_km / latest_distance
                        scale_labels[-1] = f"{scale_ratio:.3f} km/px"
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
