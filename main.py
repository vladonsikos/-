import os
import random
import string
import requests
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Конфигурация Telegram бота (замените на ваш токен)
TELEGRAM_BOT_TOKEN = '8575700235:AAHck7YcLrSAkg0tC6UNMMbdYoQss04dr64'
TELEGRAM_CHAT_ID = '6854608564'

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

def generate_promo_code():
    """Генерация 5-значного промокода"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(5))

class TicTacToeGame:
    def __init__(self):
        self.board = [' ' for _ in range(9)]
        self.current_player = 'X'  # Игрок всегда X
        self.game_over = False
        self.winner = None
        self.promo_code = None
    
    def make_move(self, position):
        """Ход игрока"""
        if self.board[position] == ' ' and not self.game_over:
            self.board[position] = self.current_player
            
            if self.check_winner():
                self.game_over = True
                self.winner = 'player'
                self.promo_code = generate_promo_code()
                # Отправка в Telegram
                send_telegram_message(
                    f"🎉 Победа! Промокод выдан: <b>{self.promo_code}</b>\n"
                    f"🎮 Игрок победил компьютер в Крестиках-ноликах!"
                )
                return True
            elif self.is_board_full():
                self.game_over = True
                self.winner = 'draw'
                send_telegram_message("🤝 Ничья! Игра завершилась вничью.")
                return True
            
            # Ход компьютера
            self.computer_move()
            return True
        return False
    
    def computer_move(self):
        """Ход компьютера (упрощенный ИИ)"""
        # Сначала проверяем возможность победить
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'O'
                if self.check_winner('O'):
                    self.game_over = True
                    self.winner = 'computer'
                    send_telegram_message("💻 Проигрыш! Компьютер победил.")
                    return
                self.board[i] = ' '
        
        # Блокируем игрока, если он может победить
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'X'
                if self.check_winner('X'):
                    self.board[i] = 'O'
                    return
                self.board[i] = ' '
        
        # Занимаем центр, если свободен
        if self.board[4] == ' ':
            self.board[4] = 'O'
            return
        
        # Занимаем углы
        corners = [0, 2, 6, 8]
        random.shuffle(corners)
        for corner in corners:
            if self.board[corner] == ' ':
                self.board[corner] = 'O'
                return
        
        # Любая свободная клетка
        available_moves = [i for i in range(9) if self.board[i] == ' ']
        if available_moves:
            position = random.choice(available_moves)
            self.board[position] = 'O'
            
            if self.check_winner('O'):
                self.game_over = True
                self.winner = 'computer'
                send_telegram_message("💻 Проигрыш! Компьютер победил.")
            elif self.is_board_full():
                self.game_over = True
                self.winner = 'draw'
                send_telegram_message("🤝 Ничья! Игра завершилась вничью.")
    
    def check_winner(self, player=None):
        """Проверка победителя"""
        if player is None:
            player = self.current_player
        
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Горизонтали
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Вертикали
            [0, 4, 8], [2, 4, 6]              # Диагонали
        ]
        
        for combo in winning_combinations:
            if all(self.board[i] == player for i in combo):
                return True
        return False
    
    def is_board_full(self):
        """Проверка заполненности поля"""
        return ' ' not in self.board
    
    def reset(self):
        """Сброс игры"""
        self.__init__()

@app.route('/')
def index():
    """Главная страница с игрой"""
    if 'game' not in session:
        session['game'] = {
            'board': [' ' for _ in range(9)],
            'current_player': 'X',
            'game_over': False,
            'winner': None,
            'promo_code': None
        }
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def make_move():
    """Обработка хода игрока"""
    if 'game' not in session:
        session['game'] = {
            'board': [' ' for _ in range(9)],
            'current_player': 'X',
            'game_over': False,
            'winner': None,
            'promo_code': None
        }
    
    game_data = session['game']
    game = TicTacToeGame()
    game.board = game_data['board']
    game.current_player = game_data['current_player']
    game.game_over = game_data['game_over']
    game.winner = game_data['winner']
    game.promo_code = game_data['promo_code']
    
    position = int(request.json.get('position'))
    
    if not game.game_over and game.make_move(position):
        # Обновляем сессию
        session['game'] = {
            'board': game.board,
            'current_player': game.current_player,
            'game_over': game.game_over,
            'winner': game.winner,
            'promo_code': game.promo_code
        }
        
        response = {
            'board': game.board,
            'game_over': game.game_over,
            'winner': game.winner,
            'promo_code': game.promo_code
        }
        
        return jsonify(response)
    
    return jsonify({'error': 'Invalid move'})

@app.route('/reset', methods=['POST'])
def reset_game():
    """Сброс игры"""
    session.pop('game', None)
    return jsonify({'success': True})

@app.route('/test_telegram', methods=['POST'])
def test_telegram():
    """Тестовая отправка в Telegram"""
    message = request.json.get('message', 'Тестовое сообщение')
    success = send_telegram_message(message)
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)