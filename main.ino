#include <Keypad.h>

// Definição do teclado matricial
const byte linhas = 4;  // Número de linhas no teclado
const byte colunas = 4; // Número de colunas no teclado

// Mapeamento das portas digitais para as linhas e colunas do teclado
byte pinosLinhas[linhas] = {2, 3, 4, 5};  // Pinos digitais conectados às linhas do teclado
byte pinosColunas[colunas] = {6, 7, 8, 9}; // Pinos digitais conectados às colunas do teclado

// Definição dos caracteres das teclas do teclado
char teclas[linhas][colunas] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

// Inicialização do objeto Keypad
Keypad teclado = Keypad(makeKeymap(teclas), pinosLinhas, pinosColunas, linhas, colunas);

void setup() {
  Serial.begin(9600);  // Inicializa a comunicação serial a 9600 bps
}

void loop() {
  // Lê os valores dos potenciômetros nas portas A0, A1 e A2
  int valorPotenciometro1 = analogRead(A0);
  int valorPotenciometro2 = analogRead(A1);
  int valorPotenciometro3 = analogRead(A2);

  // Imprime os valores lidos dos potenciômetros na porta serial
  Serial.print("P1: ");
  Serial.print(valorPotenciometro1);
  Serial.print(" | P2: ");
  Serial.print(valorPotenciometro2);
  Serial.print(" | P3: ");
  Serial.println(valorPotenciometro3);

  // Lê a tecla pressionada no teclado matricial
  char teclaPressionada = teclado.getKey();

  // Se uma tecla foi pressionada, imprime o valor da tecla
  if (teclaPressionada) {
    Serial.print("T: ");
    Serial.println(teclaPressionada);
  }

  delay(50);  // Aguarda 50 ms antes de fazer a próxima leitura
}
