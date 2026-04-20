class Plugboard:
    """
    Коммутационная панель (Steckerbrett).

    Соединяет буквы парами (self-reciprocal):
    если A ↔ Y, то сигнал A → Y и сигнал Y → A.
    Незадействованные буквы проходят без изменений.

    Стандарт военного времени: 10 кабелей (максимум 13).
    """

    def __init__(self):
        # Таблица замен: индекс → индекс (по умолчанию прямое соединение)
        self._table: list[int] = list(range(26))

    def add_connection(self, letter_a: str, letter_b: str):
        """
        Добавить пару соединения (кабель).
        Пример: add_connection('A', 'Y')
        """
        a = ord(letter_a.upper()) - ord("A")
        b = ord(letter_b.upper()) - ord("A")
        if a == b:
            raise ValueError("Нельзя соединить букву саму с собой.")
        if self._table[a] != a:
            raise ValueError(f"Буква {letter_a.upper()} уже задействована в паре.")
        if self._table[b] != b:
            raise ValueError(f"Буква {letter_b.upper()} уже задействована в паре.")
        self._table[a] = b
        self._table[b] = a

    def remove_connection(self, letter: str):
        """Удалить пару, в которой участвует данная буква."""
        i = ord(letter.upper()) - ord("A")
        j = self._table[i]
        self._table[i] = i
        self._table[j] = j

    def clear(self):
        """Снять все кабели."""
        self._table = list(range(26))

    def set_connections(self, pairs: list[tuple[str, str]]):
        """
        Установить сразу несколько пар.
        Пример: set_connections([('A', 'Y'), ('B', 'R'), ('C', 'U')])
        """
        self.clear()
        for a, b in pairs:
            self.add_connection(a, b)

    def encode(self, index: int) -> int:
        """Пропустить сигнал через панель (одинаково для прямого и обратного прохода)."""
        return self._table[index]

    def get_pairs(self) -> list[tuple[str, str]]:
        """Вернуть список активных пар."""
        seen = set()
        pairs = []
        for i, j in enumerate(self._table):
            if i != j and i not in seen:
                pairs.append((chr(i + ord("A")), chr(j + ord("A"))))
                seen.add(i)
                seen.add(j)
        return pairs

    def __repr__(self):
        pairs = self.get_pairs()
        return f"Plugboard({pairs})"
