import pygame
import heapq
import random
import csv
import time
from pygame.locals import *

# -------------------- Classe Noeud pour la résolution automatique -------------------- #
class Noeud:
    def __init__(self, state, pred=None, g=0, h=0):
        self.state = state  # État actuel du puzzle
        self.pred = pred  # Noeud prédécesseur
        self.succ = []  # Successeurs
        self.g = g  # Coût accumulé
        self.h = h  # Estimation heuristique
        self.size = pred.size if pred else 3  # Définir la taille par défaut ou à partir du prédécesseur

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
                succ.append(Noeud(new_state, pred=self))
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
    return distance


def a_star(depart):
    open_list = []
    closed_list = set()
    heapq.heappush(open_list, depart)

    while open_list:
        current = heapq.heappop(open_list)
        if current.isSuccess():
            return current

        closed_list.add(tuple(current.state))

        for succ in current.getSucc():
            if tuple(succ.state) not in closed_list:
                succ.g = current.g + 1
                succ.h = heuristic(succ)
                heapq.heappush(open_list, succ)

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
        self.screen_size = (self.size * 90 + 10, self.size * 90 + 160)
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

    def shuffle_state(self):
        random.shuffle(self.state)
        while not self.is_solvable():
            random.shuffle(self.state)

    def is_solvable(self):
        inversions = 0
        for i in range(len(self.state)):
            for j in range(i + 1, len(self.state)):
                if self.state[i] and self.state[j] and self.state[i] > self.state[j]:
                    inversions += 1
        return inversions % 2 == 0

    def solve(self):
        # Résolution du puzzle avec A*
        depart = Noeud(self.state)  # Le paramètre size n'est plus nécessaire ici
        solution = a_star(depart)
        if solution:
            # On sauvegarde la solution comme liste de mouvements
            moves = []
            current_node = solution
            while current_node.pred is not None:
                moves.append(current_node.state)
                current_node = current_node.pred
            moves.reverse()
            self.moves = moves  # Solution trouvée par A*
        else:
            print("Pas de solution trouvée.")

    def draw_tiles(self):
        self.screen.fill((255, 255, 255))
        for i in range(self.size):
            for j in range(self.size):
                tile = self.state[i * self.size + j]
                if tile != 0:
                    pygame.draw.rect(self.screen, (0, 0, 255), (j * 90 + 5, i * 90 + 5, 80, 80))
                    font = pygame.font.Font(None, 50)
                    text = font.render(str(tile), True, (255, 255, 255))
                    self.screen.blit(text, (j * 90 + 30, i * 90 + 30))
    
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

    def run(self):
        self.solve()  # Solve the puzzle with A*
        self.start_time = time.time()  # Start timer when the game starts
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
    
            # Make a move if the puzzle is not solved
            if not self.is_solved():
                self.make_move()
                # Update the elapsed time only if the puzzle is not solved
                self.elapsed_time = int(time.time() - self.start_time)
    
            # Stop updating time once solved
            if self.is_solved() and not hasattr(self, 'finished_time'):
                self.finished_time = self.elapsed_time  # Store final time when puzzle is solved
                self.final_moves = self.current_move  # Store the final number of moves
                self.solved_status = "Solved"  # Mark the puzzle as solved
    
                # Write the result to a CSV file
                self.write_to_csv(self.final_moves, self.finished_time, self.solved_status)
    
            self.draw_tiles()  # Update the display
            pygame.display.flip()
            pygame.time.wait(500)  # Wait a bit before doing the next move
            self.clock.tick(30)
    
        pygame.quit()
        
    def write_to_csv(self, moves, time, status):
        # Check if the file is empty, and if so, write the header
        try:
            with open('game_results.csv', mode='r') as file:
                if file.read(1):
                    pass  # The file is not empty, so don't write a header
        except FileNotFoundError:
            # File does not exist, create it and add the header row
            with open('game_results.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Puzzle Size", "K Value", "Moves", "Time (seconds)", "Solved Status"])
    
        # Now append the result to the CSV file
        with open('game_results.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
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
                            self.selected_k = None
                            self.draw(k_selection=True)
                        elif 100 < x < 300 and 200 < y < 250:  # Puzzle 4x4
                            self.selected_size = 4
                            self.selected_k = None
                            self.draw(k_selection=True)
                    elif self.selected_size:
                        if 100 < x < 300 and 100 < y < 150:  # Choisir K=0
                            self.selected_k = 0
                            Game(size=self.selected_size, k=self.selected_k).run()
                            self.running = False
                        elif 100 < x < 300 and 200 < y < 250:  # Choisir K=10
                            self.selected_k = 10
                            Game(size=self.selected_size, k=self.selected_k).run()
                            self.running = False

            self.draw(k_selection=self.selected_size is not None)
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    Menu().run()
