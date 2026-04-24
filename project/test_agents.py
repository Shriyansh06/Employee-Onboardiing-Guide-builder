import unittest
from agents.policy_fetcher import policy_fetcher_agent
from orchestrator import _coerce_evaluation, merge_state

class TestOnboardingAgents(unittest.TestCase):

    def test_policy_fetcher_engineering(self):
        """Test that engineering roles get tech/compliance policies."""
        info = {"department": "Engineering"}
        policies = policy_fetcher_agent(info)
        
        self.assertIn("IT_SETUP", policies)
        self.assertIn("COMPLIANCE", policies)
        self.assertIn("laptop_request", policies["IT_SETUP"])

    def test_policy_fetcher_hr(self):
        """Test that HR roles get HR/benefits policies."""
        info = {"department": "Human Resources"}
        policies = policy_fetcher_agent(info)
        
        self.assertIn("HR_POLICIES", policies)
        self.assertIn("BENEFITS", policies)
        self.assertIn("pto", policies["HR_POLICIES"])

    def test_policy_fetcher_fallback(self):
        """Test that unknown departments get a decent fallback."""
        info = {"department": "Marketing"}
        policies = policy_fetcher_agent(info)
        
        self.assertIn("HR_POLICIES", policies) # All get HR
        self.assertIn("vpn_access", policies["IT_SETUP"]["general"])

    def test_coerce_evaluation_robustness(self):
        """Test that evaluation coercion handles various inputs."""
        # Case 1: Minimal Dict
        ev1 = _coerce_evaluation({"score": 8, "feedback": "Good"})
        self.assertEqual(ev1["overall_score"], 8)
        self.assertEqual(ev1["summary"], "Good")
        
        # Case 2: JSON string
        ev2 = _coerce_evaluation('{"overall_score": 7, "improvements": ["Tone"]}')
        self.assertEqual(ev2["overall_score"], 7)
        self.assertEqual(ev2["suggestions"], ["Tone"])
        
        # Case 3: Messy input
        ev3 = _coerce_evaluation("Just some text")
        self.assertEqual(ev3["overall_score"], 0)
        self.assertEqual(ev3["summary"], "Just some text")

    def test_merge_state(self):
        """Test orchestrator state merging."""
        state = {"a": 1, "b": 2}
        patch = {"b": 3, "c": 4}
        merge_state(state, patch)
        self.assertEqual(state, {"a": 1, "b": 3, "c": 4})

if __name__ == "__main__":
    unittest.main()
