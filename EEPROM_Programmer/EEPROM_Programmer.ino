#define PIN_CLK     4
#define PIN_LATCH   3
#define PIN_SERIAL  2

#define PIN_D0      5
#define PIN_D7      12
#define PIN_WE      13

bool isModeInput = true;

void setup() {
  // put your setup code here, to run once:
  pinMode(PIN_CLK, OUTPUT);
  pinMode(PIN_LATCH, OUTPUT);
  pinMode(PIN_SERIAL, OUTPUT);
  digitalWrite(PIN_LATCH, LOW);

  digitalWrite(PIN_WE, HIGH);
  pinMode(PIN_WE, OUTPUT);

  Serial.begin(115200);

  setValueMode(false);
//  byte data[] = {0x11, 0x02, 0x03, 0x04, 0x65, 0x08, 0x08, 0x08};
//  word pageAddr = 0x300 >> 6;
//  writePage(pageAddr, data, 8);
//  writeByte(0x0f, 0x86);
//  writeByte(0xff, 0xea);
//  delay(1000);
  
//  flushContent(0x0, 0x1fff);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0) {
    word pageAddr;
    byte data[64];
    bool success;

    parseInstruction(data, &pageAddr, &success);
    if (!success) return;
    
    pageAddr = pageAddr >> 6;
    
    writePage(pageAddr, data);
    
    delay(15);

    Serial.println("DONE");
    
//    flushContent(pageAddr << 6, (pageAddr << 6) + 63);
  }
}

void parseInstruction(byte* buf, word* addr, bool* success) {
  String message = Serial.readString();

//  Serial.println(message.c_str());

  if (message.c_str()[0] == 'p') {
    word start;
    word ending;

    sscanf(message.c_str(), "p %x %x", &start, &ending);

    flushContent(start, ending);

    *success = false;

    return;
  }

  word data[32];
  sscanf(message.c_str(), "%x: %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x  %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x",
    addr, data, data+1, data+2, data+3, data+4, data+5, data+6, data+7,
    data+8, data+9, data+10, data+11, data+12, data+13, data+14, data+15,
    data+16, data+17, data+18, data+19, data+20, data+21, data+22, data+23,
    data+24, data+25, data+26, data+27, data+28, data+29, data+30, data+31);

  for (int i = 0; i < 32; i++) {
    buf[2*i + 1] = data[i] & 0xff;
    buf[2*i] = data[i] >> 8;
  }

  *success = true;
}

void setValueMode(bool isInput) {
  if (isInput == isModeInput)
    return;
    
  for (int i = PIN_D0; i <= PIN_D7; i++) {
    pinMode(i, isInput ? INPUT : OUTPUT);
  }

  isModeInput = isInput;
}

void sendSerial(word data) {
  shiftOut(PIN_SERIAL, PIN_CLK, MSBFIRST, data >> 8);
  shiftOut(PIN_SERIAL, PIN_CLK, MSBFIRST, data);

  digitalWrite(PIN_LATCH, HIGH);
  digitalWrite(PIN_LATCH, LOW);
}

byte readByte(word address) {
  //setup value pins as input
  setValueMode(true);
  
  //send address and output enable (0)
  sendSerial(address);
  
  //read value
  byte value = 0;
  for (int i = PIN_D7; i >= PIN_D0; i--) {
    value = (value << 1) + digitalRead(i);
  }

  //return value
  return value;
}

void writeByte(word address, byte value) {
  
  //send address and output enable
  word data = 0x8000 + address;
  sendSerial(data);
  
  //send value
  for (int i = PIN_D0; i <= PIN_D7; i++) {
    digitalWrite(i, value & 1);
    value = value >> 1;
  }

  //pulse write enable
  digitalWrite(PIN_WE, HIGH);
  digitalWrite(PIN_WE, LOW);
  delayMicroseconds(1);
  digitalWrite(PIN_WE, HIGH);
  
}

void writePage(word page, byte* values) {
  writePage(page, 0x00, values, 0x40);
}

void writePage(word page, byte* values, byte len) {
  writePage(page, 0x00, values, len);
}

void writePage(word page, word start, byte* values, byte len) {
  //setup value mode as output
  setValueMode(false);
  
  len = len > 64 ? 64 : len;
  word beginning = (page << 6) + start;
  for (word i = 0; i < len; i++) {
    writeByte(beginning + i, values[i]); 
  }
}

void flushContent(word start, word ending) {
  Serial.println("");
  for (int i = start; i <= ending; i += 16) {
    byte data[16];
    for (int j = 0; j < 16; j++) {
      data[j] = readByte(i + j);
    }

    char buf[80];
    sprintf(buf, "%04x: %02x %02x %02x %02x  %02x %02x %02x %02x   %02x %02x %02x %02x  %02x %02x %02x %02x",
    i, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
    data[8], data[9], data[10], data[11], data[12], data[13], data[14], data[15]);

    Serial.println(buf);
  }
  Serial.println("END");
}
