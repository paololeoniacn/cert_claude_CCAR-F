#!/usr/bin/env python3
"""CCAR-F adaptive trainer: engine, CLI (chat mode) and local HTTP server (web UI).

Stdlib only. Run with: uv run trainer/ccar.py <command>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
BANK_FILE = PROJECT / "fonti" / "ccafpreparation-bank-2026-11-10.json"
BLUEPRINT_FILE = PROJECT / "KB" / "esame" / "blueprint.md"
SCENARIOS_FILE = ROOT / "scenarios.json"
TRANSLATION_FILE = ROOT / "data" / "rationale_it.jsonl"  # built by translate.py, optional
STATE_DIR = ROOT / "state"
WEB_DIR = ROOT / "web"

DOMAINS = {
    1: ("Agentic Architecture & Orchestration", 0.27),
    2: ("Tool Design & MCP Integration", 0.18),
    3: ("Claude Code Configuration & Workflows", 0.20),
    4: ("Prompt Engineering & Structured Output", 0.20),
    5: ("Context Management & Reliability", 0.15),
}
REVIEW_GAP = (5, 10)        # a wrong answer comes back after 5-10 answers
CONFIRM_GAP = 30            # first correct answer after an error: one more check later
LESSON_AFTER_WRONG = 2      # micro-lesson before re-serving a question missed twice
MASTERY_WINDOW = 20         # last N attempts per domain
MOCK_SCENARIOS, MOCK_PER_SCENARIO, MOCK_MINUTES = 4, 15, 120
RESERVED_PER_SCENARIO = 25  # kept fresh for the final mocks (day 6)
TARGET = 0.85

log = logging.getLogger("ccar")


# ---------------------------------------------------------------- data loading

def load_bank() -> dict[str, dict]:
    return {q["id"]: q for q in json.loads(BANK_FILE.read_text(encoding="utf-8"))}


def load_rules() -> dict[str, dict]:
    """Italian rule per task statement, parsed from KB/esame/blueprint.md (single source)."""
    rules = {}
    pattern = re.compile(r"^- \*\*(\d\.\d) ([^*]+)\*\*: (.+)$")
    for line in BLUEPRINT_FILE.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            rules[m.group(1)] = {"title": m.group(2).strip(), "rule": m.group(3).strip()}
    return rules


def load_translations() -> dict[str, dict]:
    if not TRANSLATION_FILE.exists():
        return {}
    out = {}
    for line in TRANSLATION_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["id"]] = row["rationale_it"]
    return out


def load_scenarios() -> dict[str, str]:
    return json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))


def reserved_ids(bank: dict[str, dict]) -> set[str]:
    """Deterministic pool kept out of practice so the final mocks use unseen questions."""
    by_scn: dict[str, list[str]] = {}
    for qid, q in bank.items():
        if q["source"] != "official-sample":
            by_scn.setdefault(q["scenario"], []).append(qid)
    out = set()
    for ids in by_scn.values():
        ids.sort(key=lambda i: hashlib.sha256(i.encode()).hexdigest())
        out.update(ids[:RESERVED_PER_SCENARIO])
    return out


# ---------------------------------------------------------------- state

@dataclass
class QState:
    seen: int = 0
    wrong: int = 0
    streak: int = 0
    last_idx: int = -1
    due_idx: int | None = None


@dataclass
class Trainer:
    bank: dict[str, dict]
    rules: dict[str, dict]
    scenarios: dict[str, str]
    state_dir: Path = STATE_DIR
    attempts: list[dict] = field(default_factory=list)
    qstate: dict[str, QState] = field(default_factory=dict)
    reserved: set[str] = field(default_factory=set)
    translations: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def open(cls, state_dir: Path = STATE_DIR) -> "Trainer":
        bank = load_bank()
        t = cls(bank, load_rules(), load_scenarios(), state_dir)
        t.reserved = reserved_ids(bank)
        t.translations = load_translations()
        t.state_dir.mkdir(parents=True, exist_ok=True)
        if t.attempts_file.exists():
            for line in t.attempts_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    t._apply(json.loads(line))
        return t

    @property
    def attempts_file(self) -> Path:
        return self.state_dir / "attempts.jsonl"

    @property
    def counter(self) -> int:
        return len(self.attempts)

    def _apply(self, a: dict) -> None:
        idx = len(self.attempts)
        self.attempts.append(a)
        s = self.qstate.setdefault(a["qid"], QState())
        s.seen += 1
        s.last_idx = idx
        if a["correct"]:
            s.streak += 1
            s.due_idx = idx + 1 + CONFIRM_GAP if (s.wrong and s.streak == 1) else None
        else:
            s.wrong += 1
            s.streak = 0
            rng = random.Random(f"{a['qid']}:{idx}")
            s.due_idx = idx + 1 + rng.randint(*REVIEW_GAP)  # due after that many other answers

    def record(self, qid: str, answer: list[str], mode: str, session: str | None = None) -> dict:
        q = self.bank[qid]
        a = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "qid": qid,
            "domain": q["domain"],
            "task": q["taskRef"],
            "answer": sorted(answer),
            "correct": sorted(answer) == sorted(q["correct"]),
            "mode": mode,
            "session": session,
        }
        with self.attempts_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
        self._apply(a)
        log.info("attempt qid=%s mode=%s correct=%s session=%s", qid, mode, a["correct"], session)
        return a

    # ------------------------------------------------------------ metrics

    def mastery(self) -> dict[int, dict]:
        out = {}
        for d, (name, weight) in DOMAINS.items():
            recent = [a for a in self.attempts if a["domain"] == d][-MASTERY_WINDOW:]
            ok = sum(a["correct"] for a in recent)
            total_d = [a for a in self.attempts if a["domain"] == d]
            out[d] = {
                "name": name,
                "weight": weight,
                "recent_n": len(recent),
                "recent_ok": ok,
                "score": (ok + 1) / (len(recent) + 2),  # Laplace: 50% with no data
                "accuracy": ok / len(recent) if recent else None,
                "total": len(total_d),
                "total_ok": sum(a["correct"] for a in total_d),
                "seen_questions": len({a["qid"] for a in total_d}),
                "bank_questions": sum(1 for q in self.bank.values() if q["domain"] == d),
            }
        return out

    def stats(self) -> dict:
        m = self.mastery()
        due = [qid for qid, s in self.qstate.items() if s.due_idx is not None and s.due_idx <= self.counter]
        pending = [qid for qid, s in self.qstate.items() if s.due_idx is not None]
        streak = 0
        for a in reversed(self.attempts):
            if not a["correct"]:
                break
            streak += 1
        mocks = [json.loads(p.read_text()) for p in sorted(self.state_dir.glob("mock-*.json"))]
        return {
            "answered": self.counter,
            "correct": sum(a["correct"] for a in self.attempts),
            "streak": streak,
            "due_now": len(due),
            "pending_reviews": len(pending),
            "never_seen": sum(1 for qid in self.bank if qid not in self.qstate),
            "reserved_unseen": sum(1 for qid in self.reserved if qid not in self.qstate),
            "weighted_mastery": sum(v["score"] * v["weight"] for v in m.values()),
            "mastery": m,
            "mocks": [
                {k: x.get(k) for k in ("id", "kind", "started", "submitted", "score", "n", "ok")}
                for x in mocks if x.get("submitted")
            ],
            "open_mocks": [{"id": x["id"], "kind": x["kind"], "started": x["started"], "answered": len(x["answers"])}
                           for x in mocks if not x.get("submitted")],
            "target": TARGET,
        }

    def missed(self) -> list[dict]:
        out = []
        for qid, s in self.qstate.items():
            if s.wrong:
                q = self.bank[qid]
                out.append({"qid": qid, "domain": q["domain"], "task": q["taskRef"], "wrong": s.wrong,
                            "streak": s.streak, "due_in": None if s.due_idx is None else s.due_idx - self.counter,
                            "stem": q["stem"][:140]})
        return sorted(out, key=lambda x: (-x["wrong"], x["streak"]))

    # ------------------------------------------------------------ selection

    def next_question(self, domain: int | None = None, rng: random.Random | None = None) -> dict:
        rng = rng or random.Random()
        ok = lambda qid: domain is None or self.bank[qid]["domain"] == domain  # noqa: E731
        due = [(s.due_idx, qid) for qid, s in self.qstate.items()
               if s.due_idx is not None and s.due_idx <= self.counter and ok(qid)]
        if due:
            qid = min(due)[1]
            reason = "review"
        else:
            unseen = [qid for qid in self.bank if qid not in self.qstate and qid not in self.reserved and ok(qid)]
            if not unseen:  # practice pool exhausted: reserved, then least recently seen
                unseen = [qid for qid in self.bank if qid not in self.qstate and ok(qid)]
            if unseen:
                m = self.mastery()
                by_dom: dict[int, list[str]] = {}
                for qid in unseen:
                    by_dom.setdefault(self.bank[qid]["domain"], []).append(qid)
                doms = sorted(by_dom)
                weights = [DOMAINS[d][1] * (1.2 - m[d]["score"]) ** 2 for d in doms]
                d = rng.choices(doms, weights=weights)[0]
                qid = rng.choice(sorted(by_dom[d]))
                reason = "new"
            else:
                pool = [qid for qid in self.bank if ok(qid)]
                qid = min(pool, key=lambda i: self.qstate[i].last_idx)
                reason = "refresh"
        s = self.qstate.get(qid, QState())
        return self.public_question(qid) | {
            "reason": reason,
            "times_wrong": s.wrong,
            "lesson": self.lesson(qid) if s.wrong >= LESSON_AFTER_WRONG else None,
        }

    def public_question(self, qid: str) -> dict:
        q = self.bank[qid]
        return {
            "id": qid,
            "domain": q["domain"],
            "domain_name": DOMAINS[q["domain"]][0],
            "task": q["taskRef"],
            "scenario": q["scenario"],
            "scenario_text": self.scenarios.get(q["scenario"], ""),
            "stem": q["stem"],
            "multi": q["multi"],
            "pick": len(q["correct"]),
            "options": q["options"],
        }

    def lesson(self, qid: str) -> dict:
        q = self.bank[qid]
        r = self.rules.get(q["taskRef"], {})
        return {"task": q["taskRef"], "title": r.get("title", ""), "rule_it": r.get("rule", "")}

    def explain(self, qid: str) -> dict:
        """Per-option rationale (official samples only have one explanation), with Italian when translated."""
        q, it = self.bank[qid], self.translations.get(qid, {})
        return {
            "rationale": q["rationale"],
            "rationale_it": {k: v for k, v in it.items() if k in q["rationale"]} or None,
            "explanation": q.get("explanation"),
            "explanation_it": it.get("explanation"),
        }

    def feedback(self, qid: str, attempt: dict, before: dict[int, dict]) -> dict:
        q = self.bank[qid]
        after = self.mastery()
        d = q["domain"]
        return {
            "correct": attempt["correct"],
            "your_answer": attempt["answer"],
            "correct_answer": q["correct"],
            **self.explain(qid),
            "citation": q.get("citation"),
            "lesson": self.lesson(qid),
            "domain": d,
            "domain_name": DOMAINS[d][0],
            "mastery_before": before[d]["score"],
            "mastery_after": after[d]["score"],
            "next_review_in": (self.qstate[qid].due_idx - self.counter) if self.qstate[qid].due_idx is not None else None,
        }

    def answer(self, qid: str, answer: list[str], mode: str = "practice") -> dict:
        validate_answer(self.bank, qid, answer)
        before = self.mastery()
        a = self.record(qid, answer, mode)
        return self.feedback(qid, a, before)

    # ------------------------------------------------------------ mock exams

    def build_mock(self, kind: str, rng: random.Random | None = None) -> dict:
        """kind=baseline: practice pool. kind=final: reserved pool first (unseen questions)."""
        if kind not in ("baseline", "final"):
            raise ValueError("kind must be baseline or final")
        rng = rng or random.Random()
        scenarios = sorted({q["scenario"] for q in self.bank.values()})
        chosen = rng.sample(scenarios, MOCK_SCENARIOS)
        used_in_mocks = set()
        for p in self.state_dir.glob("mock-*.json"):
            used_in_mocks.update(json.loads(p.read_text())["questions"])
        qids: list[str] = []
        for scn in chosen:
            pool = [qid for qid, q in self.bank.items() if q["scenario"] == scn]

            def rank(qid: str) -> tuple:
                fresh = qid not in self.qstate
                reserved = qid in self.reserved
                pref = (not reserved) if kind == "final" else reserved
                return (not fresh, qid in used_in_mocks, pref, rng.random())

            qids.extend(sorted(pool, key=rank)[:MOCK_PER_SCENARIO])
        mock = {
            "id": time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6],
            "kind": kind,
            "started": time.time(),
            "minutes": MOCK_MINUTES,
            "scenarios": chosen,
            "questions": qids,
            "answers": {},
            "flags": [],
            "submitted": None,
        }
        self._save_mock(mock)
        log.info("mock start id=%s kind=%s scenarios=%s", mock["id"], kind, chosen)
        return mock

    def mock_path(self, mock_id: str) -> Path:
        if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{6}", mock_id):
            raise ValueError("invalid mock id")
        return self.state_dir / f"mock-{mock_id}.json"

    def load_mock(self, mock_id: str) -> dict:
        p = self.mock_path(mock_id)
        if not p.exists():
            raise KeyError(mock_id)
        return json.loads(p.read_text())

    def _save_mock(self, mock: dict) -> None:
        self.mock_path(mock["id"]).write_text(json.dumps(mock, ensure_ascii=False, indent=1))

    def mock_public(self, mock: dict) -> dict:
        return {k: mock[k] for k in ("id", "kind", "started", "minutes", "scenarios", "answers", "flags", "submitted")} | {
            "questions": [self.public_question(qid) for qid in mock["questions"]],
            "server_now": time.time(),
        }

    def save_mock_progress(self, mock_id: str, answers: dict, flags: list) -> dict:
        mock = self.load_mock(mock_id)
        if mock["submitted"]:
            raise ValueError("mock already submitted")
        mock["answers"] = clean_mock_answers(self.bank, mock, answers)
        mock["flags"] = [f for f in flags if f in mock["questions"]]
        self._save_mock(mock)
        return {"saved": True}

    def submit_mock(self, mock_id: str, answers: dict, flags: list) -> dict:
        mock = self.load_mock(mock_id)
        if mock["submitted"]:
            return self.mock_result(mock)
        mock["answers"] = clean_mock_answers(self.bank, mock, answers)
        mock["flags"] = [f for f in flags if f in mock["questions"]]
        for qid in mock["questions"]:
            self.record(qid, mock["answers"].get(qid, []), "mock", mock["id"])
        results = [sorted(mock["answers"].get(qid, [])) == sorted(self.bank[qid]["correct"]) for qid in mock["questions"]]
        mock["submitted"] = time.time()
        mock["n"] = len(results)
        mock["ok"] = sum(results)
        mock["score"] = mock["ok"] / mock["n"]
        self._save_mock(mock)
        log.info("mock submit id=%s score=%.3f", mock_id, mock["score"])
        return self.mock_result(mock)

    def mock_result(self, mock: dict) -> dict:
        items, by_dom, by_scn = [], {}, {}
        for qid in mock["questions"]:
            q = self.bank[qid]
            ans = sorted(mock["answers"].get(qid, []))
            ok = ans == sorted(q["correct"])
            for key, bucket in ((q["domain"], by_dom), (q["scenario"], by_scn)):
                b = bucket.setdefault(key, [0, 0])
                b[0] += ok
                b[1] += 1
            items.append(self.public_question(qid) | {
                "your_answer": ans, "correct_answer": q["correct"], "ok": ok,
                **self.explain(qid), "citation": q.get("citation"), "lesson": self.lesson(qid),
                "flagged": qid in mock["flags"],
            })
        return {
            "id": mock["id"], "kind": mock["kind"], "score": mock.get("score"), "ok": mock.get("ok"), "n": mock.get("n"),
            "target": TARGET, "duration_min": round((mock["submitted"] - mock["started"]) / 60, 1),
            "by_domain": {str(d): {"name": DOMAINS[d][0], "ok": v[0], "n": v[1]} for d, v in sorted(by_dom.items())},
            "by_scenario": {k: {"ok": v[0], "n": v[1]} for k, v in by_scn.items()},
            "items": items,
        }


def validate_answer(bank: dict, qid: str, answer: list[str]) -> None:
    if qid not in bank:
        raise KeyError(qid)
    keys = {o["key"] for o in bank[qid]["options"]}
    if not answer or any(a not in keys for a in answer) or len(set(answer)) != len(answer):
        raise ValueError(f"answer must be distinct letters among {sorted(keys)}")


def clean_mock_answers(bank: dict, mock: dict, answers: dict) -> dict:
    out = {}
    for qid, ans in (answers or {}).items():
        if qid in mock["questions"] and isinstance(ans, list) and ans:
            keys = {o["key"] for o in bank[qid]["options"]}
            sel = sorted({a for a in ans if a in keys})
            if sel:
                out[qid] = sel
    return out


# ---------------------------------------------------------------- HTTP server

class Handler(BaseHTTPRequestHandler):
    trainer: Trainer
    STATIC = {"/": ("index.html", "text/html; charset=utf-8")}

    def log_message(self, fmt, *args):  # route http.server logs through logging
        log.debug("http %s", fmt % args)

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status: int = 200) -> None:
        self._send(status, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 1_000_000:
            raise ValueError("body too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def _dispatch(self, method: str) -> None:
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        t = self.trainer
        try:
            if method == "GET" and url.path in self.STATIC:
                name, ctype = self.STATIC[url.path]
                return self._send(200, (WEB_DIR / name).read_bytes(), ctype)
            if method == "GET" and url.path == "/api/stats":
                return self._json(t.stats())
            if method == "GET" and url.path == "/api/missed":
                return self._json(t.missed())
            if method == "GET" and url.path == "/api/next":
                d = qs.get("domain", [""])[0]
                return self._json(t.next_question(int(d) if d else None))
            if method == "GET" and url.path == "/api/question":
                return self._json(t.public_question(qs["id"][0]) | {"lesson": t.lesson(qs["id"][0])})
            if method == "POST" and url.path == "/api/answer":
                b = self._body()
                return self._json(t.answer(str(b["qid"]), list(b["answer"]), "practice"))
            if method == "POST" and url.path == "/api/mock/start":
                return self._json(t.mock_public(t.build_mock(self._body().get("kind", "baseline"))))
            m = re.fullmatch(r"/api/mock/([^/]+)(?:/(save|submit|result))?", url.path)
            if m:
                mock_id, action = m.group(1), m.group(2)
                if method == "GET" and action is None:
                    return self._json(t.mock_public(t.load_mock(mock_id)))
                if method == "GET" and action == "result":
                    return self._json(t.mock_result(t.load_mock(mock_id)))
                if method == "POST" and action in ("save", "submit"):
                    b = self._body()
                    fn = t.save_mock_progress if action == "save" else t.submit_mock
                    return self._json(fn(mock_id, b.get("answers", {}), b.get("flags", [])))
            return self._json({"error": "not found"}, 404)
        except KeyError as e:
            log.warning("not found path=%s key=%s", url.path, e)
            return self._json({"error": f"not found: {e}"}, 404)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            log.warning("bad request path=%s err=%s", url.path, e)
            return self._json({"error": str(e)}, 400)
        except Exception:
            log.exception("server error path=%s", url.path)
            return self._json({"error": "internal error"}, int(HTTPStatus.INTERNAL_SERVER_ERROR))

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def serve(port: int, state_dir: Path = STATE_DIR) -> None:
    Handler.trainer = Trainer.open(state_dir)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    log.info("serving on http://127.0.0.1:%d", port)
    print(f"CCAR-F trainer: http://127.0.0.1:{port}", flush=True)
    httpd.serve_forever()


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CCAR-F adaptive trainer")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--state-dir", type=Path, default=STATE_DIR, help="progress folder (default: trainer/state)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="web UI on 127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    n = sub.add_parser("next", help="next adaptive question (JSON, no answer)")
    n.add_argument("--domain", type=int, choices=sorted(DOMAINS))
    a = sub.add_parser("answer", help="record an answer and print feedback (JSON)")
    a.add_argument("qid")
    a.add_argument("letters", help="e.g. B or BE")
    sub.add_parser("stats", help="mastery and progress (JSON)")
    sub.add_parser("missed", help="questions answered wrong (JSON)")
    args = p.parse_args(argv)

    args.state_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(args.state_dir / "trainer.log", encoding="utf-8")],
    )
    if args.cmd == "serve":
        serve(args.port, args.state_dir)
        return 0
    t = Trainer.open(args.state_dir)
    if args.cmd == "next":
        out = t.next_question(args.domain)
    elif args.cmd == "answer":
        out = t.answer(args.qid, list(args.letters.upper()), "chat")
    elif args.cmd == "stats":
        out = t.stats()
    else:
        out = t.missed()
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
