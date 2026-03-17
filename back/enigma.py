from dataclasses import dataclass, field

from .rotor import Rotor
from .reflector import Reflector
from .plugboard import Plugboard


@dataclass
class SignalTrace:
    """
    Трассировка пути сигнала для одной буквы — передаётся в интерфейс
    для визуализации (Участник №3, модуль пути сигнала).

    Все значения — буквы (str, один символ A..Z).
    """
    input_letter: str               # исходная буква (нажата на клавиатуре)
    after_plugboard_in: str         # после Steckerbrett (вход в роторы)
    after_rotor_r_fwd: str          # после правого ротора (прямой проход)
    after_rotor_m_fwd: str          # после среднего ротора
    after_rotor_l_fwd: str          # после левого ротора
    after_reflector: str            # после рефлектора
    after_rotor_l_bwd: str          # после левого ротора (обратный проход)
    after_rotor_m_bwd: str          # после среднего ротора
    after_rotor_r_bwd: str          # после правого ротора
    after_plugboard_out: str        # после Steckerbrett (выход)
    output_letter: str              # результирующая (зажжённая) буква
    rotor_positions: list[str] = field(default_factory=list)  # [L, M, R] позиции до шага


class EnigmaMachine:
    """
    Класс-контроллер машины Энигма (модель M3, Wehrmacht/Luftwaffe).
    Объединяет узлы Rotor, Reflector, Plugboard в единую цепь и управляет
    потоком данных — от нажатия клавиши до загорания лампы.

    Порядок роторов: left | middle | right (левый — медленный, правый — быстрый).
    Сигнал: Plugboard → Rotor III → Rotor II → Rotor I → Reflector
                      → Rotor I (inv) → Rotor II (inv) → Rotor III (inv) → Plugboard

    Пример использования:
        from back.enigma import EnigmaMachine
        machine = EnigmaMachine(
            rotor_names=["I", "II", "III"],
            reflector_name="UKW-B",
            ring_settings=[1, 1, 1],
            start_positions=["A", "A", "A"],
            plugboard_pairs=[("A", "Y"), ("B", "R")],
        )
        ciphertext = machine.encrypt("HELLO")
        print(ciphertext)
    """

    def __init__(
        self,
        rotor_names: list[str] = ("I", "II", "III"),
        reflector_name: str = "UKW-B",
        ring_settings: list[int] = (1, 1, 1),
        start_positions: list[str] = ("A", "A", "A"),
        plugboard_pairs: list[tuple[str, str]] = (),
    ):
        if len(rotor_names) != 3:
            raise ValueError("Модель M3 использует ровно 3 ротора.")

        # Роторы: [0]=левый (медленный), [1]=средний, [2]=правый (быстрый)
        self.rotors = [
            Rotor(rotor_names[i], ring_settings[i], start_positions[i])
            for i in range(3)
        ]
        self.reflector = Reflector(reflector_name)
        self.plugboard = Plugboard()
        if plugboard_pairs:
            self.plugboard.set_connections(list(plugboard_pairs))

    # ------------------------------------------------------------------
    # Механизм вращения (stepping mechanism)
    # ------------------------------------------------------------------

    def _step_rotors(self):
        """
        Реализует механизм stepping, включая «двойной шаг» среднего ротора.

        Правила:
        1. Правый ротор шагает всегда при каждом нажатии клавиши.
        2. Средний ротор шагает, если правый стоит на позиции turnover.
        3. Левый ротор шагает, если средний стоит на позиции turnover.
        4. «Двойной шаг»: если средний ротор на позиции turnover,
           он шагает снова вместе с левым (аномалия реального механизма).
        """
        L, M, R = self.rotors[0], self.rotors[1], self.rotors[2]

        # Определяем условия ДО шага
        r_at_turnover = R.is_at_turnover()
        m_at_turnover = M.is_at_turnover()

        # Двойной шаг: средний на turnover → шагают и средний, и левый
        if m_at_turnover:
            L.step()
            M.step()
        elif r_at_turnover:
            # Правый вызывает шаг среднего
            M.step()

        # Правый шагает всегда
        R.step()

    # ------------------------------------------------------------------
    # Кодирование одной буквы
    # ------------------------------------------------------------------

    def _encode_letter(self, letter: str) -> tuple[str, SignalTrace]:
        """
        Кодирует одну букву и возвращает (зашифрованная_буква, трассировка).
        Роторы шагают ДО прохождения сигнала (исторически точно).
        """
        letter = letter.upper()
        if not letter.isalpha():
            raise ValueError(f"Символ '{letter}' не является буквой A-Z.")

        # Сохраняем позиции до шага для трассировки
        positions_before = [r.get_position_letter() for r in self.rotors]

        # Шаг роторов (происходит при каждом нажатии клавиши)
        self._step_rotors()

        idx = ord(letter) - ord("A")

        # 1. Steckerbrett (вход)
        idx = self.plugboard.encode(idx)
        after_plug_in = chr(idx + ord("A"))

        # 2. Правый ротор (прямой проход)
        idx = self.rotors[2].forward(idx)
        after_r_fwd = chr(idx + ord("A"))

        # 3. Средний ротор (прямой проход)
        idx = self.rotors[1].forward(idx)
        after_m_fwd = chr(idx + ord("A"))

        # 4. Левый ротор (прямой проход)
        idx = self.rotors[0].forward(idx)
        after_l_fwd = chr(idx + ord("A"))

        # 5. Рефлектор
        idx = self.reflector.reflect(idx)
        after_ref = chr(idx + ord("A"))

        # 6. Левый ротор (обратный проход)
        idx = self.rotors[0].backward(idx)
        after_l_bwd = chr(idx + ord("A"))

        # 7. Средний ротор (обратный проход)
        idx = self.rotors[1].backward(idx)
        after_m_bwd = chr(idx + ord("A"))

        # 8. Правый ротор (обратный проход)
        idx = self.rotors[2].backward(idx)
        after_r_bwd = chr(idx + ord("A"))

        # 9. Steckerbrett (выход)
        idx = self.plugboard.encode(idx)
        output = chr(idx + ord("A"))

        trace = SignalTrace(
            input_letter=letter,
            after_plugboard_in=after_plug_in,
            after_rotor_r_fwd=after_r_fwd,
            after_rotor_m_fwd=after_m_fwd,
            after_rotor_l_fwd=after_l_fwd,
            after_reflector=after_ref,
            after_rotor_l_bwd=after_l_bwd,
            after_rotor_m_bwd=after_m_bwd,
            after_rotor_r_bwd=after_r_bwd,
            after_plugboard_out=output,
            output_letter=output,
            rotor_positions=positions_before,
        )

        return output, trace

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def encrypt(self, text: str) -> str:
        """
        Зашифровать / расшифровать строку.
        Небуквенные символы (пробелы, цифры) пропускаются без изменений.
        """
        result = []
        for char in text.upper():
            if char.isalpha():
                encoded, _ = self._encode_letter(char)
                result.append(encoded)
            else:
                result.append(char)
        return "".join(result)

    def encrypt_with_trace(self, text: str) -> tuple[str, list[SignalTrace]]:
        """
        Зашифровать строку и вернуть полную трассировку сигнала для каждой буквы.
        Используется интерфейсом для визуализации пути сигнала.

        Возвращает: (зашифрованный_текст, [SignalTrace, ...])
        """
        result = []
        traces = []
        for char in text.upper():
            if char.isalpha():
                encoded, trace = self._encode_letter(char)
                result.append(encoded)
                traces.append(trace)
        return "".join(result), traces

    def reset(self, start_positions: list[str] = ("A", "A", "A")):
        """Сбросить позиции роторов к начальным значениям."""
        for i, rotor in enumerate(self.rotors):
            rotor.set_position(start_positions[i])

    def get_rotor_positions(self) -> list[str]:
        """Текущие позиции роторов [левый, средний, правый]."""
        return [r.get_position_letter() for r in self.rotors]

    def get_plugboard_pairs(self) -> list[tuple[str, str]]:
        """Список активных пар коммутационной панели."""
        return self.plugboard.get_pairs()

    def __repr__(self):
        rotors = " | ".join(repr(r) for r in self.rotors)
        return (
            f"EnigmaMachine(rotors=[{rotors}], "
            f"reflector={self.reflector.name}, "
            f"plugboard={self.plugboard.get_pairs()})"
        )
