"""Workout prescriptions for the six-week Hundred Pushups program.

The tables intentionally use a small, editable data structure so the program can
be tuned without changing the bot or database code.  ``MAX`` means the athlete
performs as many clean repetitions as possible, while respecting the minimum.
"""

from __future__ import annotations

from typing import Final, TypedDict


class SetPrescription(TypedDict):
    reps: list[int | str]
    rest_seconds: int


# This is a representative six-week progression based on the standard five-set
# Hundred Pushups cadence.  The last set is always an effort set with a floor.
# Level 1 is for a baseline below 5, level 2 for 6-10, and level 3 for 11-20.
WEEK_DATA: Final[dict[int, dict[int, dict[int, SetPrescription]]]] = {
    1: {
        1: {
            1: {"reps": [2, 3, 2, 2, "max (at least 3)"], "rest_seconds": 60},
            2: {"reps": [6, 6, 4, 4, "max (at least 5)"], "rest_seconds": 60},
            3: {"reps": [10, 12, 7, 7, "max (at least 9)"], "rest_seconds": 60},
        },
        2: {
            1: {"reps": [3, 4, 3, 3, "max (at least 4)"], "rest_seconds": 60},
            2: {"reps": [7, 8, 5, 5, "max (at least 7)"], "rest_seconds": 60},
            3: {"reps": [10, 12, 8, 8, "max (at least 10)"], "rest_seconds": 60},
        },
        3: {
            1: {"reps": [4, 5, 4, 4, "max (at least 5)"], "rest_seconds": 60},
            2: {"reps": [8, 10, 6, 6, "max (at least 8)"], "rest_seconds": 60},
            3: {"reps": [12, 17, 9, 9, "max (at least 12)"], "rest_seconds": 60},
        },
    },
    2: {
        1: {
            1: {"reps": [4, 5, 4, 4, "max (at least 6)"], "rest_seconds": 60},
            2: {"reps": [9, 11, 8, 8, "max (at least 10)"], "rest_seconds": 60},
            3: {"reps": [14, 16, 12, 12, "max (at least 15)"], "rest_seconds": 60},
        },
        2: {
            1: {"reps": [5, 6, 4, 4, "max (at least 7)"], "rest_seconds": 60},
            2: {"reps": [10, 12, 9, 9, "max (at least 12)"], "rest_seconds": 60},
            3: {"reps": [16, 17, 14, 14, "max (at least 17)"], "rest_seconds": 60},
        },
        3: {
            1: {"reps": [5, 7, 5, 5, "max (at least 8)"], "rest_seconds": 60},
            2: {"reps": [12, 14, 10, 10, "max (at least 14)"], "rest_seconds": 60},
            3: {"reps": [18, 20, 16, 16, "max (at least 20)"], "rest_seconds": 60},
        },
    },
    3: {
        1: {
            1: {"reps": [6, 7, 5, 5, "max (at least 9)"], "rest_seconds": 60},
            2: {"reps": [12, 17, 13, 13, "max (at least 17)"], "rest_seconds": 90},
            3: {"reps": [20, 25, 15, 15, "max (at least 25)"], "rest_seconds": 90},
        },
        2: {
            1: {"reps": [7, 8, 6, 6, "max (at least 10)"], "rest_seconds": 60},
            2: {"reps": [14, 19, 14, 14, "max (at least 19)"], "rest_seconds": 90},
            3: {"reps": [23, 29, 17, 17, "max (at least 29)"], "rest_seconds": 90},
        },
        3: {
            1: {"reps": [8, 10, 7, 7, "max (at least 12)"], "rest_seconds": 60},
            2: {"reps": [16, 22, 16, 16, "max (at least 22)"], "rest_seconds": 90},
            3: {"reps": [26, 33, 19, 19, "max (at least 33)"], "rest_seconds": 90},
        },
    },
    4: {
        1: {
            1: {"reps": [8, 10, 8, 8, "max (at least 12)"], "rest_seconds": 60},
            2: {"reps": [15, 20, 15, 15, "max (at least 20)"], "rest_seconds": 90},
            3: {"reps": [28, 35, 20, 20, "max (at least 35)"], "rest_seconds": 90},
        },
        2: {
            1: {"reps": [9, 11, 9, 9, "max (at least 13)"], "rest_seconds": 60},
            2: {"reps": [17, 22, 16, 16, "max (at least 22)"], "rest_seconds": 90},
            3: {"reps": [30, 38, 22, 22, "max (at least 38)"], "rest_seconds": 90},
        },
        3: {
            1: {"reps": [10, 12, 10, 10, "max (at least 15)"], "rest_seconds": 60},
            2: {"reps": [19, 25, 18, 18, "max (at least 25)"], "rest_seconds": 90},
            3: {"reps": [32, 42, 24, 24, "max (at least 42)"], "rest_seconds": 90},
        },
    },
    5: {
        1: {
            1: {"reps": [10, 12, 10, 10, "max (at least 15)"], "rest_seconds": 60},
            2: {"reps": [20, 25, 20, 20, "max (at least 25)"], "rest_seconds": 90},
            3: {"reps": [35, 45, 25, 25, "max (at least 45)"], "rest_seconds": 120},
        },
        2: {
            1: {"reps": [12, 14, 12, 12, "max (at least 17)"], "rest_seconds": 60},
            2: {"reps": [22, 28, 22, 22, "max (at least 28)"], "rest_seconds": 90},
            3: {"reps": [38, 50, 28, 28, "max (at least 50)"], "rest_seconds": 120},
        },
        3: {
            1: {"reps": [14, 16, 14, 14, "max (at least 20)"], "rest_seconds": 60},
            2: {"reps": [25, 32, 25, 25, "max (at least 32)"], "rest_seconds": 90},
            3: {"reps": [42, 55, 30, 30, "max (at least 55)"], "rest_seconds": 120},
        },
    },
    6: {
        1: {
            1: {"reps": [15, 17, 15, 15, "max (at least 22)"], "rest_seconds": 60},
            2: {"reps": [25, 30, 25, 25, "max (at least 30)"], "rest_seconds": 90},
            3: {"reps": [45, 55, 35, 35, "max (at least 55)"], "rest_seconds": 120},
        },
        2: {
            1: {"reps": [17, 19, 17, 17, "max (at least 25)"], "rest_seconds": 60},
            2: {"reps": [27, 35, 27, 27, "max (at least 35)"], "rest_seconds": 90},
            3: {"reps": [50, 60, 40, 40, "max (at least 60)"], "rest_seconds": 120},
        },
        3: {
            1: {"reps": [20, 22, 20, 20, "max (at least 28)"], "rest_seconds": 60},
            2: {"reps": [30, 40, 30, 30, "max (at least 40)"], "rest_seconds": 90},
            3: {"reps": [55, 65, 45, 45, "max (at least 65)"], "rest_seconds": 120},
        },
    },
}


def get_workout(week: int, day: int, level: int) -> SetPrescription:
    """Return one prescription and fail clearly for invalid state."""

    try:
        return WEEK_DATA[week][day][level]
    except KeyError as exc:
        raise ValueError(f"No workout exists for week={week}, day={day}, level={level}") from exc

