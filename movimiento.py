from machine import Pin, I2C
import time
import math

MPU_ADDR = 0x68          
PWR_MGMT_1 = 0x6B       
ACCEL_XOUT_H = 0x3B      

UMBRAL_MOVIMIENTO = 0.15

UMBRAL_INCLINACION_GRADOS = 10

class SensorMovimiento:
    def __init__(self, scl_pin=22, sda_pin=21):
        self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self._despertar_sensor()
        self.referencia_pitch = None
        self.referencia_roll = None

    def _despertar_sensor(self):
        self.i2c.writeto_mem(MPU_ADDR, PWR_MGMT_1, b'\x00')
        time.sleep_ms(100)

    def _leer_word(self, registro):
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
