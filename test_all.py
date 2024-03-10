import pytest
from server.knowledge_base.kb_service.faiss_kb_service import FaissKBService
from server.knowledge_base.migrate import create_tables
from server.knowledge_base.utils import KnowledgeFile

class TestFaissKBService:
    kbService = FaissKBService("test")
    test_kb_name = "test"
    test_file_name = "README.md"
    testKnowledgeFile = KnowledgeFile(test_file_name, test_kb_name)
    search_content = "如何启动api服务"

    def test_init(self):
        create_tables()

    def test_create_db(self):
        assert self.kbService.create_kb()

    def test_add_doc(self):
        assert self.kbService.add_doc(self.testKnowledgeFile)

    def test_search_db(self):
        result = self.kbService.search_docs(self.search_content)
        assert len(result) > 0

    def test_delete_doc(self):
        assert self.kbService.delete_doc(self.testKnowledgeFile)

    def test_delete_db(self):
        assert self.kbService.drop_kb()

if __name__ == "__main__":
    pytest.main()

