import sys, os
print("sys.path[:5]:", sys.path[:5])
print("app.database.py exists:", os.path.exists("/app/app/database.py"))
print("app/__init__.py exists:", os.path.exists("/app/app/__init__.py"))
print("tests/__init__.py exists:", os.path.exists("/app/tests/__init__.py"))

try:
    import app.database
    print("import app.database: OK")
except Exception as e:
    print("import app.database: FAILED -", e)

try:
    import tests.conftest
    print("import tests.conftest: OK")
except Exception as e:
    print("import tests.conftest: FAILED -", e)
