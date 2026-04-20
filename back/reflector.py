from .rotors import REFLECTOR_WIRINGS


class Reflector:
    """
    Рефлектор (Umkehrwalze) — соединяет буквы симметричными парами
    и отправляет сигнал обратно через роторы.

    Буква никогда не шифруется сама в себя (self-reciprocal).
    """

    def __init__(self, name: str = "UKW-B"):
        if name not in REFLECTOR_WIRINGS:
            raise ValueError(
                f"Неизвестный рефлектор: {name}. Допустимые: {list(REFLECTOR_WIRINGS)}"
            )
        self.name = name
        self.wiring = REFLECTOR_WIRINGS[name]
        self._table = [ord(c) - ord("A") for c in self.wiring]

    def reflect(self, index: int) -> int:
        """Отразить сигнал: возвращает парную букву."""
        return self._table[index]

    def __repr__(self):
        return f"Reflector({self.name})"
