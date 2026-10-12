import unittest
from pathlib import Path

from knowledge_transfer_agent.symbols import hints, role_hint


class SymbolTests(unittest.TestCase):
    def test_python_routes_imports_and_foreign_keys(self):
        text = '''from .db import User
class Session:
    owner = ForeignKey("users.id")
@router.post("/login")
def login():
    pass
'''
        symbols, imports = hints(Path("routes.py"), text)
        self.assertIn(".db", imports)
        self.assertIn(("POST /login", "route"), {(s.name, s.kind) for s in symbols})
        self.assertIn(("users.id", "foreign-key"), {(s.name, s.kind) for s in symbols})

    def test_typescript_and_schema_hints(self):
        symbols, imports = hints(Path("login.ts"),
                                 'import { api } from "./api";\nexport function login() {}\n')
        self.assertIn("./api", imports)
        self.assertIn("login", {symbol.name for symbol in symbols})
        symbols, _ = hints(Path("schema.prisma"), "model User {\n  id Int @id\n}\n")
        self.assertIn("User", {symbol.name for symbol in symbols})
        self.assertEqual(role_hint(Path("tests/test_auth.py")), "tests and expected behavior")


if __name__ == "__main__":
    unittest.main()
