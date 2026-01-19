import logging
from risclog.logging import getLogger, log_decorator

# Logger erstellen und konfigurieren
logger = getLogger(__name__)
logger.set_level(logging.DEBUG)
logger.add_file_handler("test.log", level=logging.DEBUG)


@log_decorator
def add_numbers(a: int, b: int):
    """Addiert zwei Zahlen."""
    logger.info("Addiere Zahlen", a=a, b=b)
    result = a + b
    logger.debug("Ergebnis berechnet", result=result)
    return result


@log_decorator
def divide_numbers(a: int, b: int):
    """Dividiert zwei Zahlen."""
    logger.info("Dividiere Zahlen", a=a, b=b)
    try:
        result = a / b
        logger.info("Division erfolgreich", result=result)
        return result
    except ZeroDivisionError:
        logger.error("Division durch Null nicht möglich", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("=== Logger Test gestartet ===")

    # Test 1: Einfache Addition
    logger.info("Test 1: Addition")
    result1 = add_numbers(5, 3)
    logger.info("Resultat Test 1", result=result1)

    # Test 2: Weitere Addition
    logger.info("Test 2: Weitere Addition")
    result2 = add_numbers(10, 20)
    logger.info("Resultat Test 2", result=result2)

    # Test 3: Division - Erfolg
    logger.info("Test 3: Division erfolgreich")
    try:
        result3 = divide_numbers(10, 2)
        logger.info("Resultat Test 3", result=result3)
    except Exception as e:
        logger.error("Fehler bei Test 3", error=str(e))

    # Test 4: Division - Fehler
    logger.info("Test 4: Division mit Fehler")
    try:
        result4 = divide_numbers(10, 0)
    except Exception:
        logger.warning("Erwarteter Fehler wurde abgefangen")

    logger.info("=== Logger Test beendet ===")
