#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <chrono>
#include <algorithm>
#include "mqtt/async_client.h"
#include <fstream>
#include <sstream>

#define RCV_ADDR 0x42
#define RTCM3_PREAMBLE 0xD3
#define NMEA_PREAMBLE 0x24
#define ENDLINE 0x0A

float timestamp;
double hdop = 0;
int rtk_flag = 0;

const std::string DFLT_ADDRESS { "localhost:1883" };
const std::string TOPIC { "bike/sensor/gps" };
const std::string TOPIC2 { "bike/display/rtk" };
const std::string CLIENT_ID { "gipies" };
const int QOS = 0;

const uint8_t RMC_SET[]{
	0xB5, 0x62, 0x06, 0x8A, 0x0E, 0x00, 
	0x00, 0x01, 0x00, 0x00, 0xB5, 0x00, 
	0x91, 0x20, 0x00, 0xAB, 0x00, 0x91, 
	0x20, 0x01, 0x62, 0x48   
	};

const uint8_t SET_NMEA[] = {
    0xB5, 0x62, 0x06, 0x8A, 0x0E, 0x00,
    0x00, 0x01, 0x00, 0x00, 0xAB, 0x00,
    0x91, 0x20, 0x01, 0xB5, 0x00, 0x91,
    0x20, 0x01, 0x63, 0x1C
};

const uint8_t USB_SET[]{
    0xB5, 0x62, 0x06, 0x8A, 0x18, 0x00,
    0x00, 0x01, 0x00, 0x00, 0x01, 0x00,
    0x78, 0x10, 0x01, 0x01, 0x00, 0x78,
    0x10, 0x01, 0x02, 0x00, 0x78, 0x10,
    0x01, 0x01, 0x00, 0x77, 0x10, 0x01, 
    0xD1, 0x28, 0x00, 0x00
};

const uint8_t DISABLE_UART1[] = {
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00,
    0x01, 0x00, 0x00, 0x00, 0xD0, 0x08,
    0x00, 0x00, 0x00, 0x96, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x89, 0x46};

const uint8_t DISABLE_UART2[] = {
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 
    0x02, 0x00, 0x00, 0x00, 0xD0, 0x08, 
    0x00, 0x00, 0x00, 0x96, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x8A, 0x5A};


const uint8_t DISABLE_USB[] = {
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00,
    0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x1D, 0x84};

const uint8_t DISABLE_SPI[] = {
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 
    0x04, 0x00, 0x00, 0x00, 0x00, 0x32, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x50, 0x86};

const uint8_t SET_RATE_UTC[] = {
    0xB5, 0x62, 0x06, 0x08, 0x06, 0x00,
    0x19, 0x00, 0x01, 0x00, 0x00, 0x00,
    0x2E, 0x4E
};

const uint8_t SET_RATE_GPS[] = {
    0xB5, 0x62, 0x06, 0x08, 0x06, 0x00,
    0x19, 0x00, 0x01, 0x00, 0x01, 0x00,
    0x2F, 0x50
};

const uint8_t SET_RATE_GAL[] = {
    0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 
    0x19, 0x00, 0x01, 0x00, 0x02, 0x00, 
    0x30, 0x52
};

const uint8_t SET_RATE_GLO[] = {
    0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 
    0x19, 0x00, 0x01, 0x00, 0x03, 0x00, 
    0x31, 0x54
};

const uint8_t SET_RATE_BDS[] = {
    0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 
    0x19, 0x00, 0x01, 0x00, 0x04, 0x00, 
    0x32, 0x56,
};

const uint8_t SET_I2C_OUT[] = {

};

const uint8_t SET_I2C_IN[] = {

};

const uint8_t GPS_EXC_SET[] = {
    0xB5, 0x62, 0x06, 0x8A, 0x36, 0x00,
    0x00, 0x01, 0x00, 0x00, 0x1F, 0x00,
    0x31, 0x10, 0x01, 0x20, 0x00, 0x31,
    0x10, 0x00, 0x01, 0x00, 0x31, 0x10,
    0x01, 0x03, 0x00, 0x31, 0x10, 0x01,
    0x04, 0x00, 0x31, 0x10, 0x01, 0x21,
    0x00, 0x31, 0x10, 0x00, 0x22, 0x00,
    0x31, 0x10, 0x00, 0x24, 0x00, 0x31,
    0x10, 0x00, 0x25, 0x00, 0x31, 0x10,
    0x00, 0x26, 0x00, 0x31, 0x10, 0x00,
    0x4E, 0xA9
};

const uint8_t *commands[] = {
    DISABLE_UART1,
    DISABLE_UART2,
    //DISABLE_USB,
    DISABLE_SPI,
    SET_RATE_UTC,
    SET_RATE_GPS,
    SET_RATE_GAL,
    SET_RATE_GLO,
    SET_RATE_BDS,
    SET_NMEA,
    USB_SET,
    GPS_EXC_SET

};

std::string convert_to_string(char* a)
{
    std::string s = a;
    return s;
}

void sendConfig(int i2cHandle)
{
    for (int i = 0; i < sizeof(commands); i++){
        write(i2cHandle, commands[i], sizeof(commands[i]));
    }
}

unsigned long millis()
{
    return std::chrono::duration_cast<std::chrono::milliseconds>(
               std::chrono::high_resolution_clock::now().time_since_epoch()
           ).count();
}

volatile double mili()
{
    double fractional_seconds_since_epoch
    = std::chrono::duration_cast<std::chrono::duration<double>>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    return fractional_seconds_since_epoch;
}

double dms2dd(double dms)
{
    int deg = dms/100;
    double min = (double)dms-100*deg;
    min = 10*min/6;
    return deg+min/100;
}

void write_to_file(uint8_t *ptr, size_t len, mqtt::topic& top1, mqtt::topic& top2, double stamp) {
    static int disp_counter = 0;
    std::vector<std::string> msg;
    std::string str;
    std::string even;
    std::stringstream strim(convert_to_string(reinterpret_cast<char*>(ptr)));
    while (getline(strim, str, ','))
        msg.push_back(str);
    try{
        if(msg[0] == "$GNRMC")
	    {
        if(msg[8] == "")
            msg[8] = std::to_string(0);
        even = "gps," + std::to_string(stamp) + "," + std::to_string(dms2dd(stod(msg[5]))) + " " + std::to_string(dms2dd(stod(msg[3]))) + " " + std::to_string(1.852 * std::stod(msg[7])) + " "  + msg[8] + " " + std::to_string(hdop) + " " + std::to_string(rtk_flag) + ",bike/sensor/gps,string";
		top1.publish(std::move(even));
        }
        if(msg[0] == "$GNGNS")
	    {
        if(msg[8] == "")
            hdop = 0;
        else{
            hdop = std::stod(msg[8]);
            rtk_flag = (msg[6] != "") ? ((msg[6] == "FFFFNN") ? 1 : 0): rtk_flag;
            disp_counter++;
            if(disp_counter > 100)
            {
                top2.publish(std::move(std::to_string(rtk_flag)));
                disp_counter = 0;
            }
        }
        }
    }

    catch(std::exception &exc){
        std::cout << exc.what();
        std::cout<<"No mqtt\n";
    }
        


}

int i2cOpen()
{
    int i2cHandle; 
    while ((i2cHandle = open("/dev/i2c-1", O_RDWR))<0)
    {
        std::cerr << "Failed to open I2C device.\n";
    }
    return i2cHandle;
}

void i2cSetAddress(int i2cHandle)
{
    while (ioctl(i2cHandle, I2C_SLAVE, RCV_ADDR) < 0)
    {
        std::cerr << "Failed to set I2C address.\n";
    }
}

void i2cWrite(const std::vector<uint8_t> data, int i2cHandle)
{
    if (write(i2cHandle, data.data(), data.size()) != data.size()) {
        std::cerr << "Failed to send I2C data.\n";
    }
}

void readRTCM(int i2cHandle)
{
    while(true){
    std::vector<uint8_t> rtcm_bytes;
    char rtcm_byte;
    if (std::cin.get(rtcm_byte) && rtcm_byte == RTCM3_PREAMBLE)
    {
        std::string line;
        std::getline(std::cin, line, '\n');  
        for (char c : line)
        {
            rtcm_bytes.push_back(reinterpret_cast<uint8_t&>(c));
        }
        i2cWrite(rtcm_bytes, i2cHandle);
    }
    }
}

void readNMEA(int i2cHandle)
{

    mqtt::async_client cli(DFLT_ADDRESS, CLIENT_ID);
    mqtt::topic top1(cli, TOPIC, QOS, true);
    mqtt::topic top2(cli, TOPIC2, QOS, true);
    try{
        cli.connect()->wait();
    }
    catch(std::exception){
        std::cerr<<"No client";
    }
    while(true){
    uint8_t received_bytes[92] = {'$'};
    uint8_t received_byte;
    int i = 1;

    if (read(i2cHandle, &received_byte, 1) == 1 && received_byte == NMEA_PREAMBLE)
    {
        while(read(i2cHandle, &received_byte, 1) == 1 && received_byte != ENDLINE && received_byte > 0x20) {
            received_byte &= 0b01111111;
            received_bytes[i] = received_byte;
            i++;
        }
        received_bytes[i] = ENDLINE;
        double stamp = mili() - timestamp;
        write_to_file(received_bytes, i+1, top1, top2, stamp);
    }
    }
}

int setup()
{
    unsigned long startTime = millis();
    int i2cHandle = i2cOpen();
    i2cSetAddress(i2cHandle);
    sendConfig(i2cHandle);
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    std::cout<<"Connected "<<i2cHandle<<"\n";
    return i2cHandle;
}

void fill_timestamp()
{
    std::ifstream file ("/home/catreson/skrypty/timestamp.txt");
    if (file.is_open())
    {
    std::string line;
    std::getline(file,line);
    timestamp = std::stod(line);
    file.close();
    }

}

int main()
{
    int i2cHandle = setup();
    fill_timestamp();
    std::thread th2(readRTCM, i2cHandle);
    std::thread th1(readNMEA, i2cHandle);
    th1.join();
    close(i2cHandle);
    return 0;
}
