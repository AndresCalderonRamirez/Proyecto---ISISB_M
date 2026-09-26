from machine import Pin, ADC
import time

PIN_ADC = 34  

UMBRAL_CAMBIO_LUZ = 30  

class SensorLuz:
    def __init__(self, pin_adc=PIN_ADC):
        self.adc = ADC(Pin(pin_adc))
        self.adc.atten(ADC.ATTN_11DB)   
        self.adc.width(ADC.WIDTH_12BIT)  
        self.referencia = None

    def leer_crudo(self):
        """Valor crudo del ADC, entre 0 (oscuro) y 4095 (muy iluminado)."""
        return self.adc.read()

    def leer_porcentaje(self):
        """Convierte la lectura cruda a un porcentaje de luz (0-100)."""
        return (self.leer_crudo() / 4095) * 100

    def calibrar(self, muestras=10, intervalo_ms=100):
        """
        Guarda el nivel de luz actual como referencia ('normal').
        Debe llamarse justo cuando el dueño arma el sistema, con
        el vehículo en su lugar habitual de estacionamiento.
        """
        total = 0
        for _ in range(muestras):
            total += self.leer_porcentaje()
            time.sleep_ms(intervalo_ms)
        self.referencia = total / muestras
        return self.referencia

    def hay_manipulacion_luz(self):
        """
        Compara la luz actual contra la referencia calibrada.
        Devuelve True si el cambio supera el umbral (lo taparon,
        o el vehículo ya no está en el mismo lugar/condición de luz).
        """
        if self.referencia is None:
            raise RuntimeError("Primero debes llamar a calibrar()")

        actual = self.leer_porcentaje()
        diferencia = abs(actual - self.referencia)
        return diferencia > UMBRAL_CAMBIO_LUZ


