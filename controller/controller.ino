#define USE_OCTOWS2811
#include <OctoWS2811.h>
#include <FastLED.h>
#include <EEPROM.h>

/***************************
User defines
***************************/
#define NUM_LEDS_PER_STRIP 143
#define NUM_STRIPS 8

#define MAX_BRIGHTNESS 255
#define GLOBAL_BRIGHTNESS 255

#define FIRMWARE_VER 3
#define SERIALRATE 12000000 // Full USB 1.1 speed (native USB)

/***************************
LEDs Setup
***************************/
CRGB leds[NUM_STRIPS * NUM_LEDS_PER_STRIP];

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

inline void setup_leds()
{
    pinMode(1, OUTPUT);
    digitalWrite(1, HIGH);
    LEDS.addLeds<OCTOWS2811>(leds, NUM_LEDS_PER_STRIP);
    LEDS.setBrightness(255);
    digitalWrite(1, LOW);
    //leds.begin();
    for(int i = 0; i < NUM_STRIPS; i++) {
        for(int j = 0; j < NUM_LEDS_PER_STRIP; j++) {
            leds[(i*NUM_LEDS_PER_STRIP) + j] = CRGB(255,0,0);
        }
    }
    LEDS.show();
    delay(1000);
    for(int i = 0; i < NUM_STRIPS; i++) {
        for(int j = 0; j < NUM_LEDS_PER_STRIP; j++) {
            leds[(i*NUM_LEDS_PER_STRIP) + j] = CHSV(0,0,0);
        }
    }
    LEDS.show();
  
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

            LEDS.show();
            Serial.write(resp);
        }
        else if(cmd == CMDTYPE::GETID)
        {
            Serial.write(0);
          //Serial.write(EEPROM.read(16));

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
                //#ifdef USE_EEPROM
                //    EEPROM.write(16, id);
                //#endif
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
                uint8_t brightness = MAX_BRIGHTNESS;
                size_t read = Serial.readBytes((char*)&brightness, 1);
                if (read != size)
                    result = RETURN_CODES::ERROR_SIZE;
                else
                {
                    LEDS.setBrightness(min(MAX_BRIGHTNESS, brightness));
                }
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


void loop()
{
      getData();
      LEDS.delay(0);
//    static uint8_t hue = 0;
//    for(int i = 0; i < NUM_STRIPS; i++) {
//        for(int j = 0; j < NUM_LEDS_PER_STRIP; j++) {
//            leds[(i*NUM_LEDS_PER_STRIP) + j] = CHSV((32*i) + hue+j,192,255);
//        }
//    }
//
//    hue++;
//
//    LEDS.show();
//    LEDS.delay(10);
}
