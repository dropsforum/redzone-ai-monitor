import json
import unittest
from pathlib import Path

from ai_motion_app.breach_state import BreachStateMachine, TrackObservation
from ai_motion_app.breach_recorder import BreachRecorder
from ai_motion_app.zone_entry import classify_foot_point


def observation(
    track_id: int = 1,
    *,
    inside: bool = False,
    near: bool = False,
    confidence: float = 0.8,
) -> TrackObservation:
    return TrackObservation(track_id, inside, near, confidence)


class BreachStateMachineTests(unittest.TestCase):
    def test_confirms_entry_after_300ms_and_exits_after_750ms_grace(self):
        machine = BreachStateMachine(
            entry_confirm_ms=300,
            exit_grace_ms=750,
            tracker_max_gap_ms=750,
        )

        pending = machine.update([observation(inside=True, near=True)], 10.0)
        self.assertEqual("yellow", pending.traffic)
        self.assertFalse(pending.is_breach)

        still_pending = machine.update([observation(inside=True, near=True)], 10.299)
        self.assertEqual("yellow", still_pending.traffic)

        confirmed = machine.update([observation(inside=True, near=True)], 10.300)
        self.assertEqual("red", confirmed.traffic)
        self.assertTrue(confirmed.entered_breach)
        self.assertEqual((1,), confirmed.active_track_ids)
        self.assertEqual(10.0, confirmed.started_events[0].start)

        grace = machine.update([], 11.049)
        self.assertEqual("red", grace.traffic)
        self.assertFalse(grace.exited_breach)

        exited = machine.update([], 11.051)
        self.assertEqual("green", exited.traffic)
        self.assertTrue(exited.exited_breach)
        self.assertAlmostEqual(11.05, exited.ended_events[0].end)

    def test_near_and_pending_people_are_yellow(self):
        machine = BreachStateMachine()
        near = machine.update([observation(inside=False, near=True)], 1.0)
        self.assertEqual("yellow", near.traffic)

        pending = machine.update([observation(inside=True, near=True)], 2.0)
        self.assertEqual("yellow", pending.traffic)
        self.assertEqual((1,), pending.pending_track_ids)

    def test_overall_breach_transition_occurs_only_once_for_multiple_people(self):
        machine = BreachStateMachine(entry_confirm_ms=0)
        first = machine.update([
            observation(1, inside=True, near=True),
            observation(2, inside=True, near=True),
        ], 5.0)
        self.assertTrue(first.entered_breach)
        self.assertEqual((1, 2), first.active_track_ids)

        stable = machine.update([
            observation(1, inside=True, near=True),
            observation(2, inside=True, near=True),
        ], 5.1)
        self.assertFalse(stable.entered_breach)
        self.assertTrue(stable.is_breach)

    def test_reset_ends_active_person_events(self):
        machine = BreachStateMachine(entry_confirm_ms=0)
        machine.update([observation(7, inside=True, near=True)], 20.0)
        reset = machine.reset(21.0)
        self.assertEqual("green", reset.traffic)
        self.assertTrue(reset.exited_breach)
        self.assertEqual(7, reset.ended_events[0].track_id)
        self.assertEqual(21.0, reset.ended_events[0].end)

    def test_matches_shared_cross_platform_state_and_reporting_fixture(self):
        fixture_path = Path(__file__).parents[1] / "fixtures" / "zone_sequences.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        frame = fixture["frame"]
        config = fixture["config"]
        zone = [(point["x"], point["y"]) for point in fixture["zone"]]

        for sequence in fixture["sequences"]:
            with self.subTest(sequence=sequence["name"]):
                machine = BreachStateMachine(
                    entry_confirm_ms=config["entryConfirmMs"],
                    exit_grace_ms=config["exitGraceMs"],
                    tracker_max_gap_ms=config["trackerMaxGapMs"],
                )
                recorder = BreachRecorder(Path(":memory:"))
                recorder.start(sequence["steps"][0]["atMs"] / 1000.0)
                person_events = []

                for step in sequence["steps"]:
                    now = step["atMs"] / 1000.0
                    observations = []
                    confidence_by_track = {}
                    for detection in step["detections"]:
                        x1, y1, x2, y2 = detection["box"]
                        contact = classify_foot_point(
                            x1,
                            x2,
                            y2,
                            zone,
                            frame["width"],
                            frame["height"],
                            config["warningBuffer"],
                        )
                        track_id = detection["trackId"]
                        confidence = detection["confidence"]
                        confidence_by_track[track_id] = confidence
                        observations.append(TrackObservation(
                            track_id=track_id,
                            inside=contact.inside,
                            near=contact.near,
                            confidence=confidence,
                        ))

                    decision = machine.update(observations, now)
                    self.assertEqual(
                        step["expectedState"],
                        decision.traffic,
                        f"{sequence['name']} at {step['atMs']}ms",
                    )
                    for event in decision.started_events:
                        recorder.start_person_breach(
                            event.track_id,
                            event.start,
                            event.max_confidence,
                        )
                    for track_id in decision.active_track_ids:
                        if track_id in confidence_by_track:
                            recorder.update_person_confidence(
                                track_id,
                                confidence_by_track[track_id],
                            )
                    for event in decision.ended_events:
                        recorder.end_person_breach(
                            event.track_id,
                            event.end,
                            event.max_confidence,
                        )
                        person_events.append(event)

                    state_time = (
                        max(event.end for event in decision.ended_events)
                        if decision.exited_breach and decision.ended_events
                        else now
                    )
                    recorder.update(decision.is_breach, state_time)

                final_time = sequence["steps"][-1]["atMs"] / 1000.0
                recorder.stop(final_time)
                actual_people = [
                    {
                        "trackId": event.track_id,
                        "startMs": round(event.start * 1000),
                        "endMs": round(event.end * 1000),
                        "maxConfidence": event.max_confidence,
                    }
                    for event in recorder.person_events(final_time)
                ]
                self.assertEqual(sequence["expectedPersonEvents"], actual_people)

                actual_segments = [
                    {
                        "state": segment.state,
                        "startMs": round(segment.start * 1000),
                        "endMs": round(segment.end * 1000),
                    }
                    for segment in recorder.segments(final_time)
                ]
                self.assertEqual(sequence["expectedSegments"], actual_segments)
                recorder.store.close()


if __name__ == "__main__":
    unittest.main()
