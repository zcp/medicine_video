import sys
print("Default app:", end=" ")
try:
    import app
    print(app.__file__)
except ImportError:
    print("NOT FOUND")

sys.path.insert(0, '/app')
print("After /app insert:", end=" ")
try:
    import app
    print(app.__file__)
except ImportError:
    print("NOT FOUND")
