from .rotors import ROTOR_WIRINGS, ROTOR_TURNOVERS


class Rotor:
    """
    Один ротор машины Энигма.

    Параметры:
        name       — название ротора (I, II, III, IV, V)
        ring_setting — кольцевая настройка Ringstellung (1..26, по умолчанию 1 = A)
        position   — начальная позиция (буква A..Z)
    """

    def __init__(self, name: str, ring_setting: int = 1, position: str = "A"):
        if name not in ROTOR_WIRINGS:
            raise ValueError(f"Неизвестный ротор: {name}. Допустимые: {list(ROTOR_WIRINGS)}")
        self.name = name
        self.wiring = ROTOR_WIRINGS[name]
        self.turnover = ROTOR_TURNOVERS[name]
        self.ring_setting = ring_setting - 1  # переводим в 0-индекс
        self.position = ord(position.upper()) - ord("A")

        # Предвычисляем обратную проводку (inverse wiring) для прохода сигнала назад
        self._forward = [ord(c) - ord("A") for c in self.wiring]
        self._backward = [0] * 26
        for i, v in enumerate(self._forward):
            self._backward[v] = i

    # ------------------------------------------------------------------
    # Вращение
    # ------------------------------------------------------------------

    def step(self):
        """Повернуть ротор на одну позицию вперёд."""
        self.position = (self.position + 1) % 26

    def is_at_turnover(self) -> bool:
        """True, если ротор стоит на позиции turnover (вызовет шаг следующего ротора)."""
        return chr(self.position + ord("A")) == self.turnover

    # ------------------------------------------------------------------
    # Прохождение сигнала
    # ------------------------------------------------------------------

    def _encode(self, table: list[int], index: int) -> int:
        """Общий метод кодирования с учётом позиции ротора и Ringstellung."""
        # Смещение с учётом текущей позиции и кольцевой настройки
        offset = (self.position - self.ring_setting) % 26
        shifted_in = (index + offset) % 26
        output = table[shifted_in]
        return (output - offset) % 26

    def forward(self, index: int) -> int:
        """Прямой проход сигнала (справа налево, до рефлектора)."""
        return self._encode(self._forward, index)

    def backward(self, index: int) -> int:
        """Обратный проход сигнала (слева направо, после рефлектора)."""
        return self._encode(self._backward, index)

    # ------------------------------------------------------------------
    # Вспомогательное
    # ------------------------------------------------------------------

    def get_position_letter(self) -> str:
        """Буква текущей позиции (отображается в окне машины)."""
        return chr(self.position + ord("A"))

    def set_position(self, letter: str):
        """Установить позицию ротора по букве."""
        self.position = ord(letter.upper()) - ord("A")

    def __repr__(self):
        return (
            f"Rotor({self.name}, pos={self.get_position_letter()}, "
            f"ring={self.ring_setting + 1})"
        )
