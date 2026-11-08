"""
SetuSentry Setup and Environment Initializer
1. Creates required directories
2. Initializes SQLite database and seeds 8 Indian bridge assets & inspection history
3. Generates high-resolution sample cracked and sound concrete images for instant testing
4. Validates deep learning & computer vision runtime (PyTorch, MobileNetV2, OpenCV)
5. Executes automated unit tests to verify system integrity
"""

import os
import sys
import unittest

# Ensure current directory is on PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def main():
    print("=" * 70)
    print("       SETUSENTRY: AI-ASSISTED BRIDGE INSPECTION SYSTEM SETUP       ")
    print("=" * 70)

    # 1. Directory creation
    print("\n[1/5] Creating application directories...")
    uploads_dir = os.path.join(BASE_DIR, "uploads")
    samples_dir = os.path.join(uploads_dir, "samples")
    os.makedirs(samples_dir, exist_ok=True)
    print(f"  [OK] Uploads directory: {uploads_dir}")
    print(f"  [OK] Sample images directory: {samples_dir}")

    # 2. Database initialization & seeding
    print("\n[2/5] Initializing SQLite database and seeding sample records...")
    from database import init_db, get_all_bridges, get_all_inspections
    from data.seed_data import seed_database

    init_db()
    b_count, i_count = seed_database(force=True)
    all_b = get_all_bridges()
    all_i = get_all_inspections()
    print(f"  [OK] Database initialized successfully.")
    print(f"  [OK] Loaded {len(all_b)} bridge assets and {len(all_i)} inspection logs into setusentry.db.")

    # 3. Generate sample images
    print("\n[3/5] Generating synthetic test images for visual inspection demo...")
    from utils.image_utils import generate_synthetic_concrete_image

    sample_cracked_path = os.path.join(samples_dir, "sample_cracked_pier.jpg")
    sample_sound_path = os.path.join(samples_dir, "sample_sound_deck.jpg")

    cracked_img = generate_synthetic_concrete_image(is_cracked=True, width=640, height=480)
    cracked_img.save(sample_cracked_path, quality=95)

    sound_img = generate_synthetic_concrete_image(is_cracked=False, width=640, height=480)
    sound_img.save(sample_sound_path, quality=95)

    print(f"  [OK] Generated cracked concrete sample: {sample_cracked_path}")
    print(f"  [OK] Generated sound concrete sample: {sample_sound_path}")

    # 4. Neural Network and Vision pipeline check
    print("\n[4/5] Verifying PyTorch MobileNetV2 and OpenCV pipeline...")
    try:
        from model.demo_inference import run_visual_inspection
        demo_res = run_visual_inspection(sample_cracked_path)
        print(f"  [OK] MobileNetV2 + OpenCV inspection test passed!")
        print(f"       Classification: {demo_res['classification']} | Confidence: {demo_res['confidence_pct']}% | Severity: {demo_res['severity']}")
    except Exception as e:
        print(f"  [ERROR] Vision pipeline check failed: {e}")
        sys.exit(1)

    # 5. Execute automated unit test suite
    print("\n[5/5] Executing automated test suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(BASE_DIR, "tests"))
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    if not test_result.wasSuccessful():
        print("\n[ERROR] One or more unit tests failed. Please review errors above.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("SETUSENTRY INITIALIZATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nTo launch the SetuSentry Streamlit web dashboard:")
    print(f"  cd {BASE_DIR}")
    print("  streamlit run app.py\n")


if __name__ == "__main__":
    main()
