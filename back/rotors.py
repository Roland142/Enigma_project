# Данные роторов и рефлекторов Wehrmacht/Luftwaffe
# Источник: Теоретическая база, подготовленная Участником №1

# Строки проводки роторов (индекс = входная буква A=0..Z=25, значение = выходная буква)
ROTOR_WIRINGS = {
    "I":   "EKMFLGDQVZNTOWYHXUSPAIBRCJ",
    "II":  "AJDKSIRUXBLHWTMCQGZNPYFVOE",
    "III": "BDFHJLCPRTXVZNYEIWGAKMUSQO",
    "IV":  "ESOVPZJAYQUIRHXLNFTGKDCMWB",
    "V":   "VZBRGITYUPSDNHLXAWMJQOFECK",
}

# Позиции поворота (notch) — буква на кольце, при которой происходит шаг следующего ротора
# Turnover — буква в окне, при которой следующий ротор шагает
ROTOR_TURNOVERS = {
    "I":   "Q",  # когда в окне Q → следующий ротор шагает (физический notch на Y)
    "II":  "E",  # notch на M
    "III": "V",  # notch на D
    "IV":  "J",  # notch на R
    "V":   "Z",  # notch на H
}

# Строки проводки рефлекторов (симметричные пары)
REFLECTOR_WIRINGS = {
    "UKW-B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "UKW-C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",
}

# Входной диск ETW (Eintrittswalze) — прямое соединение, без изменений
ETW_WIRING = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
