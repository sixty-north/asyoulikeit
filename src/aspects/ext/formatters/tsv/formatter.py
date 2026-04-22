"""Tab-separated values formatter."""

from aspects.formatter import Formatter
from aspects.tabular_data import Reports, DetailLevel


class TsvFormatter(Formatter):
    """Tab-separated values formatter for UNIX-style processing.

    Outputs data as TSV with optional header rows, suitable for use with traditional
    UNIX tools like awk, cut, and grep. Headers are prefixed with "# " by default
    to allow tools to identify and skip them as comments.

    Multiple tables are separated by blank lines. Clients parse based on column
    headings they discover in each section.

    Examples:
        Single table with header=True (default)::

            # Format Name<tab>Description
            yaml<tab>YAML serializer for...

        Multiple tables with blank line separator::

            # Output Path
            /path/to/file1.png
            /path/to/file2.png

            # Fragment<tab>Elapsed<tab>Slept
            0<tab>1.234<tab>1.000
            1<tab>0.500<tab>0.450

        With header=False::

            yaml<tab>YAML serializer for...
    """

    def format(self, reports: Reports) -> str:
        """Format reports as TSV with optional header rows.

        Args:
            reports: A Reports object containing one or more named reports

        Returns:
            TSV string with tables separated by blank lines.
            If present_transposed is True for a report, its rows and columns are swapped.
        """
        table_outputs = []

        for report_name, report in reports.items():
            data = report.data
            detail_level = report.detail_level
            header = report.header

            # Transpose if requested
            if data.present_transposed:
                data = data.transpose()

            # TSV defaults to essential-only for machine parseability
            if detail_level == DetailLevel.AUTO:
                detail_level = DetailLevel.ESSENTIAL

            # Filter columns based on detail_level
            columns = (
                data.columns if detail_level == DetailLevel.DETAILED
                else data.essential_columns
            )

            # Filter rows based on detail_level
            rows = data.rows_for_detail_level(detail_level)

            lines = []

            # Header row (optional, with comment prefix)
            if header:
                labels = [col.label for col in columns]
                if labels:
                    # Prefix first cell with "# " to mark as comment
                    labels[0] = f"# {labels[0]}"
                lines.append("\t".join(labels))

            # Data rows
            for row in rows:
                values = [str(row[col.key]) for col in columns]
                lines.append("\t".join(values))

            table_outputs.append("\n".join(lines))

        # Join tables with blank line separator
        return "\n\n".join(table_outputs)
