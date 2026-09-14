#include <Wire.h>
#include <U8g2lib.h>

// =====================================================
// OLED
// =====================================================
U8G2_SSD1306_128X64_NONAME_1_HW_I2C oled(
  U8G2_R0,
  U8X8_PIN_NONE
);

// =====================================================
// PINS
// =====================================================
#define RED_LED    2
#define BLUE_LED   3
#define WHITE_LED  4

#define SPEAKER_PIN 6

// L298N
#define ENA 5
#define IN1 7
#define IN2 8

// =====================================================
// PAGES
// =====================================================
#define PAGE_LOGIN    0
#define PAGE_MENU     1
#define PAGE_LED      2
#define PAGE_MOTOR    3
#define PAGE_MUSIC    4
#define PAGE_SETTINGS 5
#define PAGE_STATUS   6

int currentPage = PAGE_LOGIN;

// =====================================================
// STATES
// =====================================================
bool redState = false;
bool blueState = false;
bool whiteState = false;

int motorSpeed = 0;

// =====================================================
// SERIAL
// =====================================================
String serialCommand = "";

// =====================================================
// MOTOR
// =====================================================
const int MIN_PWM = 45;

void setMotorSpeed(int speedPercent) {

  speedPercent = constrain(speedPercent, 0, 100);
  motorSpeed = speedPercent;

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  int pwmValue = 0;

  if (speedPercent > 0) {

    pwmValue = map(
      speedPercent,
      1,
      100,
      MIN_PWM,
      255
    );

    pwmValue = constrain(
      pwmValue,
      MIN_PWM,
      255
    );
  }

  analogWrite(
    ENA,
    pwmValue
  );
}

void stopMotor() {

  motorSpeed = 0;

  analogWrite(
    ENA,
    0
  );
}

// =====================================================
// MUSIC
// =====================================================

#define NOTE_C4  262
#define NOTE_D4  294
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_G4  392
#define NOTE_A4  440
#define NOTE_B4  494
#define NOTE_C5  523

int melody[] = {

  NOTE_C4,
  NOTE_C4,
  NOTE_G4,
  NOTE_G4,

  NOTE_A4,
  NOTE_A4,
  NOTE_G4,

  NOTE_F4,
  NOTE_F4,
  NOTE_E4,
  NOTE_E4,

  NOTE_D4,
  NOTE_D4,
  NOTE_C4
};

int durations[] = {

  400,
  400,
  400,
  400,

  400,
  400,
  800,

  400,
  400,
  400,
  400,

  400,
  400,
  800
};

const int numberOfNotes =
  sizeof(melody) / sizeof(melody[0]);

int currentNote = 0;

bool musicPlaying = false;

unsigned long noteStartTime = 0;

void startMusic() {

  if (!musicPlaying) {

    musicPlaying = true;

    currentNote = 0;

    noteStartTime = millis();

    tone(
      SPEAKER_PIN,
      melody[currentNote]
    );
  }
}

void stopMusic() {

  musicPlaying = false;

  noTone(
    SPEAKER_PIN
  );

  currentNote = 0;
}

void updateMusic() {

  if (!musicPlaying) {
    return;
  }

  unsigned long now = millis();

  if (
    now - noteStartTime >=
    durations[currentNote]
  ) {

    noTone(
      SPEAKER_PIN
    );

    delay(50);

    currentNote++;

    if (
      currentNote >= numberOfNotes
    ) {

      currentNote = 0;
    }

    tone(
      SPEAKER_PIN,
      melody[currentNote]
    );

    noteStartTime = millis();
  }
}

// =====================================================
// SEND STATES
// =====================================================

void sendStates() {

  Serial.print("STATE:RED:");
  Serial.println(
    redState ? "ON" : "OFF"
  );

  Serial.print("STATE:BLUE:");
  Serial.println(
    blueState ? "ON" : "OFF"
  );

  Serial.print("STATE:WHITE:");
  Serial.println(
    whiteState ? "ON" : "OFF"
  );

  Serial.print("STATE:SPEED:");
  Serial.println(
    motorSpeed
  );

  Serial.print("STATE:MUSIC:");
  Serial.println(
    musicPlaying ? "PLAYING" : "STOPPED"
  );

  Serial.println(
    "STATE:ONLINE:1"
  );
}

// =====================================================
// LOGIN PAGE
// =====================================================

void drawLoginPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      10,
      "TOUCHLESS LOGIN"
    );

    oled.drawStr(
      10,
      25,
      "SYSTEM READY"
    );

    oled.drawStr(
      10,
      39,
      "USER: READY"
    );

    oled.drawStr(
      10,
      53,
      "PASS: ****"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// MAIN MENU
// =====================================================

void drawMenuPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      9,
      "MAIN MENU"
    );

    oled.drawStr(
      10,
      21,
      "LED MANAGEMENT"
    );

    oled.drawStr(
      10,
      33,
      "MOTOR SPEED"
    );

    oled.drawStr(
      10,
      45,
      "MUSIC"
    );

    oled.drawStr(
      10,
      57,
      "SETTINGS"
    );

    oled.drawStr(
      90,
      57,
      "QUIT"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// LED PAGE
// =====================================================

void drawLedPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      10,
      "LED MANAGEMENT"
    );

    oled.drawStr(
      10,
      25,
      redState
        ? "RED   : ON"
        : "RED   : OFF"
    );

    oled.drawStr(
      10,
      38,
      blueState
        ? "BLUE  : ON"
        : "BLUE  : OFF"
    );

    oled.drawStr(
      10,
      51,
      whiteState
        ? "WHITE : ON"
        : "WHITE : OFF"
    );

    oled.drawStr(
      10,
      63,
      "BACK"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// MOTOR PAGE
// =====================================================

void drawMotorPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      10,
      "MOTOR SPEED"
    );

    oled.setCursor(
      10,
      23
    );

    oled.print(
      motorSpeed
    );

    oled.print(
      " km/h"
    );

    int barX = 10;
    int barY = 31;
    int barW = 108;
    int barH = 10;

    oled.drawFrame(
      barX,
      barY,
      barW,
      barH
    );

    int fillW = map(
      motorSpeed,
      0,
      100,
      0,
      barW - 2
    );

    if (fillW > 0) {

      oled.drawBox(
        barX + 1,
        barY + 1,
        fillW,
        barH - 2
      );
    }

    oled.drawStr(
      10,
      51,
      "0"
    );

    oled.drawStr(
      103,
      51,
      "100"
    );

    oled.drawStr(
      10,
      63,
      "BACK"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// MUSIC PAGE
// =====================================================

void drawMusicPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      10,
      "MUSIC"
    );

    oled.drawStr(
      10,
      25,
      musicPlaying
        ? "STATUS: PLAYING"
        : "STATUS: STOPPED"
    );

    oled.drawStr(
      10,
      39,
      "PLAY"
    );

    oled.drawStr(
      65,
      39,
      "STOP"
    );

    oled.drawStr(
      10,
      53,
      "NEXT"
    );

    oled.drawStr(
      65,
      53,
      "BACK"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// SETTINGS PAGE
// =====================================================

void drawSettingsPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      10,
      "SETTINGS"
    );

    oled.drawStr(
      10,
      27,
      "SYSTEM STATUS"
    );

    oled.drawStr(
      10,
      43,
      "MUSIC SETTINGS"
    );

    oled.drawStr(
      10,
      60,
      "BACK"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// STATUS PAGE
// =====================================================

void drawStatusPage() {

  oled.firstPage();

  do {

    oled.setFont(
      u8g2_font_6x10_tf
    );

    oled.drawStr(
      10,
      10,
      "SYSTEM STATUS"
    );

    oled.drawStr(
      10,
      23,
      redState
        ? "RED   : ON"
        : "RED   : OFF"
    );

    oled.drawStr(
      10,
      35,
      blueState
        ? "BLUE  : ON"
        : "BLUE  : OFF"
    );

    oled.drawStr(
      10,
      47,
      whiteState
        ? "WHITE : ON"
        : "WHITE : OFF"
    );

    oled.setCursor(
      10,
      59
    );

    oled.print(
      "MOTOR:"
    );

    oled.print(
      motorSpeed
    );

    oled.print(
      "% "
    );

    oled.print(
      musicPlaying
        ? "M"
        : "-"
    );

  } while (
    oled.nextPage()
  );
}

// =====================================================
// OLED UPDATE
// =====================================================

void updateOLED() {

  if (
    currentPage == PAGE_LOGIN
  ) {
    drawLoginPage();
  }

  else if (
    currentPage == PAGE_MENU
  ) {
    drawMenuPage();
  }

  else if (
    currentPage == PAGE_LED
  ) {
    drawLedPage();
  }

  else if (
    currentPage == PAGE_MOTOR
  ) {
    drawMotorPage();
  }

  else if (
    currentPage == PAGE_MUSIC
  ) {
    drawMusicPage();
  }

  else if (
    currentPage == PAGE_SETTINGS
  ) {
    drawSettingsPage();
  }

  else if (
    currentPage == PAGE_STATUS
  ) {
    drawStatusPage();
  }
}

// =====================================================
// COMMAND PROCESSOR
// =====================================================

void processCommand(
  String cmd
) {

  cmd.trim();

  // ---------------------------------------------------
  // NAVIGATION
  // ---------------------------------------------------

  if (
    cmd == "LOGIN_PAGE"
  ) {

    currentPage = PAGE_LOGIN;

    updateOLED();

    return;
  }

  if (
    cmd == "LOGIN_OK"
  ) {

    currentPage = PAGE_MENU;

    updateOLED();

    return;
  }

  if (
    cmd == "MENU_PAGE"
  ) {

    currentPage = PAGE_MENU;

    updateOLED();

    return;
  }

  if (
    cmd == "LED_PAGE"
  ) {

    currentPage = PAGE_LED;

    updateOLED();

    return;
  }

  if (
    cmd == "MOTOR_PAGE"
  ) {

    currentPage = PAGE_MOTOR;

    updateOLED();

    return;
  }

  if (
    cmd == "MUSIC_PAGE"
  ) {

    currentPage = PAGE_MUSIC;

    updateOLED();

    return;
  }

  if (
    cmd == "SETTINGS_PAGE"
  ) {

    currentPage = PAGE_SETTINGS;

    updateOLED();

    return;
  }

  if (
    cmd == "STATUS_PAGE"
  ) {

    currentPage = PAGE_STATUS;

    updateOLED();

    return;
  }

  if (
    cmd == "BACK"
  ) {

    currentPage = PAGE_MENU;

    updateOLED();

    return;
  }

  // ---------------------------------------------------
  // MUSIC
  // ---------------------------------------------------

  if (
    cmd == "PLAY"
  ) {

    startMusic();

    sendStates();

    updateOLED();

    return;
  }

  if (
    cmd == "STOP_MUSIC"
  ) {

    stopMusic();

    sendStates();

    updateOLED();

    return;
  }

  if (
    cmd == "NEXT"
  ) {

    currentNote++;

    if (
      currentNote >= numberOfNotes
    ) {
      currentNote = 0;
    }

    if (musicPlaying) {

      noTone(
        SPEAKER_PIN
      );

      tone(
        SPEAKER_PIN,
        melody[currentNote]
      );

      noteStartTime = millis();
    }

    sendStates();

    updateOLED();

    return;
  }

  // ---------------------------------------------------
  // RED
  // ---------------------------------------------------

  if (
    cmd == "RED:ON"
  ) {

    redState = true;

    digitalWrite(
      RED_LED,
      HIGH
    );

    sendStates();

    updateOLED();

    return;
  }

  if (
    cmd == "RED:OFF"
  ) {

    redState = false;

    digitalWrite(
      RED_LED,
      LOW
    );

    sendStates();

    updateOLED();

    return;
  }

  // ---------------------------------------------------
  // BLUE
  // ---------------------------------------------------

  if (
    cmd == "BLUE:ON"
  ) {

    blueState = true;

    digitalWrite(
      BLUE_LED,
      HIGH
    );

    sendStates();

    updateOLED();

    return;
  }

  if (
    cmd == "BLUE:OFF"
  ) {

    blueState = false;

    digitalWrite(
      BLUE_LED,
      LOW
    );

    sendStates();

    updateOLED();

    return;
  }

  // ---------------------------------------------------
  // WHITE
  // ---------------------------------------------------

  if (
    cmd == "WHITE:ON"
  ) {

    whiteState = true;

    digitalWrite(
      WHITE_LED,
      HIGH
    );

    sendStates();

    updateOLED();

    return;
  }

  if (
    cmd == "WHITE:OFF"
  ) {

    whiteState = false;

    digitalWrite(
      WHITE_LED,
      LOW
    );

    sendStates();

    updateOLED();

    return;
  }

  // ---------------------------------------------------
  // MOTOR
  // ---------------------------------------------------

  if (
    cmd.startsWith("SPEED:")
  ) {

    int value =
      cmd.substring(6).toInt();

    setMotorSpeed(
      value
    );

    sendStates();

    updateOLED();

    return;
  }

  if (
    cmd == "STOP"
  ) {

    stopMotor();

    sendStates();

    updateOLED();

    return;
  }

  // ---------------------------------------------------
  // STATE
  // ---------------------------------------------------

  if (
    cmd == "GET_STATE"
  ) {

    sendStates();

    return;
  }
}

// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(
    9600
  );

  pinMode(
    RED_LED,
    OUTPUT
  );

  pinMode(
    BLUE_LED,
    OUTPUT
  );

  pinMode(
    WHITE_LED,
    OUTPUT
  );

  pinMode(
    SPEAKER_PIN,
    OUTPUT
  );

  pinMode(
    ENA,
    OUTPUT
  );

  pinMode(
    IN1,
    OUTPUT
  );

  pinMode(
    IN2,
    OUTPUT
  );

  digitalWrite(
    RED_LED,
    LOW
  );

  digitalWrite(
    BLUE_LED,
    LOW
  );

  digitalWrite(
    WHITE_LED,
    LOW
  );

  digitalWrite(
    IN1,
    HIGH
  );

  digitalWrite(
    IN2,
    LOW
  );

  stopMotor();

  noTone(
    SPEAKER_PIN
  );

  oled.begin();

  updateOLED();

  delay(300);

  sendStates();
}

// =====================================================
// LOOP
// =====================================================

void loop() {

  updateMusic();

  while (
    Serial.available() > 0
  ) {

    char c =
      Serial.read();

    if (
      c == '\n'
    ) {

      if (
        serialCommand.length() > 0
      ) {

        processCommand(
          serialCommand
        );

        serialCommand = "";
      }
    }

    else if (
      c != '\r'
    ) {

      serialCommand += c;
    }
  }
}