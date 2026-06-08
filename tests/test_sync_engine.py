import unittest
from sync import calculate_deltas

class TestVectorStoreSyncEngine(unittest.TestCase):
    def test_calculate_deltas(self):
        # Zendesk articles list
        active_articles = [
            # 1. New article (not in remote store)
            {"id": 101, "title": "New Article", "body": "content", "html_url": "url1", "updated_at": "2026-06-08T12:00:00Z"},
            # 2. Unchanged article
            {"id": 102, "title": "Unchanged Article", "body": "content", "html_url": "url2", "updated_at": "2026-06-08T12:00:00Z"},
            # 3. Updated article (remote timestamp is older)
            {"id": 103, "title": "Updated Article", "body": "new content", "html_url": "url3", "updated_at": "2026-06-08T13:00:00Z"}
        ]

        # Files currently in Vector Store / OpenAI (mock response list)
        remote_files = [
            # Matches article 102 exactly
            {"id": "file_102", "filename": "optibot_102_1780920000.md"},
            # Older version of article 103 (timestamp 1780920000 instead of 1780923600)
            {"id": "file_103_old", "filename": "optibot_103_1780920000.md"},
            # Stale file (article 104 is no longer in active articles)
            {"id": "file_104_stale", "filename": "optibot_104_1780920000.md"},
            # System file or unrelated file (should NOT be deleted)
            {"id": "file_unrelated", "filename": "some_other_doc.pdf"}
        ]

        deltas = calculate_deltas(remote_files, active_articles)

        # 1. Verify "add" list contains article 101
        self.assertEqual(len(deltas["add"]), 1)
        self.assertEqual(deltas["add"][0]["id"], 101)

        # 2. Verify "update" list contains article 103 and points to the old file details
        self.assertEqual(len(deltas["update"]), 1)
        self.assertEqual(deltas["update"][0][0]["id"], 103)
        self.assertEqual(deltas["update"][0][1], "file_103_old")
        self.assertEqual(deltas["update"][0][2], "optibot_103_1780920000.md")

        # 3. Verify "delete" list contains the stale file file_104_stale
        self.assertEqual(len(deltas["delete"]), 1)
        self.assertEqual(deltas["delete"][0]["id"], "file_104_stale")

        # 4. Verify "skip" list contains article 102
        self.assertEqual(len(deltas["skip"]), 1)
        self.assertEqual(deltas["skip"][0]["id"], 102)
