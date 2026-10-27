from app.code_intelligence.ast_parser import PythonASTParser

def test_ast_parser_extracts_functions_and_classes():
    parser = PythonASTParser()
    sample_code = (
        'import os\n'
        'from datetime import datetime\n\n'
        'class UserService:\n'
        '    """Handles user operations."""\n'
        '    def __init__(self, db):\n'
        '        self.db = db\n\n'
        '    def get_user(self, user_id: str) -> dict:\n'
        '        return {"id": user_id}\n\n'
        '@app.get("/users/{user_id}")\n'
        'async def read_user(user_id: str):\n'
        '    service = UserService(None)\n'
        '    return service.get_user(user_id)\n'
    )

    res = parser.parse_source(sample_code, "app/routes.py")
    assert res["has_syntax_error"] is False
    assert len(res["imports"]) == 2
    
    entities = res["entities"]
    names = [e["name"] for e in entities]
    assert "UserService" in names
    assert "UserService.__init__" in names or "UserService.get_user" in names
    assert "read_user" in names

    endpoints = res["endpoints"]
    assert len(endpoints) == 1
    assert endpoints[0]["name"] == "read_user"
    assert endpoints[0]["method"] == "GET"

def test_ast_parser_handles_syntax_errors_gracefully():
    parser = PythonASTParser()
    invalid_code = "def broken_func(x \n return x"
    res = parser.parse_source(invalid_code, "broken.py")
    assert res["has_syntax_error"] is True
    assert "Syntax error" in res["error_message"]
