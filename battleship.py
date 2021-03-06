"""
Игра «Морской бой» для произвольного размера поля и наборов кораблей.
Итоговое практическое задание B7.5 для SkillFactory.
Поддерживается режим игры только с компьютерным оппонентом.
Формат ввода координат: «строка колонка». Можно использовать любой
небуквенный разделитель, или вводить координаты слитно.

Используются модули только из стандартной библиотеки Python 3.8.5.
"""
# !!! КОММЕНТАРИЙ ДЛЯ МЕНТОРА !!!
#
# 1. Решил немного изменить внешний вид поля по сравнению с образцом.
#    На мой взгляд, символы O-X-T слишком сливаются друг с другом
#    из-за одинаковых размеров, и иногда сложно понять, что происходит
#    на поле. Все символы настраиваются в константном блоке.
# 2. Дополнил правила игры в соответствии с настольной версией игры,
#    по крайней мере, с той, с которой я знаком. При потоплений вражеского
#    корабля сообщается, что он именно убит, а не просто ранен, и,
#    как следствие, все клетки вокруг него помечаются как гарантированно
#    пустые. После этого компьютер со своим примитивным алгоритмом стал
#    чуть лучше играть.
# 3. В теории поддерживаются поля и списки кораблей большего размера
#    (изменить можно также в константном блоке). С учётом полей размером
#    больше девяти клеток решено было использовать буквы вместо цифр
#    для обозначения рядов и колонок.
# 4. Вместо функции print_intro изначально использовался метод draw
#    класса Board, но для более симпатичного (параллельного) вывода
#    игровых полей решил использовать эту функцию. Конечно, в метод draw
#    одной доски можно было бы передавать аргументом вторую, но не думаю,
#    что это очень изящный способ.
#    Изначальный код метода оставлен в программе и закомментирован.


import os
import random
import time
from string import ascii_uppercase as letters


BOARD_SIZE = 6
SHIP_RULES = [3, 2, 2, 1, 1, 1, 1]
EMPTY_SYMBOL = '~'
SHIP_SYMBOL = '■'
HIT_SYMBOL = 'X'
MISS_SYMBOL = '·'
SCR_WIDTH = BOARD_SIZE * 8
CLEAR_SCREEN = 'cls' if os.name == 'nt' else 'clear'
TIMEOUT = 1


def print_intro(board1, board2, with_ships=False):
    """
    Функция очистки экрана и вывода игровых полей.
    Аргументы:
    with_ships — отображать или нет при выводе поля противника расставленные
    корабли. По умолчанию False.
    """
    os.system(CLEAR_SCREEN)

    print('-' * SCR_WIDTH)
    print('Морской бой'.center(SCR_WIDTH))
    print()
    print('формат ввода ходов: «строка колонка»'.center(SCR_WIDTH))
    print('-' * SCR_WIDTH)
    print()
    print('Игрок'.center(SCR_WIDTH // 2) + 'Компьютер'.center(SCR_WIDTH // 2))
    print(f'Кораблей: {len(board1.ships)}'.center(SCR_WIDTH // 2)
        + f'Кораблей: {len(board2.ships)}'.center(SCR_WIDTH // 2))
    print()

    col_numbers1 = ' ' + '|'.join(letters[:board1.size])
    col_numbers2 = ' ' + '|'.join(letters[:board2.size])
    print(col_numbers1.center(SCR_WIDTH // 2)
        + col_numbers2.center(SCR_WIDTH // 2))

    for row_number, rows in enumerate(zip(board1.state, board2.state)):
        hidden_row = [EMPTY_SYMBOL if cell == SHIP_SYMBOL
                      else cell for cell in rows[1]]
        row1 = letters[row_number] + '|' + '|'.join(map(str, rows[0]))
        row2 = (letters[row_number] + '|' + '|'.join(map(str, rows[1]))
                if with_ships else
                letters[row_number] + '|' + '|'.join(map(str, hidden_row)))
        print(row1.center(SCR_WIDTH // 2) + row2.center(SCR_WIDTH // 2))

    print()
    print('-' * SCR_WIDTH)
    print()


class Board:
    """
    Класс игрового поля.
    Атрибуты:
    size — размер игрового поля.
    state — текущее состояние игрового поля.
    ships — список кораблей (объектов класса Ship), находящихся на поле.
    """
    board_size = BOARD_SIZE
    ship_rules = SHIP_RULES

    def __init__(self):
        self.reset()

    def reset(self):
        """ Метод приведения игрового поля в изначальное состояние. """
        self.size = self.board_size
        self.state = [[EMPTY_SYMBOL for col in range(self.size)]
                      for row in range(self.size)]
        self.ships = []

    # def draw(self, with_ships = True):
    #     """
    #     Метод отображения игрового поля.
    #     Аргументы:
    #     with_ships — отображать или, в случае компьютерного игрока,
    #     скрывать корабли на поле. Значение по умолчанию: True.
    #     """
    #     print(' ', *range(1, self.size + 1), sep='|')
    #     for row_number, row in enumerate(self.state, 1):
    #         print(row_number, end='|')
    #         hidden_row = [EMPTY_SYMBOL if cell == SHIP_SYMBOL
    #                       else cell for cell in row]
    #         print(*row if with_ships else hidden_row, sep='|')
    #     print()

    def setup(self, auto=True):
        """
        Метод расстановки кораблей на поле.
        Аргументы:
        auto — расставлять ли корабли автоматически случайным образом.
        По умолчанию True.
        """
        # Заглушка в виде пустой доски для функции отображения.
        dummy = Board()
        while len(self.ships) < len(self.ship_rules):
            ship_size = self.ship_rules[len(self.ships)]

            # Автоматическая расстановка.
            if auto:
                # На случай возникновения тупиковой ситуации, при которой
                # следующий корабль невозможно разместить, используется
                # ограниченное количество попыток (20). По их истечении поле
                # сбрасывается, и расстановка начинается сначала.
                try_count = 0
                while try_count <= 20:
                    try_count += 1
                    orientation = random.choice(('h', 'v'))
                    start_position = (random.randrange(self.size),
                                      random.randrange(self.size))
                    ship = Ship(ship_size, orientation, start_position)
                    if self.is_ship_fit(ship):
                        self.add_ship(ship)
                        break
                if try_count > 20:
                    self.reset()

            # Ручная расстановка.
            else:
                print_intro(self, dummy)
                print(f'Расстановка — Корабль №{len(self.ships) + 1}, '
                      f'{ship_size}-палубный')
                try:
                    if ship_size > 1:
                        orientation = input('Введите ориентацию корабля — '
                            'горизонтальная (h) или вертикальная (v): ')
                        start_position = (letters.index(l) for l in
                        input('Введите координаты верхней левой '
                        'точки: ').upper() if l in letters)
                    # Если корабль одноклеточный, то ориентация неважна.
                    else:
                        orientation = 'h'
                        start_position = (letters.index(l) for l in
                            input('Введите координаты корабля: ').upper()
                            if l in letters)
                    ship = Ship(ship_size, orientation, start_position)
                    if self.is_ship_fit(ship):
                        self.add_ship(ship)
                    else:
                        raise ValueError
                except ValueError:
                    print('Корабль нельзя разместить в указанных координатах.')
                    print('(r)eset — начать расстановку сначала.\n'
                          '(a)uto — закончить расстановку автоматически.\n'
                          '<Enter> для продолжения:', end=' ')
                    reset = input()
                    if reset.lower() in ('r', 'reset'):
                        self.reset()
                    elif reset.lower() in ('a', 'auto'):
                        auto = True

    def add_ship(self, ship):
        """
        Метод добавления корабля на игровое поле.
        Аргументы:
        ship — объект класса Ship
        """
        for x, y in ship.coordinates:
            self.state[x][y] = SHIP_SYMBOL
        self.ships.append(ship)

    def is_ship_fit(self, ship):
        """
        Метод проверки возможности размещения корабля в заданных координатах.
        Аргументы:
        ship — объект класса Ship
        """
        # Проверяем, помещается ли корабль целиком на поле.
        if (ship.x + ship.height - 1 >= self.size or
            ship.y + ship.width - 1 >= self.size or
            ship.x < 0 or ship.y < 0):
            return False

        # Если да, то проверяем, нет ли в радиусе одной клетки от него
        # другого корабля.
        for x in range(ship.x - 1, ship.x + ship.height + 1):
            for y in range(ship.y - 1, ship.y + ship.width + 1):
                try:
                    if x < 0 or y < 0:
                        raise IndexError
                    if self.state[x][y] != EMPTY_SYMBOL:
                        return False
                except IndexError:
                    continue

        # Если обе проверки пройдены, значит, корабль можно разместить.
        return True

    def take_shot(self, is_ai):
        """
        Метод проведения выстрела по указанным координатам.
        Возвращает True при попадании и False при промахе.
        Аргументы:
        is_ai — кто делает выстрел: компьютер или человек.
        """
        while True:
            if is_ai:
                x, y = (random.randrange(self.size),
                        random.randrange(self.size))
                if self.state[x][y] in (MISS_SYMBOL, HIT_SYMBOL):
                    continue
                time.sleep(TIMEOUT)
                print(letters[x], letters[y])
                break
            try:
                x, y = (letters.index(l)
                        for l in input().upper() if l in letters)
                if x < 0 or x >= self.size or y < 0 or y >= self.size:
                    raise IndexError('Таких координат не существует.')
                if self.state[x][y] in (MISS_SYMBOL, HIT_SYMBOL):
                    raise IndexError('Вы уже стреляли в эту точку.')
            except ValueError:
                print('Неверный формат ввода. Попробуйте ещё раз:', end=' ')
            except IndexError as error_message:
                print(f'{error_message} Попробуйте ещё раз:', end=' ')
            else:
                break

        if self.state[x][y] == SHIP_SYMBOL:
            self.state[x][y] = HIT_SYMBOL
            time.sleep(TIMEOUT)
            print('Попадание!', end=' ', flush=True)
            if self.is_ship_dead(x, y):
                print('Корабль потоплен!')
                self.mark_ship_dead(x, y)
            else:
                print('Корабль ранен!')
            time.sleep(TIMEOUT)
            return True

        self.state[x][y] = MISS_SYMBOL
        time.sleep(TIMEOUT)
        print('Промах!')
        time.sleep(TIMEOUT)
        return False

    def is_ship_dead(self, shot_x, shot_y):
        """
        Метод проверки, уничтожен ли корабль. Если уничтожен, возвращает True,
        если нет — False.
        Аргументы:
        shot_x, shot_y — координаты точки, вокруг которой происходит проверка.
        """
        dead_ship = [ship for ship in self.ships
                     if (shot_x, shot_y) in ship.coordinates][0]
        for x, y in dead_ship.coordinates:
            if self.state[x][y] == SHIP_SYMBOL:
                return False
        return True

    def mark_ship_dead(self, shot_x, shot_y):
        """
        Метод, помечающий символом выстрела все ячейки вокруг убитого корабля,
        и удаляющий убитый корабль из списка кораблей.
        Аргументы:
        shot_x, shot_y — координаты точки выстрела, по которой определяется,
        в какой именно корабль совершён выстрел.
        """
        dead_ship = [ship for ship in self.ships
                     if (shot_x, shot_y) in ship.coordinates][0]
        for x in range(dead_ship.x - 1, dead_ship.x + dead_ship.height + 1):
            for y in range(dead_ship.y - 1, dead_ship.y + dead_ship.width + 1):
                try:
                    if x < 0 or y < 0:
                        raise IndexError
                    if self.state[x][y] == EMPTY_SYMBOL:
                        self.state[x][y] = MISS_SYMBOL
                except IndexError:
                    continue
        dead_ship_index = self.ships.index(dead_ship)
        self.ships.pop(dead_ship_index)

    def is_lose(self):
        """ Метод проверки игрового поля на предмет окончания игры. """
        return not self.ships


class Ship:
    """
    Класс корабля.
    Атрибуты:
    size — размер корабля.
    orientation — горизонтально или вертикально установлен корабль.
    width — условная ширина корабля.
    height — условная длина корабля.
    x, y — координаты левой верхней точки корабля.
    coordinates — список всех пар координат корабля.
    """
    def __init__(self, size, orientation, start_position):
        self.size = size
        self.orientation = orientation
        self.width = size if orientation in ('h', 'H') else 1
        self.height = 1 if orientation in ('h', 'H') else size
        self.x, self.y = start_position
        self.coordinates = []
        for cell in range(self.size):
            self.coordinates.append((self.x, self.y + cell)
                if self.orientation in ('h', 'H') else (self.x + cell, self.y))


def battleship():
    """ Основная игровая функция. """
    board1 = Board()
    board2 = Board()

    # Расстановка кораблей
    print_intro(board1, board2)
    auto = input('Расставить корабли автоматически? (y/n) ') in ('y', 'Y')
    board1.setup(auto)
    board2.setup()

    # Начало игры
    turn_count = 0
    current_board = board2
    while turn_count < BOARD_SIZE**2 * 2:
        turn_count += 1
        print_intro(board1, board2)
        print(f'Ход №{turn_count} —', end=' ')
        print('Компьютер' if current_board == board1 else 'Игрок')
        print('Координаты выстрела:', end=' ', flush=True)

        # Если текущий игрок — компьютер, то ход происходит автоматически,
        # и если выстрел попал, то не меняем текущего игрока.
        if not current_board.take_shot(is_ai=current_board == board1):
            current_board = board2 if current_board == board1 else board1
        if current_board.is_lose():
            break

    # Игрок, на котором закончился игровой цикл, является победителем.
    print_intro(board1, board2)
    print('Вы проиграли!' if current_board == board1 else 'Вы выиграли!')


    restart = input('Хотите сыграть ещё раз? (y/n) ') in ('y', 'Y')
    if restart:
        battleship()

    os.system(CLEAR_SCREEN)

if __name__ == '__main__':
    battleship()
