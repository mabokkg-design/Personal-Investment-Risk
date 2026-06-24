import io
import pandas as pd
from .base import BaseConnector, POSITIONS_SCHEMA


class CSVImportConnector(BaseConnector):
    def __init__(self, source: str | bytes):
        if isinstance(source, str):
            self._buf = io.StringIO(source)
        else:
            self._buf = io.BytesIO(source)

    def get_positions(self) -> pd.DataFrame:
        df = pd.read_csv(self._buf)
        df.columns = df.columns.str.strip().str.lower()

        missing = [c for c in POSITIONS_SCHEMA if c not in df.columns]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        df = df[POSITIONS_SCHEMA].copy()
        df["ticker"] = df["ticker"].str.upper().str.strip()
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        df["avg_cost"] = pd.to_numeric(df["avg_cost"], errors="coerce")
        df.dropna(inplace=True)

        return self._enrich_positions(df)
