try:
    import numpy
    print(f"Numpy version: {numpy.__version__}")
    import pandas
    print(f"Pandas version: {pandas.__version__}")
    print("Import success!")
except ImportError as e:
    print(f"Import failed: {e}")
except ValueError as e:
    print(f"Value Error (Binary incompatibility): {e}")
except Exception as e:
    print(f"Other error: {e}")
