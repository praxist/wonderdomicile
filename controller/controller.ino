#include <OctoWS2811.h>
#include <EEPROM.h>

/***************************
User defines
***************************/
#define NUM_LEDS_PER_STRIP 143
#define NUM_STRIPS 8

#define FIRMWARE_VER 3
#define SERIALRATE 12000000 // Full USB 1.1 speed (native USB)

/***************************
OctoWS2811 Setup
***************************/
DMAMEM int display_memory[NUM_LEDS_PER_STRIP * 6];
int drawing_memory[NUM_LEDS_PER_STRIP * 6];
const int config = WS2811_GRB | WS2811_800kHz;

OctoWS2811 leds(NUM_LEDS_PER_STRIP, display_memory, drawing_memory, config); 

/***************************
BiblioPixel Setup
***************************/
namespace CMDTYPE
{
    enum CMDTYPE
    {
        SETUP_DATA = 1,
        PIXEL_DATA = 2,
        BRIGHTNESS = 3,
        GETID      = 4,
        SETID      = 5,
        GETVER     = 6
    };
}

namespace RETURN_CODES
{
    enum RETURN_CODES
    {
        SUCCESS = 255,
        REBOOT = 42,
        ERROR = 0,
        ERROR_SIZE = 1,
        ERROR_UNSUPPORTED = 2,
        ERROR_PIXEL_COUNT = 3,
        ERROR_BAD_CMD = 4,
    };
}

typedef struct __attribute__((__packed__))
{
  uint8_t type;
  uint16_t pixel_count;
  uint8_t spi_speed;
} config_t;

int rainbowColors[180];

inline void setup_leds()
{
    pinMode(1, OUTPUT);
    digitalWrite(1, HIGH);
    for (int i=0; i<180; i++) {
        int hue = i * 2;
        int saturation = 100;
        int lightness = 50;
        // pre-compute the 180 rainbow colors
        rainbowColors[i] = makeColor(hue, saturation, lightness);
    }
    digitalWrite(1, LOW);
    leds.begin();
}

void setup()
{   

    Serial.begin(SERIALRATE);
    Serial.setTimeout(1000);

    setup_leds();
}

inline void getData()
{
    static char cmd = 0;
    static uint16_t size = 0;

    if (Serial.available())
    {
        cmd = Serial.read();
        size = 0;
        Serial.readBytes((char*)&size, 2);

        if (cmd == CMDTYPE::PIXEL_DATA)
        {
            Serial.readBytes(((char*)&leds), size);         
            uint8_t resp = RETURN_CODES::SUCCESS;

            leds.show();
            Serial.write(resp);
        }
        else if(cmd == CMDTYPE::GETID)
        {
          Serial.write(EEPROM.read(16));

        }
        else if(cmd == CMDTYPE::SETID)
        {
            if(size != 1)
            {
                Serial.write(RETURN_CODES::ERROR_SIZE);
            }
            else
            {
                uint8_t id = Serial.read();
                #ifdef USE_EEPROM
                    EEPROM.write(16, id);
                #endif
                Serial.write(RETURN_CODES::SUCCESS);
            }
        }
        else if (cmd == CMDTYPE::SETUP_DATA)
        {
            uint8_t result = RETURN_CODES::SUCCESS;
            config_t temp;

            if (size != sizeof(config_t))
            {
                result = RETURN_CODES::ERROR_SIZE;
            }
            else
            {
                size_t read = Serial.readBytes((char*)&temp, sizeof(config_t));
                if (read != size)
                {
                    result = RETURN_CODES::ERROR_SIZE;
                }
                else
                {
                    // dont care about matching sizes
                    //if(temp.pixel_count / bytesPerPixel != NUM_LEDS_PER_STRIP)
                    //    result = RETURN_CODES::ERROR_PIXEL_COUNT;
                }
            }

            Serial.write(result);
        }
        else if (cmd == CMDTYPE::BRIGHTNESS)
        {
            uint8_t result = RETURN_CODES::SUCCESS;
            if (size != 1)
                result = RETURN_CODES::ERROR_SIZE;
            else
            {
                //uint8_t brightness = MAX_BRIGHTNESS;
                //size_t read = Serial.readBytes((char*)&brightness, 1);
                //if (read != size)
                //    result = RETURN_CODES::ERROR_SIZE;
                //else
                //{
                    //FastLED.setBrightness(max(MAX_BRIGHTNESS, brightness));
                //}
            }

            Serial.write(result);
        }
        else if (cmd == CMDTYPE::GETVER)
        {
            Serial.write(RETURN_CODES::SUCCESS);
            Serial.write(FIRMWARE_VER);
        }
        else
        {
            Serial.write(RETURN_CODES::ERROR_BAD_CMD);
        }


        Serial.flush();
    }
}

// phaseShift is the shift between each row.  phaseShift=0
// causes all rows to show the same colors moving together.
// phaseShift=180 causes each row to be the opposite colors
// as the previous.
//
// cycleTime is the number of milliseconds to shift through
// the entire 360 degrees of the color wheel:
// Red -> Orange -> Yellow -> Green -> Blue -> Violet -> Red
//
void rainbow(int phaseShift, int cycleTime)
{
  int color, x, y, wait;

  wait = cycleTime * 1000 / NUM_LEDS_PER_STRIP;
  for (color=0; color < 180; color++) {
    digitalWrite(1, HIGH);
    for (x=0; x < NUM_LEDS_PER_STRIP; x++) {
      for (y=0; y < 8; y++) {
        int index = (color + x + y*phaseShift/2) % 180;
        leds.setPixel(x + y*NUM_LEDS_PER_STRIP, rainbowColors[index]);
      }
    }
    leds.show();
    digitalWrite(1, LOW);
    delayMicroseconds(wait);
  }
}
// Convert HSL (Hue, Saturation, Lightness) to RGB (Red, Green, Blue)
//
//   hue:        0 to 359 - position on the color wheel, 0=red, 60=orange,
//                            120=yellow, 180=green, 240=blue, 300=violet
//
//   saturation: 0 to 100 - how bright or dull the color, 100=full, 0=gray
//
//   lightness:  0 to 100 - how light the color is, 100=white, 50=color, 0=black
//
int makeColor(unsigned int hue, unsigned int saturation, unsigned int lightness)
{
  unsigned int red, green, blue;
  unsigned int var1, var2;

  if (hue > 359) hue = hue % 360;
  if (saturation > 100) saturation = 100;
  if (lightness > 100) lightness = 100;

  // algorithm from: http://www.easyrgb.com/index.php?X=MATH&H=19#text19
  if (saturation == 0) {
    red = green = blue = lightness * 255 / 100;
  } else {
    if (lightness < 50) {
      var2 = lightness * (100 + saturation);
    } else {
      var2 = ((lightness + saturation) * 100) - (saturation * lightness);
    }
    var1 = lightness * 200 - var2;
    red = h2rgb(var1, var2, (hue < 240) ? hue + 120 : hue - 240) * 255 / 600000;
    green = h2rgb(var1, var2, hue) * 255 / 600000;
    blue = h2rgb(var1, var2, (hue >= 120) ? hue - 120 : hue + 240) * 255 / 600000;
  }
  return (red << 16) | (green << 8) | blue;
}

unsigned int h2rgb(unsigned int v1, unsigned int v2, unsigned int hue)
{
  if (hue < 60) return v1 * 60 + (v2 - v1) * hue;
  if (hue < 180) return v2 * 60;
  if (hue < 240) return v1 * 60 + (v2 - v1) * (240 - hue);
  return v1 * 60;
}

void loop()
{
    rainbow(10, 2500);
    //getData();
}
