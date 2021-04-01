#include "stdio.h"
#include "microcode.h"

void generateCode(byte* data)
{
  //perfom all twice, once with first pin off, and duplicate when one
  for (word k = 0; k < 0b10; k++) {
    printf("\nCreating copy %d\n", k);
    word offset = k << 14;
    //write all the start code in the first few bytes of every instruction
    printf("Saving Start Code\n");
    word startSize = sizeof(startCode) / sizeof(byte);
    word leftOver = 0b10000 - startSize;
    for (word i = 0; i < 16384; i += 0b10000) {
      for (word j = 0; j < startSize; j++) {
        data[offset + i + j] = startCode[j];
      }

      //add a clear microinstruction for unused codes
      if (leftOver > 0)
        data[offset + i + startSize] = CLR;

      //fill the rest with empty no-op
      for (word j = startSize + 1; j < 0b10000; j++) {
        data[offset + i + j] = NOP;
      }
    }

    printf("Saving Base Code\n");
    //write the base condition 4 times,
    //to duplicate the code for all instructions regardless of flag
    word len = sizeof(base) / sizeof(Code);
    word location = 0;
    word size = 0;
    for (byte flag = 0; flag < 0b100; flag++) {
      for (word i = 0; i < len; i++) {
        location = offset | (flag << 12) | (base[i].instr << 4);
        size = base[i].size;
        size = size > leftOver ? leftOver : size;

        for (word j = 0; j < size; j++) {
          data[location + j + startSize] = base[i].code[j];
        }

        if (size != leftOver)
          data[location + size + startSize] = CLR;
      }
    }

    printf("Saving Carry Code\n");
    //write the Carry flag twice (carry flag and both flags),
    //to duplicate the code for all times the carry flag is up
    len = sizeof(flaggedCarry) / sizeof(Code);
    location = 0;
    size = 0;
    for (byte flag = 0b01; flag < 0b100; flag += 0b10) {
      for (word i = 0; i < len; i++) {
        location = offset | (flag << 12) | (flaggedCarry[i].instr << 4);
        size = flaggedCarry[i].size;
        size = size > leftOver ? leftOver : size;

        for (word j = 0; j < size; j++) {
          data[location + j + startSize] = flaggedCarry[i].code[j];
        }

        if (size != leftOver)
          data[location + size + startSize] = CLR;

        for (word j = size + 1; j < leftOver; j++) {
          data[location + j + startSize] = NOP;
        }
      }
    }

    printf("Saving Equal Code\n");
    //Write the Equal flag twice (equal flag and both flags),
    //to duplicate the code for all times the equal flag is up
    len = sizeof(flaggedEqual) / sizeof(Code);
    location = 0;
    size = 0;
    for (byte flag = 0b10; flag < 0b100; flag += 0b01) {
      for (word i = 0; i < len; i++) {
        location = offset | (flag << 12) | (flaggedEqual[i].instr << 4);
        size = flaggedEqual[i].size;
        size = size > leftOver ? leftOver : size;

        for (word j = 0; j < size; j++) {
          data[location + j + startSize] = flaggedEqual[i].code[j];
        }

        if (size != leftOver)
          data[location + size + startSize] = CLR;

        for (word j = size + 1; j < leftOver; j++) {
          data[location + j + startSize] = NOP;
        }
      }
    }

    printf("Saving Both Flags Code\n");
    //Write the Both flags once
    len = sizeof(flaggedBoth) / sizeof(Code);
    location = 0;
    size = 0;
    word flags = offset | (0b11 << 12);
    for (word i = 0; i < len; i++) {
      location = flags | (flaggedBoth[i].instr << 4);
      size = flaggedBoth[i].size;
      size = size > leftOver ? leftOver : size;

      for (word j = 0; j < size; j++) {
        data[location + j + startSize] = flaggedBoth[i].code[j];
      }

      if (size != leftOver)
        data[location + size + startSize] = CLR;

      for (word j = size + 1; j < leftOver; j++) {
        data[location + j + startSize] = NOP;
      }
    }
  }
}

void writeCode(byte* data)
{
  FILE* file = fopen("data.txt", "w");
  FILE* fileHuman = fopen("legible.txt", "w");

  for (word j = 0; j < 32768; j+= 0b1000000) {
    fprintf(file, "%04x: ", j);
    for (word i = 0; i < 0b1000000; i+= 0b10000) {
      fprintf(fileHuman, "%04x: %02x %02x %02x %02x  %02x %02x %02x %02x   %02x %02x %02x %02x  %02x %02x %02x %02x\n",
      j+i, data[j+i+0], data[j+i+1], data[j+i+2], data[j+i+3], data[j+i+4], data[j+i+5], data[j+i+6], data[j+i+7],
      data[j+i+8], data[j+i+9], data[j+i+10], data[j+i+11], data[j+i+12], data[j+i+13], data[j+i+14], data[j+i+15]);

      fprintf(file, "%02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x",
      data[j+i+0], data[j+i+1], data[j+i+2], data[j+i+3], data[j+i+4], data[j+i+5], data[j+i+6], data[j+i+7],
      data[j+i+8], data[j+i+9], data[j+i+10], data[j+i+11], data[j+i+12], data[j+i+13], data[j+i+14], data[j+i+15]);

      if (i != 0b110000) fprintf(file, " ");
      if (i == 0b010000) fprintf(file, " ");

      // printf(buf);
    }
    fprintf(file, "\n");
  }

  fclose(file);
  fclose(fileHuman);
}

int main()
{
  byte data[32768];

  generateCode(data);
  writeCode(data);
}
