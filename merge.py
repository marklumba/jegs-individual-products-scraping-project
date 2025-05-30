import pandas as pd
import glob
import os
import xlwings as xw

def format_excel_file(file_path):
    """Formats an Excel file using xlwings."""
    with xw.App(visible=False) as app:
        wb = xw.Book(file_path)
        ws = wb.sheets[0]
        
        # Format header
        header_range = ws.range('1:1')
        header_range.color = (200, 200, 200)
        header_range.api.Font.Bold = True
        
        # Autofit columns
        ws.autofit('c')
        
        # Set minimum and maximum column widths
        for column in ws.api.UsedRange.Columns:
            if column.ColumnWidth < 8:
                column.ColumnWidth = 8
            elif column.ColumnWidth > 50:
                column.ColumnWidth = 50
        
        wb.save()
        wb.close()

def merge_excel_files(input_folder, output_file_name):
    """Merges multiple Excel files and writes to a new file."""
    # Get the list of Excel files
    files = glob.glob(os.path.join(input_folder, '*.xlsx'))
    if not files:
        print("No Excel files found in the specified folder.")
        return

    # Read files into dataframes
    dfs = []
    for file in files:
        try:
            df = pd.read_excel(file)
            if not df.empty:
                dfs.append(df)
        except Exception as e:
            print(f"Could not read {file}: {e}")

    if not dfs:
        print("No valid dataframes to merge.")
        return

    # Concatenate dataframes
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df = merged_df.dropna(how='all')  # Drop rows where all elements are NaN

    # Define the output file path
    file_path = os.path.join(os.path.expanduser("~"), "Desktop", output_file_name)
    merged_df.to_excel(file_path, index=False, freeze_panes=(1, 0))

    # Format the output file
    format_excel_file(file_path)

    print(f"Data successfully saved to: {file_path}")

# Define paths and parameters
input_folder = r"C:\Users\Mark Lumba\Desktop\Jegs Scraped Data\Bestop\Application"
output_file_name = "Bestop_Application.xlsx"

# Merge Excel files
merge_excel_files(input_folder, output_file_name)