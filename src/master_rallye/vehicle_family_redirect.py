"""R-PHYS2.2 runtime-only named-family redirect evidence and plan helpers.

This module describes the fixed-build retail lookup path. It does not attach
to or modify a running game. It records the human-confirmed temporary catalog
pointer substitution and retains the original debugger procedure as a plan.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .vehicle_family_broker import (
    RETAIL_EXE_SHA256,
    family_type_ids,
    named_vehicle_path,
    runtime_car_path,
)


HUMAN_RUNTIME_EVIDENCE_STATUS = "CONFIRMED_BY_HUMAN_RUNTIME"
RUNTIME_EXPERIMENT_STATUS = "CONFIRMED_BY_HUMAN_RUNTIME"
REDIRECT_PLAN_STATUS = "PLAN_ONLY"


@dataclass(frozen=True)
class HumanBrokerRuntimeObservation:
    executable_sha256: str
    breakpoint_eip: int
    esp_at_hit: int
    ebp_at_hit: int
    caller_return_address: int
    family_object_address: int
    family_name: str
    overlay_text_visible_on_stack: str
    overlay_reader_call_confirmed_in_capture: bool
    evidence_status: str


HUMAN_NAVARA_BROKER_OBSERVATION = HumanBrokerRuntimeObservation(
    executable_sha256=RETAIL_EXE_SHA256,
    breakpoint_eip=0x00493E30,
    esp_at_hit=0x001AF808,
    ebp_at_hit=0,
    caller_return_address=0x0044F0D2,
    family_object_address=0x001AF838,
    family_name="Navara",
    overlay_text_visible_on_stack="Navara/Player1",
    overlay_reader_call_confirmed_in_capture=False,
    evidence_status=HUMAN_RUNTIME_EVIDENCE_STATUS,
)


@dataclass(frozen=True)
class HumanWholeFamilyRedirectObservation:
    """The successful Navara-carrier -> Trooper-family x32dbg experiment.

    Pointer values are retained as run-local evidence only. They must never be
    used as addresses by a later launcher or patcher.
    """

    executable_sha256: str
    breakpoint_eip: int
    participant_index: int
    carrier_type_id: int
    catalog_pointer_slot_address_for_this_run: int
    original_name_pointer_address_for_this_run: int
    original_family: str
    redirected_family: str
    base_reader_entry: int
    base_reader_caller_return: int
    overlay_family: str
    overlay_reader_entry: int
    runtime_writer: int
    race_started: bool
    wheel_placement_corrected: bool
    handling_changed_from_carrier: bool
    evidence_status: str


HUMAN_TROOPER_WHOLE_FAMILY_OBSERVATION = HumanWholeFamilyRedirectObservation(
    executable_sha256=RETAIL_EXE_SHA256,
    breakpoint_eip=0x0044EE69,
    participant_index=0,
    carrier_type_id=7,
    catalog_pointer_slot_address_for_this_run=0x03488A78,
    original_name_pointer_address_for_this_run=0x03489640,
    original_family="Navara",
    redirected_family="Trooper",
    base_reader_entry=0x00493E30,
    base_reader_caller_return=0x0044F0D2,
    overlay_family="Trooper/Player1",
    overlay_reader_entry=0x00493FD0,
    runtime_writer=0x004938C0,
    race_started=True,
    wheel_placement_corrected=True,
    handling_changed_from_carrier=True,
    evidence_status=HUMAN_RUNTIME_EVIDENCE_STATUS,
)


# The object supplied to FUN_00493E30 is 16 bytes at this fixed-build call
# site. The first dword is not named here because the inspected helpers do not
# establish its semantic role.
MANAGED_FAMILY_STRING_SIZE = 0x10
MANAGED_FAMILY_STRING_DATA_POINTER_OFFSET = 0x04
MANAGED_FAMILY_STRING_LENGTH_OFFSET = 0x08
MANAGED_FAMILY_STRING_CAPACITY_OFFSET = 0x0C
MANAGED_FAMILY_STRING_REFCOUNT_BYTE_FROM_DATA = -1


# FUN_0044EDFB is immediately before `MOV EAX,[EAX]`. At that point EAX is the
# address of the current catalog entry's C-string pointer field. The catalog
# entry computation is base + 0x24 + type_id * 0x34.
FAMILY_CATALOG_NAME_FIELD_BASE_OFFSET = 0x24
FAMILY_CATALOG_ENTRY_SIZE = 0x34
FAMILY_CATALOG_POINTER_READ_BREAKPOINT = 0x0044EDFB
FAMILY_OVERLAY_TEXT_CHECKPOINT = 0x0044EE25
BASE_FAMILY_READER_ENTRY = 0x00493E30
OVERLAY_READER_ENTRY = 0x00493FD0
BASE_READER_RETURN = 0x0044F0D2
OVERLAY_READER_RETURN = 0x0044F175
CAR_WRITER_RETURN_BREAKPOINT = 0x0044F343


@dataclass(frozen=True)
class WholeFamilyRedirectPlan:
    source_family: str
    target_family: str
    source_type_id: int
    target_type_ids_in_initialized_catalog: tuple[int, ...]
    participant_index: int
    overlay_player_number: int
    catalog_name_pointer_slot_offset: int
    source_pointer_read_breakpoint: int
    overlay_text_checkpoint: int
    base_reader_entry: int
    base_reader_return: int
    overlay_reader_entry: int
    overlay_reader_return: int
    runtime_car_path: str
    restore_after_family_strings_created_breakpoint: int
    car_writer_return_breakpoint: int
    replacement_c_string: str
    replacement_c_string_bytes_with_nul: int
    intervention: str
    status: str


def build_whole_family_redirect_plan(
    source_family: str,
    target_family: str,
    participant_index: int,
) -> dict[str, Any]:
    """Build the reversible pointer-substitution plan for one participant.

    `source_family` must already have exactly one initialized retail type ID.
    `target_family` needs only a named config root; it does not receive a new
    vehicle type ID. The actual runtime catalog field address is read from EAX
    at `source_pointer_read_breakpoint` rather than guessed from an ASLR base.
    """
    source_ids = family_type_ids(source_family)
    if len(source_ids) != 1:
        raise ValueError("source family must have exactly one initialized retail type ID")
    if isinstance(participant_index, bool) or not isinstance(participant_index, int) or participant_index < 0:
        raise ValueError("participant index must be a non-negative integer")
    named_vehicle_path(target_family)
    type_id = source_ids[0]
    player_number = 1 if participant_index == 0 else 2
    return asdict(WholeFamilyRedirectPlan(
        source_family=source_family,
        target_family=target_family,
        source_type_id=type_id,
        target_type_ids_in_initialized_catalog=family_type_ids(target_family),
        participant_index=participant_index,
        overlay_player_number=player_number,
        catalog_name_pointer_slot_offset=(
            FAMILY_CATALOG_NAME_FIELD_BASE_OFFSET + type_id * FAMILY_CATALOG_ENTRY_SIZE
        ),
        source_pointer_read_breakpoint=FAMILY_CATALOG_POINTER_READ_BREAKPOINT,
        overlay_text_checkpoint=FAMILY_OVERLAY_TEXT_CHECKPOINT,
        base_reader_entry=BASE_FAMILY_READER_ENTRY,
        base_reader_return=BASE_READER_RETURN,
        overlay_reader_entry=OVERLAY_READER_ENTRY,
        overlay_reader_return=OVERLAY_READER_RETURN,
        runtime_car_path=runtime_car_path(participant_index),
        restore_after_family_strings_created_breakpoint=FAMILY_OVERLAY_TEXT_CHECKPOINT,
        car_writer_return_breakpoint=CAR_WRITER_RETURN_BREAKPOINT,
        replacement_c_string=target_family,
        replacement_c_string_bytes_with_nul=len(target_family.encode("ascii")) + 1,
        intervention=(
            "Temporarily replace the existing source catalog entry's C-string "
            "pointer with a process-local NUL-terminated buffer; restore the "
            "original pointer just after the overlay builder returns, then free the buffer."
        ),
        status=REDIRECT_PLAN_STATUS,
    ))
