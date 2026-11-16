import os
import tempfile

# before anything imports config: tests write to a throwaway data folder, never data/test
os.environ["PERSISTENCE_DATA_PATH"] = tempfile.mkdtemp(prefix="aqlqa-tests-")
