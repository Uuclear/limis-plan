"""业务编号生成 (日期+序列号 + 并发安全)"""
from datetime import date
from sqlalchemy import text

NUMBER_RULES = {
    "order":  {"prefix": "WT",   "fmt": "%Y%m",   "len": 4, "reset": "monthly"},
    "sample": {"prefix": "YP",   "fmt": "%Y%m%d", "len": 4, "reset": "daily"},
    "report": {"prefix": "REP",  "fmt": "%Y",     "len": 4, "reset": "yearly"},
    "task":   {"prefix": "TK",   "fmt": "%Y%m",   "len": 4, "reset": "monthly"},
}

def generate_number(db, rule_name: str) -> str:
    rule = NUMBER_RULES[rule_name]
    now = date.today()
    period = now.strftime(rule["fmt"]) if rule["reset"] != "never" else "0"

    result = db.execute(text("""
        INSERT INTO system_number_sequences (rule_name, period, next_value)
        VALUES (:rule, :period, 2)
        ON CONFLICT (rule_name, period)
        DO UPDATE SET next_value = system_number_sequences.next_value + 1
        RETURNING next_value
    """), {"rule": rule_name, "period": period})

    next_val = result.scalar()
    return f"{rule['prefix']}-{period}-{next_val:0{rule['len']}d}"
