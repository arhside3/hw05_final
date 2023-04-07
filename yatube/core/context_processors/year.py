import datetime as dt


def year(request: str) -> None:
    del request
    """Args:
        request: Параметр который отпровляет HTTP запрос

    Returns:
        Функция year возвращает переменную с текущим годом.
    """

    return {'year': dt.datetime.now()}
