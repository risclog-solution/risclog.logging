#!/Users/riscms/repos/Risclog/risclog.logging/.appenv/current/bin/python
"""Einfaches Test-Skript für den risclog Logger."""

import logging
from risclog.logging import getLogger, log_decorator

# Logger erstellen
logger = getLogger(__name__)
logger.add_file_handler("test_logger.log", level=logging.DEBUG)
logger.set_level(logging.DEBUG)

print("=== risclog Logger Test ===\n")

# Test 1: Einfaches Logging
print("Test 1: Einfaches Info-Logging")
logger.info("Das ist eine Info-Nachricht")

# Test 2: Logging mit Kontextdaten
print("\nTest 2: Logging mit Kontextdaten")
logger.info("Benutzer angemeldet", user_id=42, email="test@example.com")

# Test 3: Warning
print("\nTest 3: Warning")
logger.warning("Das ist eine Warnung", severity="medium")

# Test 4: Error
print("\nTest 4: Error")
logger.error("Das ist ein Fehler", error_code=500)

# Test 5: Decorator
print("\nTest 5: Mit @log_decorator")


@log_decorator
def add_numbers(a, b):
    """Addiert zwei Zahlen."""
    result = a + b
    logger.info("Addition durchgeführt", a=a, b=b, result=result)
    return result


result = add_numbers(10, 20)
print(f"Ergebnis: {result}")

print("\n✓ Tests abgeschlossen!")
print("Logfile: test_logger.log")
