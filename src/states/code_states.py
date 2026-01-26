from aiogram.dispatcher.filters.state import State, StatesGroup

class CodeStates(StatesGroup):
    CHOOSING_STORE = State()      # Выбор OZON/WB
    RECEIVING_CODE = State()       # Приём фото
    CHOOSING_OFFICE = State()     # Выбор офиса (10 вариантов)
    WAITING_FOR_NAME = State()    # Только для OZON
    WAITING_FOR_PHONE = State()   # Для обоих