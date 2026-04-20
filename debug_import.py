import sys
sys.path.insert(0, ".")
import traceback
try:
    import backend.main
    print("SUCCESS")
except Exception:
    with open('error.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
