from flask import Flask, request, jsonify
from flask_cors import CORS
import control as ctrl 
import matplotlib.pyplot as plt
import math as m
import numpy as np

app = Flask(__name__)
CORS(app) 

# Cria o controlador:
def controler(Kp = 1, Ki = 0, Kd = 0, type = 'P', T = None):
    if type == 'P':
        control = ctrl.TransferFunction([Kp], [1], T)
    elif type == 'PI':
        if T is None:
            control = ctrl.TransferFunction([Kp, Ki], [1, 0])
        else:
            T = float(T)
            p = ctrl.TransferFunction([Kp], [1], T)
            i = ctrl.TransferFunction([Ki*T, Ki*T], [2, -2], T)
            control = ctrl.parallel(p, i)
    elif type == 'PD':
        if T is None:
            control = ctrl.TransferFunction([Kd, Kp], [1])
        else:
            T = float(T)
            p = ctrl.TransferFunction([Kp], [1], T)
            d = ctrl.TransferFunction([Kd, -Kd],[T, 0], T)
            control = ctrl.parallel(p, d)
    elif type == 'PID':
        if T is None:
            control = ctrl.TransferFunction([Kd, Kp, Ki],[1, 0])
        else:
           T = float(T)
           p = ctrl.TransferFunction([Kp], [1], T)
           i = ctrl.TransferFunction([Ki*T, Ki*T], [2, -2], T)
           d = ctrl.TransferFunction([Kd, -Kd],[T, 0], T)
           control = ctrl.parallel(p, i, d) 
    
    return control

# Cria a função de primeira ordem:
def firstOrder(K=1, tau=1, T=None):
    system = ctrl.TransferFunction([K], [tau, 1])
    if T is not None:
        T = float(T)
        system = ctrl.sample_system(system, T, method='zoh')
    return system

# Cria a função de segunda ordem
def secondOrder(Ksi=1, Omn=1, T=None):
    Ksi = float(Ksi)
    Omn = float(Omn)
    system = ctrl.TransferFunction([Omn*Omn], [1, 2*Ksi*Omn, Omn*Omn])
    if T is not None:
        T = float(T)
        system = ctrl.sample_system(system, T, method='zoh')
    return system

def clean_transfer_function(tf_str):
    # Divida a string em linhas
    lines = tf_str.splitlines()
    
    # Filtrar as linhas que não são relevantes para a função de transferência
    cleaned_lines = [line.strip() for line in lines if line.strip() and not (
        line.startswith("Inputs") or line.startswith("Outputs") or 
        line.startswith("<") or line.startswith("dt"))]
    
    # A função de transferência deve ter pelo menos duas linhas: uma para o numerador e outra para o denominador
    numerador = cleaned_lines[0]
    denominador = cleaned_lines[2]
    return numerador, denominador

def replace_negative_infinity(value):
    return value if value != -np.inf else 0
    
def max_absolute_pole_zero(poles, zeros):
    poles = list(poles) if poles is not None else []
    zeros = list(zeros) if zeros is not None else []
    
    # Combine polos e zeros
    combined = poles + zeros
    
    if not combined:
        return {'x_max': 1, 'y_max': 1}
    
    # Obter o maior valor absoluto dos eixos real e imaginário
    x_max = max(abs(p.real) for p in combined) if combined else 1
    y_max = max(abs(p.imag) for p in combined) if combined else 1

    m = max(abs(x_max), abs(y_max))
    return m

@app.route('/graficos', methods=['POST'])
def dynsyn():
    data = request.json

    K = float(data['K'])
    tau = float(data['tau'])
    T = data['T']
    Kp = float(data['Kp'])
    Ki = float(data['Ki'])
    Kd = float(data['Kd'])
    type = data['type']
    Ksi = data['Ksi']
    Omn = data['Omn']

    if Ksi is None:
        system = firstOrder(K, tau, T)
    else:
        system = secondOrder(Ksi, Omn, T)

    control = controler(Kp, Ki, Kd, type, T)
    open_loop = ctrl.series(system, control)
    closed_loop = ctrl.feedback(open_loop, 1)

    # Informações Resposta degrau
    time, response = ctrl.step_response(closed_loop) # x: time, y: response
    step_response = {'time': time.tolist(), 'response': response.tolist()}

    # Informações LGR
    pzmap = ctrl.pzmap(open_loop, plot=False)
    if isinstance(pzmap, tuple) and len(pzmap) == 2:
        poles, zeros = pzmap
    else:
        # Ajustar conforme o retorno real
        poles = []
        zeros = []
        print("Unexpected pzmap return format")

    root_locus = {'poles': [(p.real, p.imag) for p in poles], 'zeros': [(z.real, z.imag) for z in zeros]}
    theta = np.linspace(0, 2 * np.pi, 361)  # 361 pontos para garantir que o círculo seja fechado
    unit_circle_x = np.cos(theta).tolist()
    unit_circle_y = np.sin(theta).tolist()
    max = max_absolute_pole_zero(poles, zeros)

    # Informações Diagrama de Bode
    mag, phase, omega = ctrl.bode(open_loop, plot=False)
    phase_degrees = [m.degrees(phase_i) for phase_i in phase]
    bode = {
        'magnitude': [20 * np.log10(val) if val > 0 else 0 for val in mag],  # y: magnitude (grafico de cima)
        'phase': phase_degrees, # y: phase
        'frequency': omega.tolist() # x: frequency msm coisa para os dois
    }

    system_num, system_den = clean_transfer_function(str(system))
    closed_num, closed_den = clean_transfer_function(str(closed_loop))
    
    return jsonify({
        'step_response': step_response,
        'root_locus': root_locus,
        'unit_circle': {'x': unit_circle_x, 'y': unit_circle_y},
        'bode': bode,
        'system': {'num': system_num, 'den': system_den}, # FT original
        'closed': {'num': closed_num, 'den': closed_den}, # FT controlada
        'max': max
    })

if __name__ == '__main__':
    app.run(port=5011, debug=True)
