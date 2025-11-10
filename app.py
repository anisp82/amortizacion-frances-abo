from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def calculate_monthly_payment(principal, monthly_rate, term):
    """Calcula la cuota mensual fija con el método francés."""
    if monthly_rate <= 0:
        return round(principal / term, 0)
    numerator = principal * monthly_rate * (1 + monthly_rate) ** term
    denominator = (1 + monthly_rate) ** term - 1
    return round(numerator / denominator, 0)

def generate_amortization_table(principal, annual_rate, term_months):
    """Genera la tabla de amortización con ajuste en la última cuota."""
    monthly_rate = (annual_rate / 100) / 12
    monthly_payment = calculate_monthly_payment(principal, monthly_rate, term_months)
    
    table = []
    balance = principal
    total_interest = 0

    for month in range(1, term_months + 1):
        if balance <= 0:
            break
        interest = balance * monthly_rate
        amortization = monthly_payment - interest
        
        # Ajuste en la última cuota
        if amortization > balance:
            amortization = balance
            monthly_payment = interest + amortization
        
        new_balance = balance - amortization
        total_interest += interest

        table.append({
            "mes": month,
            "cuota": round(monthly_payment, 0),
            "interes": round(interest, 0),
            "amortizacion": round(amortization, 0),
            "saldo": round(new_balance, 0)
        })
        balance = new_balance

    return {
        "tabla": table,
        "cuota_mensual": round(monthly_payment, 0),
        "interes_total": round(total_interest, 0),
        "costo_total": round(sum(row["cuota"] for row in table), 0)
    }

@app.route('/')
def index():
    # No usamos 'now' para evitar errores; la fecha se maneja en el frontend
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos. Por favor, recargue la página."}), 400

        # Validar campos obligatorios
        required = ['loanAmount', 'initialPayment', 'loanTerm', 'interestRate']
        for field in required:
            if field not in data or str(data[field]).strip() == '':
                return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

        # Convertir y validar números
        try:
            loan_amount = float(data['loanAmount'])
            initial_payment = float(data['initialPayment'])
            loan_term = int(data['loanTerm'])
            interest_rate = float(data['interestRate'])
        except (ValueError, TypeError):
            return jsonify({"error": "Por favor, ingrese valores numéricos válidos."}), 400

        # Validar rangos
        if loan_amount <= 0:
            return jsonify({"error": "El valor de la venta debe ser mayor a $0."}), 400
        if initial_payment < 0:
            return jsonify({"error": "La cuota inicial no puede ser negativa."}), 400
        if initial_payment >= loan_amount:
            return jsonify({"error": "La cuota inicial debe ser menor al valor de la venta."}), 400
        if loan_term <= 0:
            return jsonify({"error": "El plazo debe ser al menos 1 mes."}), 400
        if interest_rate < 0:
            return jsonify({"error": "La tasa de interés no puede ser negativa."}), 400

        principal = loan_amount - initial_payment
        result = generate_amortization_table(principal, interest_rate, loan_term)

        # ✅ CORRECTO: True con mayúscula (Python)
        return jsonify({
            "success": True,
            "result": {
                "client": data.get("client", "").strip(),
                "invoice": data.get("invoiceNumber", "").strip(),
                "salesperson": data.get("salesperson", "").strip(),
                "loan_amount": loan_amount,
                "initial_payment": initial_payment,
                "principal": principal,
                "term": loan_term,
                "annual_rate": interest_rate,
                "cuota_mensual": result["cuota_mensual"],
                "interes_total": result["interes_total"],
                "costo_total": result["costo_total"],
                "tabla": result["tabla"]
            }
        })

    except Exception as e:
        # Nunca devuelvas HTML aquí
        print("⚠️ Error en /calcular:", str(e))
        return jsonify({"error": "Error interno. Por favor, intente más tarde."}), 500

if __name__ == '__main__':
    app.run(debug=True)