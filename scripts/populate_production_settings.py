#!/usr/bin/env python3
"""
Populate Production Settings Script

This script populates production database with:
- Return survey questions
- GESI Status options
- Business Category options
- Main Reason for Signing Up options

Run this after deployment to initialize settings:
    python scripts/populate_production_settings.py

Or via docker:
    docker exec battery-hub-api python scripts/populate_production_settings.py
"""

import sys
import os

# Add parent directory to path to import models and database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from database import get_db
from models import SolarHub, ReturnSurveyQuestion, CustomerFieldOption, ReturnSurveyQuestionOption


def populate_return_surveys(db: Session):
    """Populate return survey questions for all hubs"""
    print("\n📋 Populating Return Survey Questions...")

    # Get all hubs
    hubs = db.query(SolarHub).all()

    if not hubs:
        print("⚠️  No hubs found. Please create hubs first.")
        return

    # Define survey questions
    survey_questions = [
        {
            "question_text": "How satisfied were you with the battery performance?",
            "question_type": "rating",
            "is_required": True,
            "question_order": 1,
            "rating_min": 1,
            "rating_max": 5,
            "rating_min_label": "Very Dissatisfied",
            "rating_max_label": "Very Satisfied"
        },
        {
            "question_text": "Did the battery meet your energy needs?",
            "question_type": "yes_no",
            "is_required": True,
            "question_order": 2
        },
        {
            "question_text": "How would you rate the rental process?",
            "question_type": "rating",
            "is_required": True,
            "question_order": 3,
            "rating_min": 1,
            "rating_max": 5,
            "rating_min_label": "Very Poor",
            "rating_max_label": "Excellent"
        },
        {
            "question_text": "What did you use the battery for?",
            "question_type": "multiple_choice",
            "is_required": False,
            "question_order": 4,
            "options": ["Lighting", "Phone Charging", "TV/Radio", "Small Appliances", "Business Equipment", "Other"]
        },
        {
            "question_text": "Would you rent from us again?",
            "question_type": "yes_no",
            "is_required": True,
            "question_order": 5
        },
        {
            "question_text": "Any suggestions for improvement?",
            "question_type": "text",
            "is_required": False,
            "question_order": 6
        }
    ]

    # Add questions for each hub
    questions_added = 0
    for hub in hubs:
        print(f"\n  Adding questions for hub: {hub.what_three_word_location}")

        # Check if hub already has survey questions
        existing = db.query(ReturnSurveyQuestion).filter(
            ReturnSurveyQuestion.hub_id == hub.hub_id
        ).count()

        if existing > 0:
            print(f"  ℹ️  Hub already has {existing} survey questions - skipping")
            continue

        for q_data in survey_questions:
            question = ReturnSurveyQuestion(
                hub_id=hub.hub_id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                is_required=q_data["is_required"],
                question_order=q_data["question_order"],
                rating_min=q_data.get("rating_min"),
                rating_max=q_data.get("rating_max"),
                rating_min_label=q_data.get("rating_min_label"),
                rating_max_label=q_data.get("rating_max_label")
            )
            db.add(question)
            questions_added += 1

            # Add options for multiple choice questions
            if q_data["question_type"] == "multiple_choice" and "options" in q_data:
                db.flush()  # Get the question ID
                for option_text in q_data["options"]:
                    option = ReturnSurveyQuestionOption(
                        question_id=question.question_id,
                        option_text=option_text
                    )
                    db.add(option)

    db.commit()
    print(f"\n✅ Added {questions_added} survey questions")


def populate_custom_field_options(db: Session):
    """Populate custom customer field options"""
    print("\n📝 Populating Custom Field Options...")

    # Get all hubs
    hubs = db.query(SolarHub).all()

    if not hubs:
        print("⚠️  No hubs found. Please create hubs first.")
        return

    # Define custom field options
    custom_field_options = {
        "gesi_status": {
            "display_name": "GESI Status",
            "options": [
                "Person with Disability",
                "Female-headed Household",
                "Youth (18-35)",
                "Elderly (60+)",
                "Refugee/Displaced Person",
                "Low Income Household",
                "Not Applicable"
            ]
        },
        "business_category": {
            "display_name": "Business Category",
            "options": [
                "Micro Business (1-5 employees)",
                "Small Business (6-20 employees)",
                "Medium Business (21-50 employees)",
                "Individual/Sole Proprietor",
                "Household (Non-business)",
                "Community Organization",
                "Other"
            ]
        },
        "main_reason_for_signup": {
            "display_name": "Main Reason for Signing Up",
            "options": [
                "No electricity access",
                "Unreliable grid electricity",
                "High electricity costs",
                "Business operations",
                "Productive use equipment",
                "Emergency backup power",
                "Environmental reasons",
                "Recommended by friend/family",
                "Other"
            ]
        }
    }

    options_added = 0
    for hub in hubs:
        print(f"\n  Adding options for hub: {hub.what_three_word_location}")

        for field_name, field_data in custom_field_options.items():
            # Check if options already exist for this hub and field
            existing = db.query(CustomerFieldOption).filter(
                CustomerFieldOption.hub_id == hub.hub_id,
                CustomerFieldOption.field_name == field_name
            ).count()

            if existing > 0:
                print(f"  ℹ️  '{field_data['display_name']}' options already exist - skipping")
                continue

            # Add options
            for order, option_value in enumerate(field_data["options"], start=1):
                option = CustomerFieldOption(
                    hub_id=hub.hub_id,
                    field_name=field_name,
                    option_value=option_value,
                    is_active=True,
                    sort_order=order
                )
                db.add(option)
                options_added += 1

            print(f"  ✅ Added '{field_data['display_name']}' with {len(field_data['options'])} options")

    db.commit()
    print(f"\n✅ Added {options_added} custom field options")


def main():
    """Main execution function"""
    print("=" * 70)
    print("POPULATING PRODUCTION SETTINGS")
    print("=" * 70)

    try:
        # Get database session
        db = next(get_db())

        # Populate return surveys
        populate_return_surveys(db)

        # Populate custom field options
        populate_custom_field_options(db)

        print("\n" + "=" * 70)
        print("✅ SETTINGS POPULATED SUCCESSFULLY")
        print("=" * 70)
        print("\nYou can now:")
        print("  1. View return surveys in Settings > Return Surveys")
        print("  2. View custom field options in Settings > Customer Data")
        print("  3. These will appear in customer forms and battery returns")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
