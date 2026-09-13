from __future__ import annotations

import pytest

from jla.privacy import (
    assert_public_projection_columns_safe,
    privacy_risk_columns,
    public_projection_report,
)


def test_privacy_classifier_uses_headers_only_and_finds_contact_fields() -> None:
    header = [
        "Hospital Name",
        "District",
        "Nodal Person Name",
        "Mobile Number",
        "E-Mail",
        "Telephone No.",
    ]
    findings = privacy_risk_columns(header)
    categories = {item["column"]: item["category"] for item in findings}
    assert categories["Nodal Person Name"] == "named_person"
    assert categories["Mobile Number"] == "mobile"
    assert categories["E-Mail"] == "email"
    assert categories["Telephone No."] == "telephone"
    assert "Hospital Name" not in categories
    assert "District" not in categories


def test_privacy_classifier_catches_nonstandard_contact_channels_without_false_positive_counts() -> None:
    header = [
        "Emergency_Num",
        "Tollfree",
        "Helpline",
        "Hospital_Fax",
        "Number_Doctor",
        "Total_Num_Beds",
    ]
    categories = {item["column"]: item["category"] for item in privacy_risk_columns(header)}
    assert categories["Emergency_Num"] == "telephone"
    assert categories["Tollfree"] == "telephone"
    assert categories["Helpline"] == "telephone"
    assert categories["Hospital_Fax"] == "telephone"
    assert "Number_Doctor" not in categories
    assert "Total_Num_Beds" not in categories


def test_public_projection_report_is_row_value_free_and_fail_closed() -> None:
    report = public_projection_report(
        ["Hospital Name", "District", "Mobile Number", "Absent Column"],
        source_header=["Hospital Name", "District", "Mobile Number"],
    )
    assert report["contract"] == "JLA_PRIVACY_PUBLIC_PROJECTION_V1"
    assert report["classification_scope"] == "header_names_only"
    assert report["row_values_inspected"] is False
    assert report["row_values_recorded"] is False
    assert report["safe_selected_columns"] == ["Hospital Name", "District"]
    assert report["missing_selected_columns"] == ["Absent Column"]
    assert report["privacy_risk_columns"] == [
        {"column": "Mobile Number", "category": "mobile"}
    ]
    assert report["privacy_gate_passed"] is False


def test_public_projection_report_passes_only_safe_observed_columns() -> None:
    report = public_projection_report(
        ["Hospital Name", None, "District", "Hospital Name"],
        source_header=["Hospital Name", "District", "Latitude"],
    )
    assert report["selected_columns"] == ["Hospital Name", "District"]
    assert report["safe_selected_columns"] == ["Hospital Name", "District"]
    assert report["privacy_risk_columns"] == []
    assert report["missing_selected_columns"] == []
    assert report["privacy_gate_passed"] is True


def test_assertion_rejects_missing_columns_before_publication() -> None:
    with pytest.raises(ValueError, match="absent from source header"):
        assert_public_projection_columns_safe(
            ["Hospital Name", "Unknown"], source_header=["Hospital Name"]
        )


def test_assertion_rejects_privacy_risk_columns_before_publication() -> None:
    with pytest.raises(ValueError, match="privacy-risk"):
        assert_public_projection_columns_safe(
            ["Hospital Name", "Contact Person"],
            source_header=["Hospital Name", "Contact Person"],
        )


def test_assertion_accepts_safe_observed_projection() -> None:
    assert_public_projection_columns_safe(
        ["Hospital Name", "District"],
        source_header=["Hospital Name", "District", "Phone"],
    )
