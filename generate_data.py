# generate_data.py
# ─────────────────────────────────────────────────────────────────────────────
# Run this ONCE before starting the app to create training data.
# Like: running EF Core database seeder / HasData() in OnModelCreating()
#
# Usage: python generate_data.py
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
import os

def generate_student_data(n=600):
    """
    Generate realistic student performance data.
    Like: seeding your database with fake data using Bogus library in .NET.
    """
    np.random.seed(42)

    print(f"Generating {n} student records...")

    data = {
        # Academic inputs
        "attendance":    np.random.randint(20, 100, n).astype(float),
        "math_marks":    np.random.randint(15, 100, n).astype(float),
        "science_marks": np.random.randint(15, 100, n).astype(float),
        "english_marks": np.random.randint(15, 100, n).astype(float),

        # Study habits
        "hours_studied": np.round(np.random.uniform(0.0, 10.0, n), 1),
        "assignments":   np.random.randint(20, 100, n).astype(float),

        # Previous academic record
        "prev_gpa":      np.round(np.random.uniform(1.2, 4.0, n), 2),
    }

    df = pd.DataFrame(data)

    # ── Realistic Pass/Fail Rule ──────────────────────────────────────────
    # A student PASSES if ALL conditions below are satisfied.
    # This mirrors real-world academic thresholds.
    avg_marks = (df["math_marks"] + df["science_marks"] + df["english_marks"]) / 3

    df["result"] = (
        (df["attendance"]  >= 60) &   # Must attend at least 60% classes
        (avg_marks         >= 45) &   # Must average at least 45% marks
        (df["math_marks"]  >= 35) &   # Must pass math individually
        (df["hours_studied"] >= 1.5) & # Must study at least 1.5 hrs/day
        (df["assignments"] >= 40) &   # Must complete 40%+ assignments
        (df["prev_gpa"]    >= 1.8)    # Must have decent previous GPA
    ).astype(int)   # 1 = Pass, 0 = Fail

    pass_count = df["result"].sum()
    fail_count = n - pass_count
    print(f"  Pass: {pass_count} ({pass_count/n*100:.1f}%)")
    print(f"  Fail: {fail_count} ({fail_count/n*100:.1f}%)")

    df.to_csv("student_data.csv", index=False)
    print(f"\nSaved to student_data.csv — ready for ML training!")
    return df


if __name__ == "__main__":
    generate_student_data(600)
