import copy
import unittest

from adapters.travel_e2e_mock import run_travel_mock
from shared.runtime import MockRuntime, load_fixture
from shared.scenarios import run_scenario


class TravelE2EMockTests(unittest.TestCase):
    def test_full_local_flow_binds_draft_to_sourced_total_and_stops_at_hard_approval(self):
        result = run_scenario("family_travel")
        self.assertEqual(result["status"], "waiting_approval")
        self.assertEqual(result["external_effects"], 0)
        self.assertFalse(result["profile"]["saved"])
        self.assertEqual(result["profile"]["retention"], "transient_mock_only")
        self.assertEqual(result["research"]["kind"], "synthetic_fixture_only")
        self.assertFalse(result["research"]["provider_verified"])
        self.assertEqual(len(result["comparison"]["offers"]), 2)
        selected = next(offer for offer in result["comparison"]["offers"] if offer["kind"] == "budget")
        self.assertEqual(selected["total_eur"], "1630.00")
        self.assertEqual(selected["costs"]["transfers"], "70.00")
        self.assertEqual(result["booking_draft"]["quote_id"], selected["id"])
        self.assertEqual(result["booking_draft"]["total_eur"], selected["total_eur"])
        self.assertEqual(result["booking_draft"]["travelers"]["names"], "REDACTED_NOT_COLLECTED")
        self.assertEqual(result["booking_draft"]["reservation_status"], "NOT_RESERVED")
        self.assertEqual(result["itinerary"]["status"], "draft_only")
        self.assertTrue(all(day["opening_hours"] == "unverified" for day in result["itinerary"]["days"]))
        self.assertTrue(all(day["meals_and_rest"] for day in result["itinerary"]["days"]))
        self.assertEqual(result["approval"], {"status": "required", "tier": 3,
                                              "hard_approval": True, "second_factor_required": True,
                                              "granted": False, "real_provider_recheck_required": True})
        self.assertEqual(result["proposal"]["risk_tier"], 3)
        self.assertEqual(result["proposal"]["payload"]["cancellation"], selected["cancellation"])
        self.assertEqual(result["proposal"]["payload"]["costs"], selected["costs"])
        self.assertFalse(result["proposal"]["executed"])
        self.assertFalse(any(entry["executed"] for entry in result["audit"]))
        self.assertTrue(all(not item["publishable"] for item in result["dashboard_mapping"]))

    def test_bad_quotes_or_binding_never_reach_booking_proposal(self):
        cases = {"stale_quote": ("partial", "no_current_quote"),
                 "missing_source": ("blocked", "missing_source"),
                 "missing_quote_time": ("blocked", "missing_quote_time"),
                 "insufficient_capacity": ("blocked", "insufficient_capacity"),
                 "unavailable": ("blocked", "unavailable"),
                 "invalid_cost": ("blocked", "invalid_cost"),
                 "date_mismatch": ("blocked", "date_mismatch"),
                 "price_changed": ("blocked", "draft_quote_mismatch"),
                 "bad_itinerary": ("blocked", "itinerary_invalid")}
        for variant, expected in cases.items():
            with self.subTest(variant=variant):
                result = run_scenario("family_travel", variant=variant)
                self.assertEqual((result["status"], result["reason"]), expected)
                self.assertNotIn("proposal", result)
                self.assertNotIn("booking_draft", result)
                self.assertEqual(result["audit"], [])
                self.assertEqual(result["external_effects"], 0)

    def test_untrusted_context_cannot_invent_freshness_or_hide_cost_lines(self):
        mutations = (
            (lambda data: data["options"][0].update(quoted_at="2026-10-15T12:30:00Z"), "no_current_quote"),
            (lambda data: data["options"][0]["costs"].pop("baggage"), "invalid_cost"),
            (lambda data: data["options"][0].update(source="https://provider.example/offer"), "missing_source"),
        )
        for mutate, rejection in mutations:
            with self.subTest(rejection=rejection):
                data = copy.deepcopy(load_fixture("travel", "cases"))
                mutate(data)
                result = {"external_effects": 0}
                runtime = MockRuntime()
                run_travel_mock(runtime, result, [], context=data)
                self.assertTrue(any(item["reason"] == rejection for item in result["research"]["rejected"]))
                self.assertEqual(result["status"], "partial")
                self.assertEqual(result["reason"], "no_family_fit_offer")
                self.assertNotIn("proposal", result)
                self.assertEqual(runtime.audit, [])

    def test_cancellation_deadline_must_be_valid_and_future(self):
        for cancellation in ("refundable_until_later", "refundable_until_2026-10-01"):
            with self.subTest(cancellation=cancellation):
                data = copy.deepcopy(load_fixture("travel", "cases"))
                data["options"][0]["cancellation"] = cancellation
                result = {"external_effects": 0}
                runtime = MockRuntime()
                run_travel_mock(runtime, result, [], context=data)
                self.assertEqual((result["status"], result["reason"]),
                                 ("partial", "no_family_fit_offer"))
                self.assertNotIn("booking_draft", result)
                self.assertNotIn("proposal", result)
                self.assertEqual(runtime.audit, [])

    def test_unknown_variant_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown family_travel variant"):
            run_scenario("family_travel", variant="unknown")


if __name__ == "__main__":
    unittest.main()
