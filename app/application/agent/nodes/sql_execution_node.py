from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.agent.state import AgentState


class SQLExecutionNode:
    """
    Executes validated SQL plans using SQLAlchemy raw queries.
    """

    ALLOWED_OPERATORS = {
        "=", "!=", "<>", ">", "<", ">=", "<=",
        "LIKE", "ILIKE", "NOT LIKE", "NOT ILIKE",
        "IN", "NOT IN", "IS", "IS NOT", "BETWEEN",
    }
    ALLOWED_AGGREGATES = {"SUM", "COUNT", "AVG", "MIN", "MAX"}
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 50

    def __init__(self, db: Session):
        self.db = db

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        plan     = state.generated_sql
        table    = plan["table"]
        joins    = plan.get("joins", [])
        select   = plan.get("select", [])
        filters  = plan.get("filters", [])
        group_by = plan.get("group_by", [])
        limit    = min(plan.get("limit", self.DEFAULT_LIMIT), self.MAX_LIMIT)

        params = {}

        # ── SELECT ────────────────────────────────────────────────────────────
        select_clauses = []
        for item in select:
            if "aggregate" in item:
                agg   = item["aggregate"].upper()
                col   = item["column"]
                alias = item.get("alias", f"{agg.lower()}_{col.replace('.', '_')}")
                if agg not in self.ALLOWED_AGGREGATES:
                    state.is_blocked  = True
                    state.block_reason = f"invalid_aggregate:{agg}"
                    return state
                select_clauses.append(f"{agg}({col}) AS {alias}")
            elif "column" in item:
                select_clauses.append(item["column"])

        if not select_clauses:
            state.is_blocked  = True
            state.block_reason = "missing_select"
            return state

        # ── FROM + JOIN ───────────────────────────────────────────────────────
        from_clause = f"FROM {table}"
        join_sql    = "\n".join(f"JOIN {j['table']} ON {j['on']}" for j in joins)

        # ── WHERE ─────────────────────────────────────────────────────────────
        where_clauses = []
        for idx, f in enumerate(filters):
            column   = f["column"]
            operator = f["operator"].upper()

            if operator not in self.ALLOWED_OPERATORS:
                state.is_blocked  = True
                state.block_reason = f"invalid_operator:{operator}"
                return state

            if "param" in f:
                param_name = f["param"]

                # FIX: This is a public/open agent — there is no authenticated
                # user.  When the model emits a param-based filter (e.g.
                # `tasks.assigned_to = :user_id`) because the user said "my
                # tasks", and state.user_id is None, binding NULL would either
                # return zero rows (NULL ≠ anything in SQL) or raise a type
                # error.  Instead we silently drop the filter so the query
                # falls back to returning all accessible rows — which is the
                # correct behaviour for a public agent.
                if state.user_id is None:
                    print(
                        f"[SQLExecutionNode] Dropping param filter "
                        f"'{column} {operator} :{param_name}' "
                        f"— no user_id in open-agent mode."
                    )
                    continue  # skip this filter, don't add to where_clauses

                where_clauses.append(f"{column} {operator} :{param_name}")
                params[param_name] = state.user_id

            elif "value" in f:
                key          = f"value_{idx}"
                params[key]  = f"%{f['value']}%" if operator == "ILIKE" else f["value"]
                where_clauses.append(f"{column} {operator} :{key}")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        group_sql = f"GROUP BY {', '.join(group_by)}" if group_by else ""

        sql = f"""
            SELECT {", ".join(select_clauses)}
            {from_clause}
            {join_sql}
            WHERE {where_sql}
            {group_sql}
            LIMIT {limit}
        """.strip()

        try:
            result  = self.db.execute(text(sql), params)
            columns = list(result.keys())
            rows    = result.fetchall()
        except Exception as e:
            print(f"[SQLExecutionNode] SQL EXECUTION ERROR: {e}")
            state.is_blocked  = True
            state.block_reason = "sql_execution_failed"
            return state

        state.sql_rows = [dict(zip(columns, row)) for row in rows]
        return state