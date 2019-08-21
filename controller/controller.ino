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


void flash(CRGB color, uint8_t ms, uint8_t times) {
    for(int t = 0; t < times; t++) {
        for(int i = 0; i < NUM_STRIPS; i++) {
            for(int j = 0; j < NUM_LEDS_PER_STRIP; j++) {
                leds[(i*NUM_LEDS_PER_STRIP) + j] = color;
            }
        }
        LEDS.show();
        delay(ms);
        for(int i = 0; i < NUM_STRIPS; i++) {
            for(int j = 0; j < NUM_LEDS_PER_STRIP; j++) {
                leds[(i*NUM_LEDS_PER_STRIP) + j] = CHSV(0,0,0);
            }
        }
        LEDS.show(); 
        delay(ms); 
    }
}

inline void setup_leds()
{
    LEDS.addLeds<OCTOWS2811>(leds, NUM_LEDS_PER_STRIP);
    LEDS.setBrightness(255);
    flash(CRGB(255,0,0), 500, 3); 
//    leds[0] = CRGB(255,0,0);
//    leds[2] = CRGB(0,255,0);
//    leds[4] = CRGB(0,0,255);    
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
            //flash(CRGB(0,255,0), 500, 2);
            //Serial.write(0);
            Serial.write(EEPROM.read(16));

        }
        else if(cmd == CMDTYPE::SETID)
        {
            //flash(CRGB(0,0,255), 500, 2);
            if(size != 1)
            {
                Serial.write(RETURN_CODES::ERROR_SIZE);
            }
            else
            {
                uint8_t id = Serial.read();
                EEPROM.write(16, id);

                Serial.write(RETURN_CODES::SUCCESS);
            }
        }
        else if (cmd == CMDTYPE::SETUP_DATA)
        {
            //flash(CRGB(255,0,0), 500, 1);
            uint8_t result = RETURN_CODES::SUCCESS;
            config_t temp;
            uint8_t bytesPerPixel = 3;

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
                    if(temp.pixel_count / bytesPerPixel != NUM_LEDS_PER_STRIP * NUM_STRIPS)
                        result = RETURN_CODES::ERROR_PIXEL_COUNT;
                    //result = RETURN_CODES::SUCCESS;
                }
            }

            Serial.write(result);
        }
        else if (cmd == CMDTYPE::BRIGHTNESS)
        {
            //flash(CRGB(255,255,255), 500, 3);
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
            //flash(CRGB(255,0,0), 100, 5);
            Serial.write(RETURN_CODES::ERROR_BAD_CMD);
        }


        Serial.flush();
    }
}


void loop()
{
      getData();
//      LEDS.delay(0);
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
