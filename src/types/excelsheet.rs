use std::sync::Arc;

use anyhow::{Context, Result};
use arrow::{
    array::{
        Array, BooleanArray, Float64Array, Int64Array, NullArray, StringArray,
        TimestampMillisecondArray,
    },
    datatypes::{DataType as ArrowDataType, Schema},
    record_batch::RecordBatch,
};
use calamine::{DataType as CalDataType, Range};

use pyo3::{pyclass, pymethods, PyObject, Python};

use crate::utils::arrow::record_batch_to_pybytes;

#[pyclass(name = "_ExcelSheet")]
pub(crate) struct ExcelSheet {
    #[pyo3(get)]
    name: String,
    schema: Schema,
    data: Range<CalDataType>,
    height: Option<usize>,
    width: Option<usize>,
}

impl ExcelSheet {
    pub(crate) fn schema(&self) -> &Schema {
        &self.schema
    }

    pub(crate) fn data(&self) -> &Range<CalDataType> {
        &self.data
    }

    pub(crate) fn new(name: String, schema: Schema, data: Range<CalDataType>) -> Self {
        ExcelSheet {
            name,
            schema,
            data,
            height: None,
            width: None,
        }
    }
}

fn create_boolean_array(data: &Range<CalDataType>, col: usize, height: usize) -> Arc<dyn Array> {
    Arc::new(BooleanArray::from_iter((1..height).map(|row| {
        data.get((row, col)).and_then(|cell| cell.get_bool())
    })))
}

fn create_int_array(data: &Range<CalDataType>, col: usize, height: usize) -> Arc<dyn Array> {
    Arc::new(Int64Array::from_iter(
        (1..height).map(|row| data.get((row, col)).and_then(|cell| cell.get_int())),
    ))
}

fn create_float_array(data: &Range<CalDataType>, col: usize, height: usize) -> Arc<dyn Array> {
    Arc::new(Float64Array::from_iter((1..height).map(|row| {
        data.get((row, col)).and_then(|cell| cell.get_float())
    })))
}

fn create_string_array(data: &Range<CalDataType>, col: usize, height: usize) -> Arc<dyn Array> {
    Arc::new(StringArray::from_iter((1..height).map(|row| {
        data.get((row, col)).and_then(|cell| cell.get_string())
    })))
}

fn create_date_array(data: &Range<CalDataType>, col: usize, height: usize) -> Arc<dyn Array> {
    Arc::new(TimestampMillisecondArray::from_iter((1..height).map(
        |row| {
            data.get((row, col))
                .and_then(|cell| cell.as_datetime())
                .map(|dt| dt.timestamp_millis())
        },
    )))
}

impl TryFrom<&ExcelSheet> for RecordBatch {
    type Error = anyhow::Error;

    fn try_from(value: &ExcelSheet) -> Result<Self, Self::Error> {
        let height = value.data().height();
        let iter = value
            .schema()
            .fields()
            .iter()
            .enumerate()
            .map(|(col_idx, field)| {
                (
                    field.name(),
                    match field.data_type() {
                        ArrowDataType::Boolean => {
                            create_boolean_array(value.data(), col_idx, height)
                        }
                        ArrowDataType::Int64 => create_int_array(value.data(), col_idx, height),
                        ArrowDataType::Float64 => create_float_array(value.data(), col_idx, height),
                        ArrowDataType::Utf8 => create_string_array(value.data(), col_idx, height),
                        ArrowDataType::Date64 => create_date_array(value.data(), col_idx, height),
                        ArrowDataType::Null => Arc::new(NullArray::new(height - 1)),
                        _ => unreachable!(),
                    },
                )
            });
        RecordBatch::try_from_iter(iter)
            .with_context(|| format!("Could not convert sheet {} to RecordBatch", value.name))
    }
}

#[pymethods]
impl ExcelSheet {
    #[getter]
    pub fn width(&mut self) -> usize {
        if let Some(width) = self.width {
            width
        } else {
            let width = self.schema.fields().len();
            self.width = Some(width);
            width
        }
    }

    #[getter]
    pub fn height(&mut self) -> usize {
        if let Some(height) = self.height {
            height
        } else {
            let data_height = self.data.height();
            // FIXME: Remove the subtraction once we support sheets without headers
            let height = if data_height > 0 { data_height - 1 } else { 0 };
            self.height = Some(height);
            height
        }
    }

    pub fn to_arrow(&self, py: Python<'_>) -> Result<PyObject> {
        let rb = RecordBatch::try_from(self)
            .with_context(|| format!("Could not create RecordBatch from sheet {}", self.name))?;
        record_batch_to_pybytes(py, &rb).map(|pybytes| pybytes.into())
    }

    pub fn __repr__(&self) -> String {
        format!("ExcelSheet<{}>", self.name)
    }
}
