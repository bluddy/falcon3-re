# Tactical Map Global Variables

**Generated**: 2026-11-15
**Source**: Tactical map rendering analysis

## Overview

This document catalogs 23 global variables discovered during tactical map analysis.

## Variables

### Map View State

#### map_view_coord_x

- **Address**: 0x594C8
- **Type**: `uint16_t`
- **Description**: Map view X coordinate or bound
- **Source**: map_view_project_pipeline sets this before drawing

#### map_view_bound_width

- **Address**: 0x594CA
- **Type**: `uint16_t`
- **Description**: Map view width bound (185 / 0xB9)
- **Source**: Set to 0xB9 in map_view_project_pipeline

#### map_view_coord_y

- **Address**: 0x594CC
- **Type**: `uint16_t`
- **Description**: Map view Y coordinate or bound
- **Source**: map_view_project_pipeline sets this before drawing

#### map_view_bound_height

- **Address**: 0x594CE
- **Type**: `uint16_t`
- **Description**: Map view height bound (191 / 0xBF)
- **Source**: Set to 0xBF in map_view_project_pipeline

### Far Object Sorting

#### farobj_sort_count_secondary

- **Address**: 0x7C054
- **Segment**: 0x7B0E
- **Type**: `uint16_t`
- **Description**: Number of objects in secondary sort list
- **Source**: farobj_sort_and_step checks this count

#### farobj_sort_count_primary

- **Address**: 0x7D0C2
- **Segment**: 0x7B0E
- **Type**: `uint16_t`
- **Description**: Number of objects in primary sort list
- **Source**: farobj_sort_and_step checks this count

### Entity Rendering State

#### farobj_render_color_mode_2

- **Address**: 0x1F730
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Color/rendering mode flag 2
- **Source**: Saved/restored around handler call

#### farobj_render_color_mode_1

- **Address**: 0x1F731
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Color/rendering mode flag 1
- **Source**: Saved/restored around handler call

#### farobj_render_force_rotation

- **Address**: 0x1F732
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Force rotation flag (0xFF=force)
- **Source**: Controls whether rotation_index is calculated

#### farobj_render_alternate_color

- **Address**: 0x1F738
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Alternate color flag from entity flags bits 1-2
- **Source**: Set based on entity flags & 0x06

#### farobj_render_visibility_flag

- **Address**: 0x1F73D
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Visibility flag (0xFF=visible, 0x00=hidden)
- **Source**: Set based on entity flags bit 1

#### farobj_render_lod_level

- **Address**: 0x1F742
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Current LOD level for entity rendering
- **Source**: Set by farobj_record_step during LOD selection

#### farobj_render_scale_shift

- **Address**: 0x1F743
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Bit shift amount for distance scaling
- **Source**: Used in farobj_record_step coordinate transformation

#### farobj_render_rotation_index

- **Address**: 0x1F739
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Rotation index extracted from entity flags bits 3-4
- **Source**: (flags >> 3) & 3

#### farobj_render_state_flag_20

- **Address**: 0x1F741
- **Segment**: cs
- **Type**: `uint8_t`
- **Description**: Rendering state flag from entity flags bit 5
- **Source**: Masked from entity flags & 0x20

### Display Pointers

#### display_data_ptr_off

- **Address**: 0x7A2E8
- **Segment**: 0x7894
- **Type**: `uint16_t`
- **Description**: Display data pointer offset
- **Source**: Forms far pointer with segment

#### display_data_ptr_seg

- **Address**: 0x7A2EA
- **Segment**: 0x7894
- **Type**: `uint16_t`
- **Description**: Display data pointer segment
- **Source**: Used in tactical screen coordinator

#### display_buffer_handle

- **Address**: 0x7A2F2
- **Segment**: 0x7894
- **Type**: `uint16_t`
- **Description**: Display buffer handle or identifier
- **Source**: Used in waypoint_coordinate_processor

#### display_waypoint_ptr_off

- **Address**: 0x7A2F4
- **Segment**: 0x7894
- **Type**: `uint16_t`
- **Description**: Waypoint array pointer offset
- **Source**: Together with seg forms far pointer to 0x4FC2:0x168

#### display_waypoint_ptr_seg

- **Address**: 0x7A2F6
- **Segment**: 0x7894
- **Type**: `uint16_t`
- **Description**: Waypoint array pointer segment
- **Source**: Points to waypoint data for display

### Dispatch Table

#### farobj_entity_type_handlers

- **Address**: 0x26426
- **Type**: `void (*[28])()`
- **Description**: Dispatch table of 28 entity type drawing handlers
- **Source**: farobj_record_step calls cs:off_26426[type_index]
