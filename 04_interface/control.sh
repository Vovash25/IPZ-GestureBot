#!/bin/bash
# control.sh
# Controls Jetson Nano fan based on temperature

# Configuration
FAN_PWM_PIN=0  # PWM channel (usually 0 for Jetson Nano)
MIN_TEMP=40    # Minimum temperature to start fan (Celsius)
MAX_TEMP=70    # Temperature at which fan runs at maximum speed (Celsius)
FAN_OFF_TEMP=35 # Temperature below which fan turns off
CHECK_INTERVAL=5 # Check interval in seconds

# Function to get current CPU temperature
get_temp() {
    # Read temperature from thermal zone
    cat /sys/devices/virtual/thermal/thermal_zone0/temp | awk '{print $1/1000}'
}

# Function to calculate PWM value based on temperature
calculate_pwm() {
    local temp=$1
    local pwm
    
    if (( $(echo "$temp < $FAN_OFF_TEMP" | bc -l) )); then
        pwm=0
    elif (( $(echo "$temp < $MIN_TEMP" | bc -l) )); then
        # Linear interpolation between off and minimum
        pwm=$(echo "scale=0; (($temp - $FAN_OFF_TEMP) * 100) / ($MIN_TEMP - $FAN_OFF_TEMP)" | bc)
    elif (( $(echo "$temp > $MAX_TEMP" | bc -l) )); then
        pwm=255
    else
        # Linear interpolation between min and max
        pwm=$(echo "scale=0; 100 + (($temp - $MIN_TEMP) * 155) / ($MAX_TEMP - $MIN_TEMP)" | bc)
    fi
    
    # Ensure pwm is between 0 and 255
    if (( pwm < 0 )); then pwm=0; fi
    if (( pwm > 255 )); then pwm=255; fi
    
    echo $pwm
}

# Function to set fan speed
set_fan_speed() {
    local pwm=$1
    echo $pwm > /sys/devices/pwm-fan/target_pwm
}

# Main control loop
echo "Starting Jetson Nano Fan Control"
echo "Temperature range: ${FAN_OFF_TEMP}°C (off) to ${MAX_TEMP}°C (max)"
echo "Press Ctrl+C to stop"

while true; do
    temp=$(get_temp)
    pwm=$(calculate_pwm $temp)
    
    # Only update if different from last value (optional optimization)
    if [[ $pwm != $last_pwm ]]; then
        set_fan_speed $pwm
        last_pwm=$pwm
        echo "$(date): Temp=${temp}°C, PWM=${pwm}/255"
    fi
    
    sleep $CHECK_INTERVAL
done
