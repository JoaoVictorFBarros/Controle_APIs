import serial
import time
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread

porta_serial = '/dev/ttyUSB0'
taxa_de_baud = 9600 

try:
    ser = serial.Serial(porta_serial, taxa_de_baud, timeout=1)
    print(f"Conectado à porta {porta_serial}")
except serial.SerialException as e:
    print(f"Erro ao conectar à porta {porta_serial}: {e}")
    exit()

time.sleep(2)

modo_verboso = '-v' in sys.argv

# Constantes de normalização
NORMALIZACAO_P1 = 950.0
NORMALIZACAO_P2 = 510.0
NORMALIZACAO_P3 = 950.0


ultimo_potenciometro = [None, None, None]
ultima_tecla = None 


app = Flask(__name__)


CORS(app)


def armazenar_leitura(leitura):
    global ultimo_potenciometro, ultima_tecla

    if 'P1' in leitura and 'P2' in leitura and 'P3' in leitura:
        valores = leitura.split('|')
        p1 = (int(valores[0].strip().split(': ')[1]) / NORMALIZACAO_P1).__round__(2)
        p2 = (int(valores[1].strip().split(': ')[1]) / NORMALIZACAO_P2).__round__(2)
        p3 = (int(valores[2].strip().split(': ')[1]) / NORMALIZACAO_P3).__round__(2)
        ultimo_potenciometro = [p1, p2, p3]
    elif 'T:' in leitura:
        ultima_tecla = leitura.split(': ')[1].strip()

    if modo_verboso:
        print(f"Dado recebido: {leitura}")

def leitura_serial():
    while True:
        if ser.in_waiting > 0:
            try:
                linha = ser.readline().decode('utf-8', errors='ignore').rstrip()
                armazenar_leitura(linha)
            except UnicodeDecodeError as e:
                print(f"Erro de decodificação: {e}")
        else:
            time.sleep(0.05)

@app.route('/leituras', methods=['GET'])
def obter_leituras():
    global ultimo_potenciometro, ultima_tecla

    dados_para_enviar = {
        'P': ultimo_potenciometro,
        'T': ultima_tecla if ultima_tecla is not None else None
    }

    ultima_tecla = None

    return jsonify(dados_para_enviar)

if __name__ == '__main__':
    try:
        thread = Thread(target=leitura_serial)
        thread.daemon = True
        thread.start()
        
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("Interrupção pelo usuário. Fechando a conexão...")
    finally:
        ser.close()
        print("Conexão serial fechada.")
