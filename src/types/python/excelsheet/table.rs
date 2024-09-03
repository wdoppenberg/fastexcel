use std::io::{Read, Seek};
use calamine::{Data, Sheets, Table};
use crate::error::{ErrorContext, FastExcelError, FastExcelErrorKind, FastExcelResult};

pub(crate) fn extract_table_names<'a, RS: Read + Seek>(sheets: &'a mut Sheets<RS>, sheet_name: Option<&str>) -> Result<FastExcelResult<Vec<&'a String>>, FastExcelError> {
	Ok(match sheets {
		Sheets::Xlsx(xlsx) => {
			// Internally checks if tables already loaded; is fast
			xlsx.load_tables()?;
			
			match sheet_name {
				None => {Ok(xlsx.table_names())}
				Some(sn) => {Ok(xlsx.table_names_in_sheet(sn))}
			}
		}
		_ => {
			Err(
				FastExcelErrorKind::Internal(
					"Currently only XLSX files are supported for tables".to_string(),
				).into()
			)
		}
	})
}


pub(crate) fn extract_table_range<RS: Read + Seek>(name: &str, sheets: &mut Sheets<RS>) -> Result<FastExcelResult<Table<Data>>, FastExcelError> {
	Ok(match sheets {
		Sheets::Xlsx(xlsx) => {
			// Internally checks if tables already loaded; is fast
			xlsx.load_tables()?;

			let table_result = xlsx.table_by_name(name);
			let table = table_result
				.map_err(|err| FastExcelErrorKind::XlsxError(err).into())
				.with_context(|| format!("Could not load table named {name}"))?;
			
			Ok(table)
		}
		_ => {
			Err(
				FastExcelErrorKind::Internal(
					"Currently only XLSX files are supported for tables".to_string(),
				).into()
			)
		}
	})
}