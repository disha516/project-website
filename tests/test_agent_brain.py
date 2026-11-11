import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("GEMINI_API_KEY", "unit-test-key")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")

import agent_brain


class AgentBrainTests(unittest.TestCase):
    def setUp(self):
        agent_brain.query_cache.clear()

    def test_embedding_is_truncated_to_atlas_index_dimension(self):
        values = list(range(1024))
        response = SimpleNamespace(embeddings=[SimpleNamespace(values=values)])
        with patch.object(agent_brain.client.models, "embed_content", return_value=response):
            vector = agent_brain.get_embedding("sample question")
        self.assertEqual(len(vector), 768)
        self.assertEqual(vector[-1], 767)

    def test_selected_subject_and_difficulty_reach_solver(self):
        generated = SimpleNamespace(text="A worked solution.")
        with patch.object(agent_brain, "search_similar_questions", return_value=[]) as search, \
             patch.object(agent_brain.client.models, "generate_content", return_value=generated) as generate:
            answer, score = agent_brain.get_answer_from_tutor(
                "Explain a reaction rate question",
                "Chemistry",
                difficulty="Hard",
                search_priority="Vector Database (Fast)",
            )
        search.assert_called_once_with("Explain a reaction rate question", "Chemistry")
        prompt = generate.call_args.kwargs["contents"][0]
        self.assertIn("specializing in Chemistry", prompt)
        self.assertIn("Requested problem level: Hard", prompt)
        self.assertEqual(answer, "A worked solution.")
        self.assertEqual(score, 0.0)

    def test_full_ai_fallback_skips_vector_search(self):
        generated = SimpleNamespace(text="AI-only solution.")
        with patch.object(agent_brain, "search_similar_questions", side_effect=AssertionError("must not search")) as search, \
             patch.object(agent_brain.client.models, "generate_content", return_value=generated):
            answer, _ = agent_brain.get_answer_from_tutor(
                "A distinct question for fallback mode",
                "Physics",
                difficulty="Medium",
                search_priority="Full AI Engine Fallback",
            )
        search.assert_not_called()
        self.assertEqual(answer, "AI-only solution.")

    def test_cache_key_includes_difficulty_and_search_mode(self):
        generated = SimpleNamespace(text="First answer.")
        with patch.object(agent_brain, "search_similar_questions", return_value=[]), \
             patch.object(agent_brain.client.models, "generate_content", return_value=generated) as generate:
            agent_brain.get_answer_from_tutor("Unique cache question", "Physics", difficulty="Easy")
            agent_brain.get_answer_from_tutor("Unique cache question", "Physics", difficulty="Hard")
        self.assertEqual(generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
