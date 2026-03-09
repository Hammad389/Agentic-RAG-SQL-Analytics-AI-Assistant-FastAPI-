from app.application.agent.state import AgentState
from app.domain.sql_schema_registry import extract_allowed_tables, get_schemas


class SQLValidationNode:
    ALLOWED_OPERATORS = {
        "=", "!=", "<>", ">", "<", ">=", "<=",
        "LIKE", "ILIKE", "NOT LIKE", "NOT ILIKE",
        "IN", "NOT IN", "IS", "IS NOT", "BETWEEN",
    }
    ALLOWED_AGGREGATES = {"SUM", "COUNT", "AVG", "MIN", "MAX"}
    ALLOWED_PARAMS = {"user_id"}
    MAX_LIMIT = 50

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        plan = state.generated_sql

        if not isinstance(plan, dict):
            state.is_blocked = True
            state.block_reason = "invalid_query_structure"
            return state

        if "table" not in plan or "select" not in plan:
            state.is_blocked = True
            state.block_reason = "missing_required_fields"
            return state

        table = plan.get("table")
        select_items = plan.get("select", [])
        filters = plan.get("filters", [])
        limit = plan.get("limit", 10)

        # Table validation
        try:
            schema_text = get_schemas(state.domain)
        except Exception:
            state.is_blocked = True
            state.block_reason = "invalid_domain"
            return state

        allowed_tables = extract_allowed_tables(schema_text)
        if table not in allowed_tables:
            state.is_blocked = True
            state.block_reason = f"unauthorized_table:{table}"
            return state

        # SELECT validation
        if not isinstance(select_items, list):
            state.is_blocked = True
            state.block_reason = "invalid_select_structure"
            return state

        for item in select_items:
            if not isinstance(item, dict):
                state.is_blocked = True
                state.block_reason = "invalid_select_structure"
                return state
            if "aggregate" in item:
                if item["aggregate"].upper() not in self.ALLOWED_AGGREGATES:
                    state.is_blocked = True
                    state.block_reason = f"invalid_aggregate:{item['aggregate']}"
                    return state

        # FILTER validation
        if not isinstance(filters, list):
            state.is_blocked = True
            state.block_reason = "invalid_filter_structure"
            return state

        for f in filters:
            if not isinstance(f, dict):
                state.is_blocked = True
                state.block_reason = "invalid_filter_structure"
                return state

            operator = f.get("operator")
            if operator and operator.upper() not in self.ALLOWED_OPERATORS:
                state.is_blocked = True
                state.block_reason = f"invalid_operator:{operator}"
                return state

            if "param" in f and f["param"] not in self.ALLOWED_PARAMS:
                state.is_blocked = True
                state.block_reason = f"invalid_param:{f['param']}"
                return state

        # LIMIT validation
        if not isinstance(limit, int) or limit <= 0:
            state.is_blocked = True
            state.block_reason = "invalid_limit"
            return state

        if limit > self.MAX_LIMIT:
            plan["limit"] = self.MAX_LIMIT

        return state
