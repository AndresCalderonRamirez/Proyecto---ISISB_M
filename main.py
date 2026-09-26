from machine import Pin, Timer
import time
from movimiento import SensorMovimiento
from luz import SensorLuz

""" Configuracion del boton y led de estado"""

BOTON_PIN = 4
LED_PIN = 2
DEBOUNCE_MS = 250
PARPADEO_MS = 150

boton = Pin(BOTON_PIN, Pin.IN, Pin.PULL_DOWN)
led = Pin(LED_PIN, Pin.OUT)
timer_led = Timer(1)

armado = False
alerta = False
ultimo_click_ms = 0
led_encendido = False

led.value(0)


def alternar_armado(pin):
    """Se ejecuta automáticamente al presionar el botón (interrupción).
    Esto es lo que enciende/apaga TODO el sistema de forma voluntaria:
    cuando armado=False, VIGÍA no vigila ni evalúa alertas."""
    global armado, ultimo_click_ms

    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_click_ms) > DEBOUNCE_MS:
        armado = not armado
        ultimo_click_ms = ahora
        print("Sistema", "ARMADO" if armado else "DESARMADO")


def actualizar_led(t):
    """Se ejecuta automáticamente cada PARPADEO_MS ms (Timer).
    Encendido fijo = armado, apagado = desarmado, parpadeo = alerta."""
    global led_encendido

    if alerta:
        led_encendido = not led_encendido
        led.value(1 if led_encendido else 0)
    elif armado:
        led.value(1)
    else:
        led.value(0)


boton.irq(trigger=Pin.IRQ_RISING, handler=alternar_armado)
timer_led.init(period=PARPADEO_MS, mode=Timer.PERIODIC, callback=actualizar_led)

""" Iniciar sensores """
print("Iniciando sensores")
sensor_mov = SensorMovimiento(scl_pin=22, sda_pin=21)
sensor_luz = SensorLuz(pin_adc=34)

print("Presionar botón para encender o apagar el sistema.")

armado_anterior = False

while True:
    if armado and not armado_anterior:
        print("Calibrando fotoresistor con la luz actual...")
        try:
            sensor_luz.calibrar()
        except Exception as e:
            print("Error calibrando sensor de luz:", e)
        print("Sistema listo para vigilar.")

    armado_anterior = armado

    if armado:
        try:
            alerta_mov = sensor_mov.hay_movimiento_sospechoso()
        except Exception as e:
            print("Error leyendo sensor de movimiento:", e)
            alerta_mov = False

        try:
            alerta_luz = sensor_luz.hay_manipulacion_luz()
        except Exception as e:
            print("Error leyendo sensor de luz:", e)
            alerta_luz = False

        alerta = alerta_mov or alerta_luz

        if alerta:
            print("=== ALERTA ===  movimiento:", alerta_mov, "  luz:", alerta_luz)
        else:
            print("Vigilando... (accel: {:.2f} g, luz: {:.1f}%)".format(
                sensor_mov.magnitud_aceleracion(),
                sensor_luz.leer_porcentaje()
            ))
    else:
        alerta = False

    time.sleep_ms(300)
