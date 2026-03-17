"""
Тесты корректности реализации машины Энигма.

Запуск:
    python -m pytest src/back/test_enigma.py -v
или просто:
    python src/back/test_enigma.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.back.enigma import EnigmaMachine
from src.back.plugboard import Plugboard
from src.back.rotor import Rotor
from src.back.reflector import Reflector


def test_self_reciprocal():
    """Главное свойство Энигмы: шифрование зашифрованного текста даёт исходный."""
    e1 = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"])
    ciphertext = e1.encrypt("HELLOWORLD")

    e2 = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"])
    plaintext = e2.encrypt(ciphertext)

    assert plaintext == "HELLOWORLD", f"Ожидалось HELLOWORLD, получено {plaintext}"
    print(f"[OK] Self-reciprocal: HELLOWORLD → {ciphertext} → {plaintext}")


def test_no_letter_to_itself():
    """Буква никогда не шифруется сама в себя."""
    e = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"])
    text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    result = e.encrypt(text)
    for i, (orig, enc) in enumerate(zip(text, result)):
        assert orig != enc, f"Позиция {i}: буква A зашифровалась сама в себя!"
    print(f"[OK] Нет самошифрования: {text[:10]}... → {result[:10]}...")


def test_known_vector():
    """
    Проверка по известному историческому вектору.
    Настройки: роторы I II III, рефлектор B, кольца AAA, позиции AAA, панель пуста.
    Вектор взят из публичных таблиц верификации Enigma.
    """
    e = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"])
    result = e.encrypt("AAAAA")
    # Известный результат для этих настроек
    assert result == "BDZGO", f"Ожидалось BDZGO, получено {result}"
    print(f"[OK] Известный вектор: AAAAA → {result}")


def test_with_plugboard():
    """Plugboard не нарушает свойство самообратимости."""
    pairs = [("A", "B"), ("C", "D"), ("E", "F")]
    e1 = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"], pairs)
    ciphertext = e1.encrypt("TESTMESSAGE")

    e2 = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"], pairs)
    plaintext = e2.encrypt(ciphertext)

    assert plaintext == "TESTMESSAGE", f"Ожидалось TESTMESSAGE, получено {plaintext}"
    print(f"[OK] Plugboard self-reciprocal: TESTMESSAGE → {ciphertext} → {plaintext}")


def test_rotor_stepping():
    """Проверяет механизм stepping: правый ротор шагает на каждом нажатии."""
    e = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"])
    initial = e.get_rotor_positions()
    e.encrypt("A")  # одно нажатие
    after_one = e.get_rotor_positions()
    assert after_one[2] == "B", f"Правый ротор должен быть на B, а он на {after_one[2]}"
    print(f"[OK] Stepping: {initial} → {after_one}")


def test_double_stepping():
    """
    Проверяет двойной шаг среднего ротора.
    Когда средний ротор УЖЕ стоит на позиции turnover (E для ротора II)
    и правый тоже на turnover (V для ротора III), шагают все три ротора:
    - M шагает из-за аномалии двойного шага (он на turnover)
    - L шагает потому что M был на turnover
    - R шагает всегда
    """
    # M=E (turnover ротора II), R=V (turnover ротора III)
    e = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "E", "V"])
    pos_before = e.get_rotor_positions()
    e.encrypt("A")
    pos_after = e.get_rotor_positions()
    # Все три ротора шагают: L: A→B, M: E→F (двойной шаг), R: V→W
    assert pos_after == ["B", "F", "W"], (
        f"Ожидалось двойной шаг ['B','F','W'], получено {pos_after}"
    )
    print(f"[OK] Double stepping: {pos_before} → {pos_after}")


def test_signal_trace():
    """Трассировка сигнала возвращает корректные данные."""
    e = EnigmaMachine(["I", "II", "III"], "UKW-B", [1, 1, 1], ["A", "A", "A"])
    ciphertext, traces = e.encrypt_with_trace("A")
    assert len(traces) == 1
    t = traces[0]
    assert t.input_letter == "A"
    assert t.output_letter == ciphertext
    # Входная и выходная буквы не совпадают
    assert t.input_letter != t.output_letter
    print(f"[OK] Трассировка: A → {t.output_letter}, путь: {t.after_plugboard_in} → "
          f"{t.after_rotor_r_fwd} → {t.after_rotor_m_fwd} → {t.after_rotor_l_fwd} → "
          f"{t.after_reflector} → {t.after_rotor_l_bwd} → {t.after_rotor_m_bwd} → "
          f"{t.after_rotor_r_bwd} → {t.output_letter}")


def test_plugboard_validation():
    """Plugboard: нельзя соединить букву саму с собой или использовать дважды."""
    p = Plugboard()
    p.add_connection("A", "B")
    try:
        p.add_connection("A", "C")
        assert False, "Должно было выброситься исключение"
    except ValueError:
        pass
    try:
        p.add_connection("X", "X")
        assert False, "Должно было выброситься исключение"
    except ValueError:
        pass
    print("[OK] Plugboard валидация работает корректно")


if __name__ == "__main__":
    tests = [
        test_self_reciprocal,
        test_no_letter_to_itself,
        test_known_vector,
        test_with_plugboard,
        test_rotor_stepping,
        test_double_stepping,
        test_signal_trace,
        test_plugboard_validation,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print(f"\nРезультат: {passed} прошло, {failed} упало из {len(tests)} тестов.")
