def calculate_risk(payment):
    score = 0
    alerts = []

    if payment.amount > 1000:
        score += 50
        alerts.append("high_amount")

    if payment.country not in ["IE", "GB"]:
        score += 20
        alerts.append("foreign_country")

    if payment.merchant.lower() == "crypto":
        score += 30
        alerts.append("high_risk_merchant")

    return {
        "risk_score": score,
        "alerts": alerts
    }