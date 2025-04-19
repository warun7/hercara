import pigpio
import time

# GPIO pin to use for output (matches your setup)
PPM_GPIO = 18

# Create pigpio instance
pi = pigpio.pi()
if not pi.connected:
    print("Cannot connect to pigpio daemon. Is it running?")
    exit()

# Set GPIO 18 as output
pi.set_mode(PPM_GPIO, pigpio.OUTPUT)

# Function to generate a PWM pulse (in microseconds)
def send_pwm(pulse_width_us):
    pi.set_servo_pulsewidth(PPM_GPIO, pulse_width_us)

try:
    print("Sending PWM signals to Pixhawk...")
    while True:
        for pwm in range(1000, 2001, 250):  # 1000 → 1250 → 1500 → 1750 → 2000
            print(f"Sending {pwm}µs pulse")
            send_pwm(pwm)
            time.sleep(1)  # Wait a second between changes

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Cleanup
    pi.set_servo_pulsewidth(PPM_GPIO, 0)
    pi.stop()
