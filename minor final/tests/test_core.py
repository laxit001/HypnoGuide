import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypnoguide.core import ConversationBuffer, LongTermMemory, MAX_BUFFER_TURNS, PREFERENCES_FILE

class TestHypnoGuideCore(unittest.TestCase):
    def setUp(self):
        # Clean up preferences file
        if os.path.exists(PREFERENCES_FILE):
            os.remove(PREFERENCES_FILE)

    def tearDown(self):
        if os.path.exists(PREFERENCES_FILE):
            os.remove(PREFERENCES_FILE)

    def test_buffer_trimming(self):
        buffer = ConversationBuffer()
        # Add more than max turns
        for i in range(MAX_BUFFER_TURNS + 2):
            buffer.add_turn("user", f"msg {i}")
        
        summary = json.loads(buffer.get_summary())
        self.assertEqual(len(summary), MAX_BUFFER_TURNS)
        self.assertEqual(summary[-1]["text"], f"msg {MAX_BUFFER_TURNS + 1}")

    def test_long_term_memory_persistence(self):
        memory = LongTermMemory()
        memory.update("skill_level", "novice")
        
        # Reload memory
        new_memory = LongTermMemory()
        summary = json.loads(new_memory.get_summary())
        self.assertEqual(summary.get("skill_level"), "novice")

    def test_long_term_memory_restrictions(self):
        memory = LongTermMemory()
        memory.update("medical_history", "some history") # Should be ignored
        
        summary = json.loads(memory.get_summary())
        self.assertNotIn("medical_history", summary)

if __name__ == '__main__':
    unittest.main()
