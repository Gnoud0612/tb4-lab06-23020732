import math
from types import SimpleNamespace
import pytest
from tb4_gesture.control import BehaviorController, Pose
from tb4_gesture.filtering import GestureFilter, WaveDetector


@pytest.mark.parametrize("label", ["Wave", "Pointing_Up", "Victory"])
def test_selection_does_not_move_without_confirmation(label):
    c = BehaviorController()
    p = Pose(0, 0, 0)
    for i in range(30):
        c.receive(label, i * 0.1, p)
        assert c.step(i * 0.1, p) == (0.0, 0.0)
    assert c.state == "SELECTED"


def confirmed(label="Pointing_Up"):
    c = BehaviorController()
    p = Pose(0, 0, 0)
    c.receive(label, 0, p)
    c.receive("Thumb_Up", 0.1, p)
    return c, p


def test_confirmation_without_selection_is_ignored():
    c = BehaviorController()
    c.receive("Thumb_Up", 0, Pose(0, 0, 0))
    assert c.step(0.1, Pose(0, 0, 0)) == (0.0, 0.0)
    assert c.state == "IDLE"


@pytest.mark.parametrize(
    "label,state", [("Open_Palm", "STOPPED"), ("Closed_Fist", "IDLE")]
)
def test_stop_and_cancel_before_next_controller_tick(label, state):
    c, p = confirmed()
    assert c.step(0.2, p)[0] > 0
    c.receive(label, 0.21, p)
    assert c.command == (0.0, 0.0) and c.state == state and c.selected is None


@pytest.mark.parametrize("loss", ["No_Hand", "Unknown", "untrusted_label"])
def test_hand_loss_or_unrecognized_input_cannot_keep_moving(loss):
    c, p = confirmed()
    c.receive(loss, 0.2, p)
    assert c.step(0.8, p) == (0.0, 0.0) and c.state == "STOPPED"


def test_publisher_death_watchdog():
    c, p = confirmed()
    assert c.step(0.2, p)[0] > 0
    assert c.step(0.751, p) == (0.0, 0.0) and c.state == "STOPPED"


@pytest.mark.parametrize(
    "kwargs", [{"odom_fresh": False}, {"sensors_ok": False}, {"obstruction": True}]
)
def test_sensor_fail_closed(kwargs):
    c, p = confirmed()
    assert c.step(0.2, p, **kwargs) == (0.0, 0.0)
    assert c.state == "FAULT"


def test_nonfinite_pose_stops():
    c, p = confirmed()
    assert c.step(0.2, Pose(float("nan"), 0, 0)) == (0.0, 0.0)
    assert c.state == "FAULT"


def test_expired_selection_cannot_confirm():
    c = BehaviorController()
    c.receive("Victory", 0, Pose(0, 0, 0))
    c.receive("Thumb_Up", 16, Pose(0, 0, 0))
    assert c.state == "IDLE"


@pytest.mark.parametrize(
    "gesture,behavior,phases",
    [
        ("Wave", "greet", 4),
        ("Pointing_Up", "back_and_forth", 8),
        ("Victory", "circle", 1),
    ],
)
def test_full_behavior_feedback_and_held_thumb_does_not_retrigger(
    gesture, behavior, phases
):
    c, p = confirmed(gesture)
    now = 0.1
    dt = 0.02
    for _ in range(12000):
        now += dt
        c.receive("Thumb_Up", now, p)
        v, w = c.step(now, p)
        p = Pose(
            p.x + v * math.cos(p.yaw) * dt,
            p.y + v * math.sin(p.yaw) * dt,
            p.yaw + w * dt,
        )
        if c.state == "COMPLETED":
            break
    assert c.state == "COMPLETED"
    assert len([e for e in c.events if e["event"] == "phase_completed"]) == phases
    assert c.completed_actions == [behavior]
    for _ in range(50):
        now += 0.1
        c.receive("Thumb_Up", now, p)
        assert c.step(now, p) == (0.0, 0.0)
    assert c.completed_actions == [behavior]
    if gesture == "Pointing_Up":
        assert math.hypot(p.x, p.y) < 0.04
    if gesture == "Victory":
        assert math.hypot(p.x, p.y) < 0.06


def test_debounce_rejects_jitter_and_accepts_held_class():
    f = GestureFilter()
    for i in range(20):
        assert f.update("Victory" if i % 2 else "Thumb_Up", 0.95, i * 0.05) == "Unknown"
    f = GestureFilter()
    assert f.update("Victory", 0.99, 0) == "Unknown"
    assert f.update("Victory", 0.99, 0.1) == "Unknown"
    assert f.update("Victory", 0.99, 0.34) == "Victory"
    assert f.update("Thumb_Up", 0.4, 0.5) == "Unknown"


def landmarks(x):
    return [
        SimpleNamespace(x=x + (0.05 if i == 5 else -0.05 if i == 17 else 0), y=0.5)
        for i in range(21)
    ]


def test_stationary_palm_and_small_jitter_are_not_wave():
    d = WaveDetector()
    for i in range(40):
        assert not d.update(
            "Open_Palm", 0.99, landmarks(0.5 + 0.003 * math.sin(i)), i * 0.05
        )


def test_real_motion_pattern_produces_wave_with_ai_palm():
    d = WaveDetector()
    found = False
    for i in range(35):
        found |= d.update(
            "Open_Palm", 0.95, landmarks(0.5 + 0.15 * math.sin(i * 0.4)), i * 0.05
        )
    assert found


def test_wrong_ai_class_does_not_wave_even_if_hand_moves():
    d = WaveDetector()
    for i in range(40):
        assert not d.update(
            "Closed_Fist", 0.99, landmarks(0.5 + 0.15 * math.sin(i)), i * 0.05
        )


def test_stalled_robot_stops_even_with_held_valid_gesture():
    c, p = confirmed()
    for i in range(1, 70):
        now = 0.1 + i * 0.1
        c.receive("Thumb_Up", now, p)
        c.step(now, p)
    assert c.state == "FAULT" and c.command == (0.0, 0.0)


def test_wave_is_detectable_at_measured_low_camera_rate():
    d = WaveDetector()
    found = False
    for i in range(18):
        found |= d.update(
            "Open_Palm", 0.96, landmarks(0.5 + 0.15 * math.sin(i * 0.9)), i * 0.30
        )
    assert found


@pytest.mark.parametrize("label,score", [("Open_Palm", 0.60), ("Closed_Fist", 0.66)])
def test_stop_cancel_have_priority_at_conservative_threshold(label, score):
    assert GestureFilter().update(label, score, 0) == label


def test_open_palm_during_wave_selection_never_moves_without_confirmation():
    c = BehaviorController()
    p = Pose(0, 0, 0)
    c.receive("Wave", 0, p)
    c.receive("Open_Palm", 0.1, p)
    assert c.state == "SELECTED" and c.step(0.2, p) == (0.0, 0.0)
    c.receive("Thumb_Up", 0.3, p)
    assert c.state == "RUNNING"


@pytest.mark.parametrize("dt", [0.3, 0.4, 0.5])
def test_wave_at_two_to_three_fps_with_realistic_palm_scores(dt):
    d = WaveDetector()
    positions = [0.35, 0.50, 0.65, 0.50, 0.35, 0.50, 0.65]
    assert any(
        d.update("Open_Palm", 0.62, landmarks(x), i * dt)
        for i, x in enumerate(positions)
    )


def test_wave_survives_one_uncertain_ai_frame_without_counting_it():
    d = WaveDetector()
    found = False
    for i, x in enumerate([0.35, 0.50, 0.65, 0.50, 0.35, 0.50, 0.65]):
        found |= d.update(
            "None" if i == 3 else "Open_Palm",
            0.8 if i == 3 else 0.62,
            landmarks(x),
            i * 0.3,
        )
    assert found


def test_wave_long_gap_cannot_join_unrelated_movements():
    d = WaveDetector()
    for t, x in [(0, 0.35), (0.3, 0.65), (0.6, 0.35), (2.0, 0.65), (2.3, 0.35)]:
        assert not d.update("Open_Palm", 0.65, landmarks(x), t)


def test_weak_palm_or_one_way_motion_cannot_be_wave():
    for score in (0.4, 0.65):
        d = WaveDetector()
        for i in range(20):
            assert not d.update("Open_Palm", score, landmarks(0.25 + i * 0.02), i * 0.2)


def test_closed_fist_clears_partial_wave():
    d = WaveDetector()
    for i, x in enumerate([0.35, 0.65, 0.35]):
        d.update("Open_Palm", 0.65, landmarks(x), i * 0.3)
    assert not d.update("Closed_Fist", 0.9, landmarks(0.5), 0.7)
    assert not d.history


def test_real_recorded_thumb_score_dips_do_not_interrupt_confirmed_behavior():
    # Actual score sequence observed on 2026-10-27; timestamps sampled at ~2.8 fps.
    f = GestureFilter()
    c = BehaviorController()
    p = Pose(0, 0, 0)
    c.receive("Pointing_Up", 0, p)
    scores = [0.71666, 0.74886, 0.71088, 0.57811, 0.63388, 0.73298, 0.76117, 0.70890]
    for i, score in enumerate(scores):
        now = 0.1 + i * 0.35
        label = f.update("Thumb_Up", score, now)
        c.receive(label, now, p)
        c.step(now, p)
        if i >= 2:
            assert label == "Thumb_Up" and c.state == "RUNNING"


def test_weak_thumb_alone_can_never_confirm():
    f = GestureFilter()
    for i in range(30):
        assert f.update("Thumb_Up", 0.62, i * 0.35) == "Unknown"


@pytest.mark.parametrize("loss", ["No_Hand", "Unknown", "Open_Palm", "Closed_Fist"])
def test_thumb_hysteresis_is_cleared_by_hand_loss_or_stop(loss):
    f = GestureFilter()
    for i in range(3):
        f.update("Thumb_Up", 0.9, i * 0.35)
    assert f.update("Thumb_Up", 0.6, 0.9) == "Thumb_Up"
    f.update(loss, 0.95, 1.0)
    assert f.update("Thumb_Up", 0.6, 1.2) == "Unknown"


def test_thumb_hysteresis_cannot_bridge_long_frame_gap():
    f = GestureFilter()
    for i in range(3):
        f.update("Thumb_Up", 0.9, i * 0.35)
    assert f.update("Thumb_Up", 0.6, 1.5) == "Unknown"


def test_thumb_hysteresis_rejects_low_confidence_and_nonfinite():
    for weak in [0.54, float("nan")]:
        f = GestureFilter()
        for i in range(3):
            f.update("Thumb_Up", 0.9, i * 0.35)
        assert f.update("Thumb_Up", weak, 0.9) == "Unknown"
