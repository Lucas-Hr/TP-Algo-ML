import pygame
import heapq
import random
import csv
import time
from pygame.locals import *

# -------------------- Classe Noeud pour la résolution automatique -------------------- #
class Noeud:
    def __init__(self, state, size, pred=None, g=0, h=0):
        self.state = state  # État actuel du puzzle
        self.pred = pred  # Noeud prédécesseur
        self.succ = []  # Successeurs
        self.g = g  # Coût accumulé
        self.h = h  # Estimation heuristique
        self.size = size  # Définir la taille

    def getSucc(self):
        succ = []
        zero_index = self.state.index(0)
        row, col = divmod(zero_index, self.size)

        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Déplacements possibles : droite, gauche, bas, haut

        for dr, dc in moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.size and 0 <= new_col < self.size:  # Vérification des limites
                new_index = new_row * self.size + new_col
                new_state = self.state[:]
                new_state[zero_index], new_state[new_index] = new_state[new_index], new_state[zero_index]
                
                # Ajoutez uniquement des états uniques
                if new_state != self.state:
                    succ.append(Noeud(new_state, size=self.size, pred=self))
        return succ

    def isSuccess(self):
        return self.state == list(range(1, self.size * self.size)) + [0]

    def __lt__(self, other):
        return (self.g + self.h) < (other.g + other.h)

    def __str__(self):
        return str(self.state)


def heuristic(node):
    goal = list(range(1, node.size * node.size)) + [0]
    distance = 0
    for i, value in enumerate(node.state):
        if value != 0:
            goal_index = goal.index(value)
            distance += abs(i // node.size - goal_index // node.size) + abs(i % node.size - goal_index % node.size)
    return distance * 2  # Appliquez un facteur pour rendre l'heuristique plus "agressive"


def a_star(depart, max_nodes=100000):
    open_list = []
    closed_list = set()
    heapq.heappush(open_list, depart)
    nodes_explored = 0

    while open_list:
        if nodes_explored > max_nodes:
            print(f"Limite atteinte après {nodes_explored} nœuds explorés.")
            return None
            
        current = heapq.heappop(open_list)
        if current.isSuccess():
            print(f"Solution trouvée après {nodes_explored} nœuds explorés.")
            return current

        closed_list.add(tuple(current.state))
        nodes_explored += 1

        if nodes_explored % 1000 == 0:
            print(f"Nœuds explorés : {nodes_explored}")

        for succ in current.getSucc():
            if tuple(succ.state) not in closed_list:
                succ.g = current.g + 1
                succ.h = heuristic(succ)
                heapq.heappush(open_list, succ)
                
    print(f"Échec : exploration terminée après {nodes_explored} nœuds.")
    return None


# -------------------- Interface graphique en Pygame -------------------- #
class Tile:
    def __init__(self, screen, value, x, y, size):
        self.screen = screen
        self.value = value
        self.x = x
        self.y = y
        self.size = size
        self.font = pygame.font.Font(None, 60)  # Taille de la police ajustée pour 4x4

    def draw(self):
        color = (200, 200, 200) if self.value != 0 else (50, 50, 50)
        pygame.draw.rect(self.screen, color, (self.x, self.y, self.size, self.size))
        if self.value != 0:
            text = self.font.render(str(self.value), True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.x + self.size // 2, self.y + self.size // 2))
            self.screen.blit(text, text_rect)


class Game:
    def __init__(self, size=3, k=0):
        pygame.init()
        self.size = size
        self.k = k
        self.screen_size = (self.size * 120, self.size * 120 + 200)
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption(f"Jeu de Taquin {self.size}x{self.size}")
        self.clock = pygame.time.Clock()
        self.tiles = []
        self.state = list(range(1, self.size * self.size)) + [0]
        self.goal = list(range(1, self.size * self.size)) + [0]
        self.shuffle_state()
        self.selected_tile = None
        self.moves = []  # Liste des mouvements trouvés par A*
        self.current_move = 0  # Index du mouvement actuel
        self.start_time = None  # Temps de départ pour le chronomètre
        self.elapsed_time = 0  # Temps écoulé
        self.total_moves = 0 # Mouvement au total

    def shuffle_state(self):
        # Génère un état solvable en effectuant des déplacements aléatoires depuis l'état résolu
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        state = self.goal[:]
        zero_index = state.index(0)
        for _ in range(self.size * self.size * 10):  # Effectuer un grand nombre de mouvements aléatoires
            row, col = divmod(zero_index, self.size)
            valid_moves = []
            for dr, dc in moves:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < self.size and 0 <= new_col < self.size:
                    valid_moves.append((new_row, new_col))
            if valid_moves:
                new_row, new_col = random.choice(valid_moves)
                new_index = new_row * self.size + new_col
                state[zero_index], state[new_index] = state[new_index], state[zero_index]
                zero_index = new_index
        self.state = state


    def calculate_complexity(self):
        # Utilisation d'un tableau pré-calculé pour la position finale des éléments
        goal_positions = {value: (i // self.size, i % self.size) for i, value in enumerate(self.goal)}
        distance = 0
        for i, value in enumerate(self.state):
            if value != 0:
                current_row, current_col = divmod(i, self.size)
                goal_row, goal_col = goal_positions[value]
                distance += abs(current_row - goal_row) + abs(current_col - goal_col)
        return distance
    

    def is_solvable(self):
        inversions = 0
        for i in range(len(self.state)):
            for j in range(i + 1, len(self.state)):
                if self.state[i] and self.state[j] and self.state[i] > self.state[j]:
                    inversions += 1
        return inversions % 2 == 0

    def swap_tiles(self):
        non_zero_tiles = [i for i in range(len(self.state)) if self.state[i] != 0]
        if len(non_zero_tiles) < 2:
            return
        a, b = random.sample(non_zero_tiles, 2)
        self.state[a], self.state[b] = self.state[b], self.state[a]

    def solve(self):
        print("État initial :", self.state)
        depart = Noeud(self.state, size=self.size)
        solution = a_star(depart)
        if solution:
            moves = []
            current_node = solution
            while current_node.pred is not None:
                moves.append(current_node.state)
                current_node = current_node.pred
            moves.reverse()
            self.moves = moves
            print(f"Solution trouvée en {len(moves)} étapes.")
        else:
            print("Pas de solution trouvée.")

    def draw_tiles(self):
        self.screen.fill((255, 255, 255))
        for i in range(self.size):
            for j in range(self.size):
                assert i < self.size and j < self.size, "Index hors limites"
                tile = self.state[i * self.size + j]
                if tile != 0:
                    pygame.draw.rect(self.screen, (0, 0, 255), (j * 100 + 5, i * 100 + 5, 90, 90))
                    font = pygame.font.Font(None, 50 if self.size == 3 else 40)
                    text = font.render(str(tile), True, (255, 255, 255))
                    self.screen.blit(text, (j * 100 + 35, i * 100 + 35))
    
        # Afficher les statistiques : nombre de mouvements, temps écoulé
        font = pygame.font.Font(None, 30)
        move_text = font.render(f"Moves: {self.current_move}", True, (0, 0, 0))
        
        # Display the time
        time_text = font.render(f"Time: {self.finished_time if hasattr(self, 'finished_time') else self.elapsed_time} sec", True, (0, 0, 0))
        
        # Display solved/not solved status
        solved_text = font.render(
            "Solved!" if self.is_solved() else "Not Solved", 
            True, 
            (0, 128, 0) if self.is_solved() else (255, 0, 0)
        )
    
        self.screen.blit(move_text, (10, self.size * 90 + 10))
        self.screen.blit(time_text, (10, self.size * 90 + 40))
        self.screen.blit(solved_text, (10, self.size * 90 + 70))
    
        pygame.display.flip()

    def is_solved(self):
        return self.state == self.goal

    def make_move(self):
        if self.current_move < len(self.moves):
            self.state = self.moves[self.current_move]
            self.current_move += 1
            self.total_moves += 1

            if self.k > 0 and self.total_moves % self.k == 0:
                self.swap_tiles()

    def run(self):
        self.solve()
        self.start_time = time.time()
        running = True
    
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
    
            if self.current_move < len(self.moves):
                self.make_move()
            else:
                # Fin du jeu, enregistrer les données si non fait
                if not hasattr(self, 'finished_time'):
                    self.finished_time = self.elapsed_time
                    self.final_moves = self.total_moves
                    self.solved_status = "Solved" if self.is_solved() else "Not Solved"
                    self.write_to_csv(self.final_moves, self.finished_time, self.solved_status)
                running = False  # Quitter la boucle une fois terminé
    
            self.elapsed_time = int(time.time() - self.start_time)
            self.draw_tiles()
            pygame.display.flip()
            pygame.time.wait(300)
            self.clock.tick(30)
    
        pygame.time.wait(5000)
        pygame.quit()
        
    def write_to_csv(self, moves, time, status):
        # Toujours ajouter un en-tête si le fichier est vide
        header = ["Puzzle Size", "K Value", "Moves", "Time (seconds)", "Solved Status"]
        file_exists = False
        try:
            with open('game_results.csv', 'r') as file:
                file_exists = file.read(1)  # Vérifie si le fichier a du contenu
        except FileNotFoundError:
            pass  # Le fichier sera créé ci-dessous
    
        # Ajout des résultats
        with open('game_results.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(header)
            writer.writerow([self.size, self.k, moves, time, status])


class Menu:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 300))
        pygame.display.set_caption("Menu de sélection")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 60)
        self.running = True
        self.selected_size = None
        self.selected_k = None  # Valeur de k (0 ou 10)

    def draw(self, k_selection=False):
        self.screen.fill((30, 30, 30))

        if not k_selection:
            text_3x3 = self.font.render("Puzzle 3x3", True, (255, 255, 255))
            text_4x4 = self.font.render("Puzzle 4x4", True, (255, 255, 255))
            self.screen.blit(text_3x3, (100, 100))
            self.screen.blit(text_4x4, (100, 200))
        else:
            text_k0 = self.font.render("K=0", True, (255, 255, 255))
            text_k10 = self.font.render("K=10", True, (255, 255, 255))
            self.screen.blit(text_k0, (100, 100))
            self.screen.blit(text_k10, (100, 200))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if not self.selected_size:
                        if 100 < x < 300 and 100 < y < 150:  # Puzzle 3x3
                            self.selected_size = 3
                            self.draw(k_selection=True)
                        elif 100 < x < 300 and 200 < y < 250:  # Puzzle 4x4
                            self.selected_size = 4
                            self.draw(k_selection=True)  # Afficher la sélection de k
                    elif self.selected_size in [3, 4]:
                        if 100 < x < 300 and 100 < y < 150:  # Choisir K=0
                            self.selected_k = 0
                            Game(size=self.selected_size, k=0).run()
                            return
                        elif 100 < x < 300 and 200 < y < 250:  # Choisir K=10
                            self.selected_k = 10
                            Game(size=self.selected_size, k=10).run()
                            return

            self.draw(k_selection=self.selected_size == 3)
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    Menu().run()