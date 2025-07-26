import tkinter as tk
from tkinter import ttk
import random
import json
import os
import threading
import time

class TetrisGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tetris - Juego Avanzado")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        # Variables del juego
        self.GRID_WIDTH = 10
        self.GRID_HEIGHT = 20
        self.BLOCK_SIZE = 30
        
        # Colores de las piezas
        self.COLORS = {
            'I': '#00ffff',    # Cyan
            'T': '#ff00ff',    # Magenta
            'L': '#ffa500',    # Orange
            'J': '#0000ff',    # Blue
            'O': '#ffff00',    # Yellow
            'S': '#00ff00',    # Green
            'Z': '#ff0000',    # Red
            'empty': '#34495e' # Dark blue-gray
        }
        
        # Formas de las piezas (DEFINICIÓN CORRECTA Y VERIFICADA)
        self.SHAPES = {
            'I': [
                [1, 1, 1, 1]
            ],
            'T': [
                [1, 1, 1],
                [0, 1, 0]
            ],
            'L': [
                [1, 1, 1],
                [1, 0, 0]
            ],
            'J': [
                [1, 1, 1],
                [0, 0, 1]
            ],
            'O': [
                [1, 1],
                [1, 1]
            ],
            'S': [
                [0, 1, 1],
                [1, 1, 0]
            ],
            'Z': [
                [1, 1, 0],
                [0, 1, 1]
            ]
        }
        
        self.PIECE_NAMES = ['I', 'T', 'L', 'J', 'O', 'S', 'Z']
        
        # Puntos por líneas
        self.LINE_POINTS = {1: 100, 2: 300, 3: 500, 4: 800}
        
        self.reset_game()
        self.load_high_scores()
        self.setup_ui()
        
    def reset_game(self):
        self.grid = [['empty' for _ in range(self.GRID_WIDTH)] for _ in range(self.GRID_HEIGHT)]
        self.current_piece = self.create_random_piece()
        self.next_piece = self.create_random_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.fall_speed = 1000  # ms
        self.fall_time = 0
        self.game_running = False
        
    def create_random_piece(self):
        piece_type = random.choice(self.PIECE_NAMES)
        return {
            'type': piece_type,
            'shape': self.SHAPES[piece_type],
            'color': self.COLORS[piece_type],
            'x': self.GRID_WIDTH // 2 - len(self.SHAPES[piece_type][0]) // 2,
            'y': 0
        }
        
    def rotate_piece(self, piece):
        shape = piece['shape']
        rotated = [[shape[y][x] for y in range(len(shape)-1, -1, -1)] for x in range(len(shape[0]))]
        return rotated
        
    def check_collision(self, piece, dx=0, dy=0, new_shape=None):
        shape = new_shape if new_shape else piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    pos_x = piece['x'] + x + dx
                    pos_y = piece['y'] + y + dy
                    if (pos_x < 0 or pos_x >= self.GRID_WIDTH or 
                        pos_y >= self.GRID_HEIGHT or 
                        (pos_y >= 0 and self.grid[pos_y][pos_x] != 'empty')):
                        return True
        return False
        
    def lock_piece(self):
        shape = self.current_piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    pos_y = self.current_piece['y'] + y
                    pos_x = self.current_piece['x'] + x
                    if 0 <= pos_y < self.GRID_HEIGHT and 0 <= pos_x < self.GRID_WIDTH:
                        self.grid[pos_y][pos_x] = self.current_piece['type']
                        
        lines = self.clear_lines()
        if lines > 0:
            self.score += self.LINE_POINTS.get(lines, 0) * self.level
            self.lines_cleared += lines
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(100, 1000 - (self.level - 1) * 50)
            
        self.current_piece = self.next_piece
        self.next_piece = self.create_random_piece()
        
        if self.check_collision(self.current_piece):
            self.game_over = True
            self.save_high_score()
            self.game_running = False
            
    def clear_lines(self):
        lines_to_clear = []
        for i, row in enumerate(self.grid):
            if all(cell != 'empty' for cell in row):
                lines_to_clear.append(i)
                
        for line in lines_to_clear:
            del self.grid[line]
            self.grid.insert(0, ['empty' for _ in range(self.GRID_WIDTH)])
            
        return len(lines_to_clear)
        
    def move_piece(self, dx, dy):
        if not self.game_over and not self.paused and self.game_running:
            if not self.check_collision(self.current_piece, dx, dy):
                self.current_piece['x'] += dx
                self.current_piece['y'] += dy
                if dy > 0 and self.check_collision(self.current_piece, 0, 1):
                    self.lock_piece()
                self.draw_game()
            elif dy > 0:  # Si no puede moverse abajo, bloquear pieza
                self.lock_piece()
                self.draw_game()
                
    def rotate_current_piece(self):
        if not self.game_over and not self.paused and self.game_running:
            old_shape = self.current_piece['shape']
            new_shape = self.rotate_piece(self.current_piece)
            if not self.check_collision(self.current_piece, 0, 0, new_shape):
                self.current_piece['shape'] = new_shape
                self.draw_game()
                
    def load_high_scores(self):
        try:
            if os.path.exists('tetris_scores.json'):
                with open('tetris_scores.json', 'r') as f:
                    self.high_scores = json.load(f)
            else:
                self.high_scores = []
        except:
            self.high_scores = []
            
    def save_high_score(self):
        self.high_scores.append({
            'score': self.score,
            'level': self.level,
            'lines': self.lines_cleared
        })
        self.high_scores.sort(key=lambda x: x['score'], reverse=True)
        self.high_scores = self.high_scores[:10]
        
        try:
            with open('tetris_scores.json', 'w') as f:
                json.dump(self.high_scores, f)
        except:
            pass
            
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="TETRIS", font=('Arial', 36, 'bold'), 
                              bg='#2c3e50', fg='#ecf0f1')
        title_label.pack(pady=(0, 20))
        
        # Frame del juego
        game_frame = tk.Frame(main_frame, bg='#34495e')
        game_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo - Tablero
        left_frame = tk.Frame(game_frame, bg='#34495e')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Canvas para el tablero
        self.canvas = tk.Canvas(left_frame, width=self.GRID_WIDTH * self.BLOCK_SIZE, 
                               height=self.GRID_HEIGHT * self.BLOCK_SIZE, 
                               bg='#2c3e50', highlightthickness=2, highlightbackground='#ecf0f1')
        self.canvas.pack(pady=20)
        
        # Panel derecho - Información
        right_frame = tk.Frame(game_frame, bg='#34495e')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Panel de información
        info_frame = tk.LabelFrame(right_frame, text="Información", font=('Arial', 14, 'bold'),
                                  bg='#34495e', fg='#ecf0f1', padx=20, pady=20)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Score
        self.score_label = tk.Label(info_frame, text="Score: 0", font=('Arial', 16),
                                   bg='#34495e', fg='#ecf0f1')
        self.score_label.pack(pady=5)
        
        # Level
        self.level_label = tk.Label(info_frame, text="Level: 1", font=('Arial', 16),
                                   bg='#34495e', fg='#ecf0f1')
        self.level_label.pack(pady=5)
        
        # Lines
        self.lines_label = tk.Label(info_frame, text="Lines: 0", font=('Arial', 16),
                                   bg='#34495e', fg='#ecf0f1')
        self.lines_label.pack(pady=5)
        
        # Siguiente pieza
        next_frame = tk.LabelFrame(right_frame, text="Siguiente Pieza", font=('Arial', 14, 'bold'),
                                  bg='#34495e', fg='#ecf0f1', padx=20, pady=20)
        next_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Canvas para siguiente pieza
        self.next_canvas = tk.Canvas(next_frame, width=120, height=120, 
                                    bg='#2c3e50', highlightthickness=1, highlightbackground='#ecf0f1')
        self.next_canvas.pack()
        
        # Controles
        controls_frame = tk.LabelFrame(right_frame, text="Controles", font=('Arial', 14, 'bold'),
                                      bg='#34495e', fg='#ecf0f1', padx=20, pady=20)
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        controls_text = """
        ← → : Mover
        ↑ : Rotar
        ↓ : Bajar rápido
        P : Pausa
        R : Reiniciar
        ESPACIO : Iniciar
        """
        
        controls_label = tk.Label(controls_frame, text=controls_text, font=('Arial', 12),
                                 bg='#34495e', fg='#bdc3c7', justify=tk.LEFT)
        controls_label.pack()
        
        # Botones de control
        buttons_frame = tk.Frame(right_frame, bg='#34495e')
        buttons_frame.pack(fill=tk.X)
        
        self.start_button = tk.Button(buttons_frame, text="Iniciar", font=('Arial', 12, 'bold'),
                                     bg='#27ae60', fg='white', command=self.start_game)
        self.start_button.pack(fill=tk.X, pady=5)
        
        self.pause_button = tk.Button(buttons_frame, text="Pausa", font=('Arial', 12, 'bold'),
                                     bg='#f39c12', fg='white', command=self.toggle_pause)
        self.pause_button.pack(fill=tk.X, pady=5)
        
        self.reset_button = tk.Button(buttons_frame, text="Reiniciar", font=('Arial', 12, 'bold'),
                                     bg='#e74c3c', fg='white', command=self.reset_game_ui)
        self.reset_button.pack(fill=tk.X, pady=5)
        
        self.high_scores_button = tk.Button(buttons_frame, text="Puntuaciones Altas", 
                                           font=('Arial', 12, 'bold'), bg='#3498db', fg='white',
                                           command=self.show_high_scores)
        self.high_scores_button.pack(fill=tk.X, pady=5)
        
        # Estado del juego
        self.status_label = tk.Label(main_frame, text="Presiona 'Iniciar' para comenzar", 
                                    font=('Arial', 14), bg='#2c3e50', fg='#ecf0f1')
        self.status_label.pack(pady=10)
        
        # Bind teclas
        self.root.bind('<Key>', self.handle_keypress)
        self.root.focus_set()
        
        # Inicializar dibujo
        self.draw_game()
        
    def draw_game(self):
        # Limpiar canvas
        self.canvas.delete('all')
        self.next_canvas.delete('all')
        
        # Dibujar grid
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                color = self.COLORS[self.grid[y][x]]
                self.canvas.create_rectangle(
                    x * self.BLOCK_SIZE, y * self.BLOCK_SIZE,
                    (x + 1) * self.BLOCK_SIZE, (y + 1) * self.BLOCK_SIZE,
                    fill=color, outline='#2c3e50', width=1
                )
        
        # Dibujar pieza actual
        if not self.game_over and self.game_running:
            shape = self.current_piece['shape']
            color = self.current_piece['color']
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:
                        self.canvas.create_rectangle(
                            (self.current_piece['x'] + x) * self.BLOCK_SIZE,
                            (self.current_piece['y'] + y) * self.BLOCK_SIZE,
                            (self.current_piece['x'] + x + 1) * self.BLOCK_SIZE,
                            (self.current_piece['y'] + y + 1) * self.BLOCK_SIZE,
                            fill=color, outline='#ffffff', width=2
                        )
        
        # Dibujar siguiente pieza
        shape = self.next_piece['shape']
        color = self.next_piece['color']
        offset_x = (120 - len(shape[0]) * 25) // 2
        offset_y = (120 - len(shape) * 25) // 2
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    self.next_canvas.create_rectangle(
                        offset_x + x * 25, offset_y + y * 25,
                        offset_x + (x + 1) * 25, offset_y + (y + 1) * 25,
                        fill=color, outline='#ffffff', width=1
                    )
        
        # Actualizar información
        self.score_label.config(text=f"Score: {self.score}")
        self.level_label.config(text=f"Level: {self.level}")
        self.lines_label.config(text=f"Lines: {self.lines_cleared}")
        
        # Actualizar estado
        if self.game_over:
            self.status_label.config(text="¡JUEGO TERMINADO! Presiona 'Reiniciar'")
        elif self.paused:
            self.status_label.config(text="JUEGO PAUSADO")
        elif self.game_running:
            self.status_label.config(text="Jugando...")
        else:
            self.status_label.config(text="Presiona 'Iniciar' para comenzar")
            
    def start_game(self):
        if not self.game_running:
            self.game_running = True
            self.game_over = False
            self.paused = False
            self.game_loop()
            
    def toggle_pause(self):
        if self.game_running and not self.game_over:
            self.paused = not self.paused
            self.draw_game()
            
    def reset_game_ui(self):
        self.reset_game()
        self.draw_game()
        
    def show_high_scores(self):
        scores_window = tk.Toplevel(self.root)
        scores_window.title("Puntuaciones Altas")
        scores_window.geometry("500x400")
        scores_window.configure(bg='#2c3e50')
        
        title_label = tk.Label(scores_window, text="PUNTUACIONES ALTAS", 
                              font=('Arial', 20, 'bold'), bg='#2c3e50', fg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Crear tabla
        tree_frame = tk.Frame(scores_window, bg='#2c3e50')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('Posición', 'Puntuación', 'Nivel', 'Líneas')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        # Definir encabezados
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
            
        # Agregar datos
        for i, score in enumerate(self.high_scores[:10]):
            tree.insert('', 'end', values=(i+1, score['score'], score['level'], score['lines']))
            
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón cerrar
        close_button = tk.Button(scores_window, text="Cerrar", font=('Arial', 12, 'bold'),
                                bg='#e74c3c', fg='white', command=scores_window.destroy)
        close_button.pack(pady=20)
        
    def handle_keypress(self, event):
        key = event.keysym.lower()
        
        if key == 'left':
            self.move_piece(-1, 0)
        elif key == 'right':
            self.move_piece(1, 0)
        elif key == 'down':
            self.move_piece(0, 1)
        elif key == 'up':
            self.rotate_current_piece()
        elif key == 'p':
            self.toggle_pause()
        elif key == 'r':
            self.reset_game_ui()
        elif key == 'space' and not self.game_running:
            self.start_game()
            
    def game_loop(self):
        def loop():
            while self.game_running and not self.game_over and not self.paused:
                time.sleep(self.fall_speed / 1000.0)
                if self.game_running and not self.paused:
                    self.root.after(0, lambda: self.move_piece(0, 1))
            if self.game_over:
                self.root.after(0, self.draw_game)
                
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        
    def run(self):
        self.root.mainloop()

# Ejecutar el juego
if __name__ == "__main__":
    game = TetrisGame()
    game.run()