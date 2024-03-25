from __future__ import annotations

import re
from typing import Any

import fastexcel
import pandas as pd
import polars as pl
import pytest
from pandas.testing import assert_frame_equal as pd_assert_frame_equal
from polars.testing import assert_frame_equal as pl_assert_frame_equal
from utils import path_for_fixture


@pytest.fixture
def excel_reader_single_sheet() -> fastexcel.ExcelReader:
    return fastexcel.read_excel(path_for_fixture("fixture-single-sheet.xlsx"))


@pytest.fixture
def expected_column_info() -> list[fastexcel.ColumnInfo]:
    return [
        fastexcel.ColumnInfo(
            name="Month", index=0, column_name_from="looked_up", dtype="float", dtype_from="guessed"
        ),
        fastexcel.ColumnInfo(
            name="Year", index=1, column_name_from="looked_up", dtype="float", dtype_from="guessed"
        ),
    ]


def test_single_sheet_all_columns(
    excel_reader_single_sheet: fastexcel.ExcelReader,
    expected_column_info: list[fastexcel.ColumnInfo],
) -> None:
    sheet = excel_reader_single_sheet.load_sheet(0)

    sheet_explicit_arg = excel_reader_single_sheet.load_sheet(0, use_columns=None)
    assert sheet.selected_columns == expected_column_info
    assert sheet.available_columns == expected_column_info

    expected = {"Month": [1.0, 2.0], "Year": [2019.0, 2020.0]}
    expected_pd_df = pd.DataFrame(expected)
    expected_pl_df = pl.DataFrame(expected)

    pd_df = sheet.to_pandas()
    pd_assert_frame_equal(pd_df, expected_pd_df)
    pd_df_explicit_arg = sheet_explicit_arg.to_pandas()
    pd_assert_frame_equal(pd_df_explicit_arg, expected_pd_df)

    pl_df = sheet.to_polars()
    pl_assert_frame_equal(pl_df, expected_pl_df)
    pl_df_explicit_arg = sheet_explicit_arg.to_polars()
    pl_assert_frame_equal(pl_df_explicit_arg, expected_pl_df)


def test_single_sheet_subset_by_str(
    excel_reader_single_sheet: fastexcel.ExcelReader,
    expected_column_info: list[fastexcel.ColumnInfo],
) -> None:
    expected = {"Month": [1.0, 2.0], "Year": [2019.0, 2020.0]}

    # looks like mypy 1.8 became more stupid
    sheets: list[str | int] = [0, "January"]
    for sheet_name_or_idx in sheets:
        for idx, col in enumerate(["Month", "Year"]):
            sheet = excel_reader_single_sheet.load_sheet(sheet_name_or_idx, use_columns=[col])
            assert sheet.selected_columns == [expected_column_info[idx]]
            assert sheet.available_columns == expected_column_info

            pd_df = sheet.to_pandas()
            pd_assert_frame_equal(pd_df, pd.DataFrame({col: expected[col]}))

            pl_df = sheet.to_polars()
            pl_assert_frame_equal(pl_df, pl.DataFrame({col: expected[col]}))


def test_single_sheet_subset_by_index(
    excel_reader_single_sheet: fastexcel.ExcelReader,
    expected_column_info: list[fastexcel.ColumnInfo],
) -> None:
    expected = {"Month": [1.0, 2.0], "Year": [2019.0, 2020.0]}

    sheets: list[str | int] = [0, "January"]
    for sheet_name_or_idx in sheets:
        for idx, col_name in enumerate(["Month", "Year"]):
            sheet = excel_reader_single_sheet.load_sheet(sheet_name_or_idx, use_columns=[idx])
            assert sheet.selected_columns == [expected_column_info[idx]]
            assert sheet.available_columns == expected_column_info

            pd_df = sheet.to_pandas()
            pd_assert_frame_equal(pd_df, pd.DataFrame({col_name: expected[col_name]}))

            pl_df = sheet.to_polars()
            pl_assert_frame_equal(pl_df, pl.DataFrame({col_name: expected[col_name]}))


@pytest.fixture
def excel_reader_single_sheet_with_unnamed_columns() -> fastexcel.ExcelReader:
    return fastexcel.read_excel(path_for_fixture("fixture-multi-sheet.xlsx"))


@pytest.fixture
def single_sheet_with_unnamed_columns_expected() -> dict[str, list[Any]]:
    return {
        "col1": [2.0, 3.0],
        "__UNNAMED__1": [1.5, 2.5],
        "col3": ["hello", "world"],
        "__UNNAMED__3": [-5.0, -6.0],
        "col5": ["a", "b"],
    }


@pytest.fixture
def sheet_with_unnamed_columns_expected_column_info() -> list[fastexcel.ColumnInfo]:
    return [
        fastexcel.ColumnInfo(
            name="col1", index=0, column_name_from="looked_up", dtype="float", dtype_from="guessed"
        ),
        fastexcel.ColumnInfo(
            name="__UNNAMED__1",
            index=1,
            column_name_from="generated",
            dtype="float",
            dtype_from="guessed",
        ),
        fastexcel.ColumnInfo(
            name="col3", index=2, column_name_from="looked_up", dtype="string", dtype_from="guessed"
        ),
        fastexcel.ColumnInfo(
            name="__UNNAMED__3",
            index=3,
            column_name_from="generated",
            dtype="float",
            dtype_from="guessed",
        ),
        fastexcel.ColumnInfo(
            name="col5", index=4, column_name_from="looked_up", dtype="string", dtype_from="guessed"
        ),
    ]


def test_single_sheet_with_unnamed_columns(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
    single_sheet_with_unnamed_columns_expected: dict[str, list[Any]],
    sheet_with_unnamed_columns_expected_column_info: list[fastexcel.ColumnInfo],
) -> None:
    use_columns_str = ["col1", "col3", "__UNNAMED__3"]
    use_columns_idx = [0, 2, 3]
    expected = {
        k: v for k, v in single_sheet_with_unnamed_columns_expected.items() if k in use_columns_str
    }

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_str
    )
    assert sheet.selected_columns == [
        sheet_with_unnamed_columns_expected_column_info[0],
        sheet_with_unnamed_columns_expected_column_info[2],
        sheet_with_unnamed_columns_expected_column_info[3],
    ]
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_idx
    )
    assert sheet.selected_columns == [
        sheet_with_unnamed_columns_expected_column_info[0],
        sheet_with_unnamed_columns_expected_column_info[2],
        sheet_with_unnamed_columns_expected_column_info[3],
    ]
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))


def test_single_sheet_with_unnamed_columns_and_pagination(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
    single_sheet_with_unnamed_columns_expected: dict[str, list[Any]],
    sheet_with_unnamed_columns_expected_column_info: list[fastexcel.ColumnInfo],
) -> None:
    use_columns_str = ["col1", "col3", "__UNNAMED__3"]
    use_columns_idx = [0, 2, 3]

    # first row only
    expected = {
        k: v[:1]
        for k, v in single_sheet_with_unnamed_columns_expected.items()
        if k in use_columns_str
    }

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_str, n_rows=1
    )
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_idx, n_rows=1
    )
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))

    # second row
    expected = {
        k: v[1:]
        for k, v in single_sheet_with_unnamed_columns_expected.items()
        if k in use_columns_str
    }

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_str, skip_rows=1
    )
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_idx, skip_rows=1
    )
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))


def test_single_sheet_with_unnamed_columns_and_pagination_and_column_names(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
) -> None:
    use_columns_str = ["col0", "col2", "col3"]
    use_columns_idx = [0, 2, 3]
    expected: dict[str, list[Any]] = {
        "col0": [2.0, 3.0],
        "col2": ["hello", "world"],
        "col3": [-5.0, -6.0],
    }
    column_names = [f"col{i}" for i in range(5)]

    # skipping the header row only
    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_str, skip_rows=1, column_names=column_names
    )
    assert [col.name for col in sheet.available_columns] == column_names

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_idx, skip_rows=1, column_names=column_names
    )
    assert [col.name for col in sheet.available_columns] == column_names

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))

    # skipping the header row + first data row
    expected_first_row_skipped = {k: v[1:] for k, v in expected.items()}

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_str, skip_rows=2, column_names=column_names
    )
    assert [col.name for col in sheet.available_columns] == column_names

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected_first_row_skipped))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected_first_row_skipped))

    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_idx, skip_rows=2, column_names=column_names
    )
    assert [col.name for col in sheet.available_columns] == column_names

    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected_first_row_skipped))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected_first_row_skipped))


def test_single_sheet_with_unnamed_columns_and_str_range(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
    single_sheet_with_unnamed_columns_expected: dict[str, list[Any]],
    sheet_with_unnamed_columns_expected_column_info: list[fastexcel.ColumnInfo],
) -> None:
    use_columns_str = "A,C:E"
    expected = {
        k: v
        for k, v in single_sheet_with_unnamed_columns_expected.items()
        if k in ["col1", "col3", "__UNNAMED__3", "col5"]
    }
    sheet = excel_reader_single_sheet_with_unnamed_columns.load_sheet(
        "With unnamed columns", use_columns=use_columns_str
    )
    assert sheet.selected_columns == (
        sheet_with_unnamed_columns_expected_column_info[:1]
        + sheet_with_unnamed_columns_expected_column_info[2:]
    )
    assert sheet.available_columns == sheet_with_unnamed_columns_expected_column_info
    pd_assert_frame_equal(sheet.to_pandas(), pd.DataFrame(expected))
    pl_assert_frame_equal(sheet.to_polars(), pl.DataFrame(expected))


def test_single_sheet_invalid_column_indices_negative_integer(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
) -> None:
    expected_message = """invalid parameters: expected list[int] | list[str], got [-2]
Context:
    0: could not determine selected columns from provided object: [-2]
    1: expected selected columns to be list[str] | list[int] | str | None, got Some([-2])
"""
    with pytest.raises(fastexcel.InvalidParametersError, match=re.escape(expected_message)):
        excel_reader_single_sheet_with_unnamed_columns.load_sheet(0, use_columns=[-2])


def test_single_sheet_invalid_column_indices_empty_list(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
) -> None:
    expected_message = """invalid parameters: list of selected columns is empty
Context:
    0: could not determine selected columns from provided object: []
    1: expected selected columns to be list[str] | list[int] | str | None, got Some([])
"""
    with pytest.raises(fastexcel.InvalidParametersError, match=re.escape(expected_message)):
        excel_reader_single_sheet_with_unnamed_columns.load_sheet(0, use_columns=[])


def test_single_sheet_invalid_column_indices_column_does_not_exist_str(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
) -> None:
    expected_message = """column with name \"nope\" not found
Context:
    0: available columns are: .*
"""
    with pytest.raises(fastexcel.ColumnNotFoundError, match=expected_message):
        excel_reader_single_sheet_with_unnamed_columns.load_sheet(0, use_columns=["nope"])


def test_single_sheet_invalid_column_indices_column_does_not_exist_int(
    excel_reader_single_sheet_with_unnamed_columns: fastexcel.ExcelReader,
) -> None:
    expected_message = """column at index 42 not found
Context:
    0: available columns are: .*
"""
    with pytest.raises(fastexcel.ColumnNotFoundError, match=expected_message):
        excel_reader_single_sheet_with_unnamed_columns.load_sheet(0, use_columns=[42])
