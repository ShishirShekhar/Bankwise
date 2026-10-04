from app.calculators.fd import calculate_fd


result = calculate_fd(
    principal=500000,
    annual_rate=7.10,
    tenure_months=24,
    compounding_frequency=4,
)

print(result)