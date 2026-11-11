import json
import random
import tempfile
import unittest
from pathlib import Path

import ccar


class TrainerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = ccar.Trainer.open(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def wrong(self, qid):
        q = self.t.bank[qid]
        wrong_keys = [o["key"] for o in q["options"] if o["key"] not in q["correct"]]
        return wrong_keys[:2] if q["multi"] else wrong_keys[:1]

    def filler(self, n, skip):
        for qid in [i for i in self.t.bank if i not in skip][:n]:
            self.t.answer(qid, self.t.bank[qid]["correct"])

    def test_rules_cover_all_30_task_statements(self):
        self.assertEqual(len(self.t.rules), 30)
        self.assertTrue({q["taskRef"] for q in self.t.bank.values()} <= set(self.t.rules))

    def test_wrong_answer_returns_after_5_to_10_answers(self):
        qid = "1-1-q01"
        fb = self.t.answer(qid, self.wrong(qid))
        self.assertFalse(fb["correct"])
        self.assertTrue(5 <= fb["next_review_in"] <= 10)
        self.filler(fb["next_review_in"] - 1, {qid})
        self.assertNotEqual(self.t.next_question(rng=random.Random(1))["id"], qid)
        self.filler(1, {qid} | set(self.t.qstate))
        self.assertEqual(self.t.next_question(rng=random.Random(1))["id"], qid)

    def test_micro_lesson_only_after_two_errors(self):
        qid = "1-1-q01"
        self.t.answer(qid, self.wrong(qid))
        self.filler(10, {qid})
        nq = self.t.next_question(rng=random.Random(1))
        self.assertEqual((nq["id"], nq["lesson"]), (qid, None))
        self.t.answer(qid, self.wrong(qid))
        self.filler(10, {qid} | set(self.t.qstate))
        nq = self.t.next_question(rng=random.Random(1))
        self.assertEqual(nq["id"], qid)
        self.assertEqual(nq["lesson"]["task"], "1.1")
        self.assertTrue(nq["lesson"]["rule_it"])

    def test_correct_after_error_schedules_one_confirmation(self):
        qid = "1-1-q01"
        self.t.answer(qid, self.wrong(qid))
        fb = self.t.answer(qid, self.t.bank[qid]["correct"])
        self.assertEqual(fb["next_review_in"], ccar.CONFIRM_GAP)
        fb = self.t.answer(qid, self.t.bank[qid]["correct"])
        self.assertIsNone(fb["next_review_in"])

    def test_multi_response_needs_exact_set(self):
        qid = "1-1-e03"
        self.assertFalse(self.t.answer(qid, ["B"])["correct"])
        self.assertTrue(self.t.answer(qid, ["E", "B"])["correct"])
        with self.assertRaises(ValueError):
            self.t.answer(qid, ["Z"])

    def test_weak_domain_is_drawn_more_often(self):
        for qid in [i for i, q in self.t.bank.items() if q["domain"] == 2][:20]:
            self.t.answer(qid, self.wrong(qid))
        for qid in [i for i, q in self.t.bank.items() if q["domain"] == 4][:20]:
            self.t.answer(qid, self.t.bank[qid]["correct"])
        rng = random.Random(7)
        for s in self.t.qstate.values():
            s.due_idx = None
        draws = [self.t.next_question(rng=rng)["domain"] for _ in range(400)]
        self.assertGreater(draws.count(2), 3 * draws.count(4))

    def test_practice_skips_reserved_pool(self):
        rng = random.Random(3)
        for _ in range(50):
            self.assertNotIn(self.t.next_question(rng=rng)["id"], self.t.reserved)

    def test_mock_is_4_scenarios_by_15_and_scores(self):
        m = self.t.build_mock("final", random.Random(5))
        self.assertEqual(len(m["questions"]), 60)
        self.assertEqual(len(set(m["questions"])), 60)
        scn = [self.t.bank[q]["scenario"] for q in m["questions"]]
        self.assertEqual(sorted(scn.count(s) for s in set(scn)), [15] * 4)
        answers = {q: self.t.bank[q]["correct"] for q in m["questions"][:30]}
        r = self.t.submit_mock(m["id"], answers, [])
        self.assertEqual((r["ok"], r["n"]), (30, 60))
        self.assertEqual(self.t.counter, 60)
        again = self.t.submit_mock(m["id"], {}, [])
        self.assertEqual(again["ok"], 30)
        self.assertEqual(self.t.counter, 60)

    def test_final_mock_prefers_unseen_and_unused_questions(self):
        m1 = self.t.build_mock("final", random.Random(1))
        self.t.submit_mock(m1["id"], {}, [])
        m2 = self.t.build_mock("final", random.Random(1))
        self.assertFalse(set(m1["questions"]) & set(m2["questions"]))

    def test_state_survives_reload(self):
        self.t.answer("1-1-q01", self.wrong("1-1-q01"))
        t2 = ccar.Trainer.open(Path(self.tmp.name))
        self.assertEqual(t2.qstate["1-1-q01"].wrong, 1)

    def test_explain_uses_italian_and_official_explanation(self):
        self.t.translations = {"1-1-q01": {"A": "spiegazione A", "Z": "chiave estranea"},
                               "os-01": {"explanation": "spiegazione ufficiale"}}
        e = self.t.explain("1-1-q01")
        self.assertEqual(e["rationale_it"], {"A": "spiegazione A"})
        self.assertIsNone(e["explanation_it"])
        e = self.t.explain("os-01")
        self.assertEqual(e["rationale"], {})
        self.assertTrue(e["explanation"])
        self.assertEqual(e["explanation_it"], "spiegazione ufficiale")
        self.assertIsNone(self.t.explain("1-1-e03")["rationale_it"])

    def test_mock_id_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            self.t.load_mock("../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
