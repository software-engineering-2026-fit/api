"""Seed a starter exercise catalog.

Revision ID: 20261106_0009
Revises: 20261106_0008
"""

from typing import Sequence, Union
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0009"
down_revision: Union[str, None] = "20261106_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXERCISES = (
    ("Barbell Bench Press", "Chest", "Barbell"),
    ("Dumbbell Bench Press", "Chest", "Dumbbells"),
    ("Incline Barbell Bench Press", "Chest", "Barbell and incline bench"),
    ("Incline Dumbbell Bench Press", "Chest", "Dumbbells and incline bench"),
    ("Decline Barbell Bench Press", "Chest", "Barbell and decline bench"),
    ("Dumbbell Chest Fly", "Chest", "Dumbbells and bench"),
    ("Incline Dumbbell Fly", "Chest", "Dumbbells and incline bench"),
    ("Cable Chest Fly", "Chest", "Cable machine"),
    ("Low-to-High Cable Fly", "Chest", "Cable machine"),
    ("High-to-Low Cable Fly", "Chest", "Cable machine"),
    ("Machine Chest Press", "Chest", "Chest press machine"),
    ("Pec Deck", "Chest", "Pec deck machine"),
    ("Push-Up", "Chest", "Bodyweight"),
    ("Weighted Push-Up", "Chest", "Bodyweight and weight plate"),
    ("Chest Dip", "Chest", "Dip bars"),
    ("Barbell Bent-Over Row", "Back", "Barbell"),
    ("Pendlay Row", "Back", "Barbell"),
    ("One-Arm Dumbbell Row", "Back", "Dumbbell and bench"),
    ("Chest-Supported Row", "Back", "Dumbbells and incline bench"),
    ("Seated Cable Row", "Back", "Cable machine"),
    ("Wide-Grip Seated Cable Row", "Back", "Cable machine"),
    ("Lat Pulldown", "Back", "Cable machine"),
    ("Wide-Grip Lat Pulldown", "Back", "Cable machine"),
    ("Close-Grip Lat Pulldown", "Back", "Cable machine"),
    ("Pull-Up", "Back", "Pull-up bar"),
    ("Chin-Up", "Back", "Pull-up bar"),
    ("Assisted Pull-Up", "Back", "Assisted pull-up machine"),
    ("Inverted Row", "Back", "Barbell or suspension trainer"),
    ("T-Bar Row", "Back", "T-bar row machine"),
    ("Straight-Arm Pulldown", "Back", "Cable machine"),
    ("Dumbbell Pullover", "Back", "Dumbbell and bench"),
    ("Back Extension", "Back", "Back extension bench"),
    ("Standing Barbell Overhead Press", "Shoulders", "Barbell"),
    ("Seated Dumbbell Shoulder Press", "Shoulders", "Dumbbells and bench"),
    ("Arnold Press", "Shoulders", "Dumbbells"),
    ("Dumbbell Lateral Raise", "Shoulders", "Dumbbells"),
    ("Cable Lateral Raise", "Shoulders", "Cable machine"),
    ("Machine Lateral Raise", "Shoulders", "Lateral raise machine"),
    ("Dumbbell Front Raise", "Shoulders", "Dumbbells"),
    ("Reverse Dumbbell Fly", "Shoulders", "Dumbbells and bench"),
    ("Reverse Pec Deck", "Shoulders", "Pec deck machine"),
    ("Barbell Shrug", "Shoulders", "Barbell"),
    ("Dumbbell Shrug", "Shoulders", "Dumbbells"),
    ("Landmine Press", "Shoulders", "Barbell and landmine attachment"),
    ("Barbell Curl", "Biceps", "Barbell"),
    ("EZ-Bar Curl", "Biceps", "EZ curl bar"),
    ("Alternating Dumbbell Curl", "Biceps", "Dumbbells"),
    ("Hammer Curl", "Biceps", "Dumbbells"),
    ("Preacher Curl", "Biceps", "Preacher bench and EZ curl bar"),
    ("Concentration Curl", "Biceps", "Dumbbell and bench"),
    ("Cable Biceps Curl", "Biceps", "Cable machine"),
    ("Incline Dumbbell Curl", "Biceps", "Dumbbells and incline bench"),
    ("Reverse Curl", "Biceps", "EZ curl bar"),
    ("Spider Curl", "Biceps", "Dumbbells and incline bench"),
    ("Close-Grip Bench Press", "Triceps", "Barbell and bench"),
    ("EZ-Bar Skull Crusher", "Triceps", "EZ curl bar and bench"),
    ("Overhead Cable Triceps Extension", "Triceps", "Cable machine"),
    ("Dumbbell Overhead Triceps Extension", "Triceps", "Dumbbell"),
    ("Rope Triceps Pushdown", "Triceps", "Cable machine and rope attachment"),
    ("Straight-Bar Triceps Pushdown", "Triceps", "Cable machine and straight bar"),
    ("Cable Triceps Kickback", "Triceps", "Cable machine"),
    ("Bench Dip", "Triceps", "Bench"),
    ("Diamond Push-Up", "Triceps", "Bodyweight"),
    ("Machine Triceps Dip", "Triceps", "Triceps dip machine"),
    ("Barbell Back Squat", "Legs", "Barbell and squat rack"),
    ("Front Squat", "Legs", "Barbell and squat rack"),
    ("Goblet Squat", "Legs", "Dumbbell or kettlebell"),
    ("Leg Press", "Legs", "Leg press machine"),
    ("Hack Squat", "Legs", "Hack squat machine"),
    ("Bulgarian Split Squat", "Legs", "Dumbbells and bench"),
    ("Walking Lunge", "Legs", "Bodyweight or dumbbells"),
    ("Reverse Lunge", "Legs", "Bodyweight or dumbbells"),
    ("Step-Up", "Legs", "Box or bench"),
    ("Romanian Deadlift", "Legs", "Barbell or dumbbells"),
    ("Conventional Deadlift", "Legs", "Barbell"),
    ("Sumo Deadlift", "Legs", "Barbell"),
    ("Barbell Hip Thrust", "Legs", "Barbell and bench"),
    ("Glute Bridge", "Legs", "Bodyweight or barbell"),
    ("Leg Extension", "Legs", "Leg extension machine"),
    ("Seated Leg Curl", "Legs", "Seated leg curl machine"),
    ("Lying Leg Curl", "Legs", "Lying leg curl machine"),
    ("Standing Calf Raise", "Legs", "Calf raise machine"),
    ("Seated Calf Raise", "Legs", "Seated calf raise machine"),
    ("Hip Abduction", "Legs", "Hip abduction machine"),
    ("Plank", "Core", "Bodyweight"),
    ("Side Plank", "Core", "Bodyweight"),
    ("Hanging Knee Raise", "Core", "Pull-up bar"),
    ("Hanging Leg Raise", "Core", "Pull-up bar"),
    ("Cable Crunch", "Core", "Cable machine and rope attachment"),
    ("Ab Wheel Rollout", "Core", "Ab wheel"),
    ("Russian Twist", "Core", "Bodyweight or medicine ball"),
    ("Bicycle Crunch", "Core", "Bodyweight"),
    ("Dead Bug", "Core", "Bodyweight"),
    ("Pallof Press", "Core", "Cable machine or resistance band"),
    ("Kettlebell Swing", "Conditioning", "Kettlebell"),
    ("Burpee", "Conditioning", "Bodyweight"),
    ("Box Jump", "Conditioning", "Plyometric box"),
    ("Farmer's Carry", "Conditioning", "Dumbbells or kettlebells"),
    ("Sled Push", "Conditioning", "Weight sled"),
    ("Jump Rope", "Conditioning", "Jump rope"),
)


def _exercise_table() -> sa.TableClause:
    return sa.table(
        "exercises",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("muscle_group", sa.String()),
        sa.column("equipment", sa.String()),
    )


def _exercise_id(name: str):
    return uuid5(NAMESPACE_URL, f"se-2026-exercise:{name.casefold()}")


def upgrade() -> None:
    bind = op.get_bind()
    exercises = _exercise_table()
    existing_names = {
        name.casefold()
        for name in bind.execute(sa.select(exercises.c.name)).scalars()
    }
    rows = []
    for name, muscle_group, equipment in EXERCISES:
        normalized_name = name.casefold()
        if normalized_name in existing_names:
            continue
        rows.append(
            {
                "id": _exercise_id(name),
                "name": name,
                "description": None,
                "muscle_group": muscle_group,
                "equipment": equipment,
            }
        )
        existing_names.add(normalized_name)

    if rows:
        bind.execute(exercises.insert(), rows)


def downgrade() -> None:
    exercises = _exercise_table()
    seeded_ids = [_exercise_id(name) for name, _, _ in EXERCISES]
    op.get_bind().execute(
        exercises.delete().where(exercises.c.id.in_(seeded_ids))
    )