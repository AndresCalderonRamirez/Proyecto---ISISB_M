"""
Vigía — Sensor de movimiento (MPU6050)
----------------------------------------
Lee el acelerómetro/giroscopio MPU6050 por I2C en el ESP32
y detecta si hubo un movimiento o inclinación sospechosa
mientras el sistema está "armado".

Conexión física (I2C):
    MPU6050 VCC -> 3V3
    MPU6050 GND -> GND
    MPU6050 SCL -> GPIO22  (puedes cambiar el pin)
    MPU6050 SDA -> GPIO21  (puedes cambiar el pin)
"""

from machine import Pin, I2C
import time
import math

# --------------------------------------------------------
# Configuración del sensor
# --------------------------------------------------------
MPU_ADDR = 0x68          # dirección I2C por defecto del MPU6050
PWR_MGMT_1 = 0x6B        # registro de "power management"
ACCEL_XOUT_H = 0x3B      # primer registro de datos del acelerómetro

# Umbral de sensibilidad: qué tanto se puede desviar la aceleración
# total (en "g") antes de considerarlo un movimiento sospechoso.
# 1.0 = quieto (solo gravedad). Ajusta este número probando en la moto/bici real.
UMBRAL_MOVIMIENTO = 0.35


class SensorMovimiento:
    def __init__(self, scl_pin=22, sda_pin=21):
        self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self._despertar_sensor()

    def _despertar_sensor(self):
        # El MPU6050 arranca "dormido" para ahorrar energía; hay que
        # escribir 0 en el registro de power management para activarlo.
        self.i2c.writeto_mem(MPU_ADDR, PWR_MGMT_1, b'\x00')
        time.sleep_ms(100)

    def _leer_word(self, registro):
        # Cada eje ocupa 2 bytes (High + Low) en complemento a dos.
        alto = self.i2c.readfrom_mem(MPU_ADDR, registro, 1)[0]
        bajo = self.i2c.readfrom_mem(MPU_ADDR, registro + 1, 1)[0]
        valor = (alto << 8) | bajo
        if valor > 32767:
            valor -= 65536
        return valor

    def leer_aceleracion_g(self):
        """Devuelve (ax, ay, az) en unidades de 'g' (1g = gravedad terrestre)."""
        ax = self._leer_word(ACCEL_XOUT_H)
        ay = self._leer_word(ACCEL_XOUT_H + 2)
        az = self._leer_word(ACCEL_XOUT_H + 4)
        # El sensor está configurado por defecto en el rango ±2g,
        # y esa escala equivale a 16384 unidades crudas por cada 1g.
        return (ax / 16384.0, ay / 16384.0, az / 16384.0)

    def magnitud_aceleracion(self):
        """Magnitud total del vector de aceleración, en g."""
        ax, ay, az = self.leer_aceleracion_g()
        return math.sqrt(ax * ax + ay * ay + az * az)

    def hay_movimiento_sospechoso(self, referencia=1.0):
        """
        Compara la aceleración actual contra el valor 'en reposo' (~1g).
        Devuelve True si la diferencia supera el umbral definido.
        """
        magnitud = self.magnitud_aceleracion()
        diferencia = abs(magnitud - referencia)
        return diferencia > UMBRAL_MOVIMIENTO


# --------------------------------------------------------
# Ejemplo de uso / prueba en consola
# --------------------------------------------------------
if __name__ == "__main__":
    sensor = SensorMovimiento(scl_pin=22, sda_pin=21)

    print("Calibrando... deja el vehículo quieto por 2 segundos.")
    time.sleep(2)

    while True:
        magnitud = sensor.magnitud_aceleracion()
        alerta = sensor.hay_movimiento_sospechoso()
        estado = "ALERTA: movimiento sospechoso" if alerta else "En reposo"
        print("Aceleración total: {:.2f} g  -> {}".format(magnitud, estado))
        time.sleep(0.3)