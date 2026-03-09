from app.application.agent.state import AgentState


class ResultFormatterNode:
    """
    Deterministic SQL result formatter.

    Behavior:
    - 0 rows  → empty message
    - 1 small row → single-line summary
    - Multiple rows → table mode
    """

    SIMPLE_MAX_COLUMNS = 3
    SIMPLE_MAX_ROWS = 1

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        rows = state.sql_rows or []
        row_count = len(rows)

        if row_count == 0:
            state.response = {
                "row_count": 0,
                "rows": [],
                "summary": "No matching records found.",
                "mode": "empty",
            }
            return state

        columns = list(rows[0].keys())

        if row_count <= self.SIMPLE_MAX_ROWS and len(columns) <= self.SIMPLE_MAX_COLUMNS:
            row = rows[0]
            values = ", ".join(
                f"{col.replace('_', ' ').capitalize()}: {row[col]}" for col in columns
            )
            state.response = {
                "row_count": row_count,
                "rows": rows,
                "summary": values,
                "mode": "simple",
            }
            return state

        state.response = {
            "row_count": row_count,
            "rows": rows,
            "summary": f"Here are {row_count} matching records.",
            "mode": "table",
        }
        return state
