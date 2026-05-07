#include <ESP32Servo.h>

// ==================== CONFIGURATION ====================
Servo myServo;
const int SERVO_PIN = 0;

const int POS_HOME    = 87;
const int POS_PLASTIC = 22;
const int POS_PAPER   = 140;
const int MIN_ANGLE   = 0;
const int MAX_ANGLE   = 180;
int SERVO_SPEED       = 8;

// ==================== VARIABLES ====================
int currentAngle = POS_HOME;
unsigned long lastMoveTime = 0;
const unsigned long MOVE_DELAY    = 500;
const unsigned long RETURN_DELAY  = 2000;
bool isReturning = false;

// ==================== SETUP ====================
void setup() {
    Serial.begin(9600);
    myServo.attach(SERVO_PIN);
    myServo.write(POS_HOME);
    currentAngle = POS_HOME;
    delay(500);
    Serial.println("READY - HOME POSITION");
}

// ==================== SMOOTH MOVEMENT ====================
void moveSmoothly(int targetAngle) {
    targetAngle = constrain(targetAngle, MIN_ANGLE, MAX_ANGLE);
    
    if (targetAngle == currentAngle) {
        Serial.print("ALREADY_AT:");
        Serial.println(targetAngle);
        return;
    }
    
    Serial.print("MOVING:");
    Serial.print(currentAngle);
    Serial.print("->");
    Serial.println(targetAngle);
    
    if (targetAngle > currentAngle) {
        for (int pos = currentAngle; pos <= targetAngle; pos++) {
            myServo.write(pos);
            delay(SERVO_SPEED);
        }
    } else {
        for (int pos = currentAngle; pos >= targetAngle; pos--) {
            myServo.write(pos);
            delay(SERVO_SPEED);
        }
    }
    
    currentAngle = targetAngle;
    
    if (targetAngle == POS_PLASTIC) Serial.println("STATE:PLASTIC");
    else if (targetAngle == POS_PAPER)   Serial.println("STATE:PAPER");
    else if (targetAngle == POS_HOME)    Serial.println("STATE:HOME");
}

// ==================== AUTO RETURN TO HOME ====================
void returnToHome() {
    if (currentAngle != POS_HOME && !isReturning) {
        isReturning = true;
        Serial.println("RETURNING_TO_HOME");
        delay(RETURN_DELAY);
        moveSmoothly(POS_HOME);
        isReturning = false;
        lastMoveTime = millis();
    }
}

// ==================== MAIN LOOP ====================
void loop() {
    // Auto return to HOME after detection
    if ((currentAngle == POS_PLASTIC || currentAngle == POS_PAPER) && !isReturning) {
        if (millis() - lastMoveTime > RETURN_DELAY) {
            returnToHome();
        }
    }
    
    // Read number from serial
    if (Serial.available() > 0) {
        int target = Serial.parseInt();
        
        // Clear buffer
        while (Serial.available() > 0) {
            Serial.read();
        }
        
        if (isReturning) {
            Serial.println("BUSY:RETURNING");
            return;
        }
        
        // Map numbers to positions
        // Python sends: 0=home, 22=plastic, 140=paper
        int finalTarget = -1;
        
        if (target == 0) {
            finalTarget = POS_HOME;
            Serial.println("CMD:HOME");
        } else if (target == 22) {
            finalTarget = POS_PLASTIC;
            Serial.println("CMD:PLASTIC");
        } else if (target == 140) {
            finalTarget = POS_PAPER;
            Serial.println("CMD:PAPER");
        } else {
            Serial.print("INVALID:");
            Serial.println(target);
            return;
        }
        
        // Rate limiting (except HOME)
        if (finalTarget != POS_HOME && millis() - lastMoveTime < MOVE_DELAY) {
            Serial.println("BUSY:RATE_LIMIT");
            return;
        }
        
        moveSmoothly(finalTarget);
        lastMoveTime = millis();
    }
}