require('dotenv').config();

const fs = require('fs');
const cors = require("cors");
const express = require("express");
const http = require('http');
const MQTT = require('mqtt');
const { spawn } = require('child_process');
const APP = express();
const server = http.createServer(APP);
const { Server } = require("socket.io");

const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const CLIENTID = "frontend";

// Debug: Print environment variables (hide sensitive info)
console.log('🔍 Environment Variables Check:');
console.log('CONNECT_URL:', process.env.CONNECT_URL ? '✅ Set' : '❌ Not set');
console.log('MQTT_USER:', process.env.MQTT_USER ? '✅ Set' : '❌ Not set');
console.log('MQTT_PASS:', process.env.MQTT_PASS ? '✅ Set' : '❌ Not set');

if (!process.env.CONNECT_URL) {
  console.error('❌ CONNECT_URL is not set. Please check your .env file or environment variables.');
  console.log('📝 Create a .env file with:');
  console.log('CONNECT_URL=mqtt://your-broker-host:1883');
  console.log('MQTT_USER=your_username');
  console.log('MQTT_PASS=your_password');
  process.exit(1);
}

console.log('🔗 Attempting to connect to:', process.env.CONNECT_URL);

// MQTT connection options with detailed logging
const mqttOptions = {
  clientId: CLIENTID,
  clean: true,
  connectTimeout: 30000,
  username: process.env.MQTT_USER,
  password: process.env.MQTT_PASS,
  reconnectPeriod: 10000,
  debug: true, // Enable debug mode
  rejectUnauthorized: false
};

console.log('🔧 MQTT Options:', {
  clientId: mqttOptions.clientId,
  connectTimeout: mqttOptions.connectTimeout,
  username: mqttOptions.username ? '✅ Set' : '❌ Not set',
  password: mqttOptions.password ? '✅ Set' : '❌ Not set',
  reconnectPeriod: mqttOptions.reconnectPeriod
});

const client = MQTT.connect(process.env.CONNECT_URL, mqttOptions);

// Comprehensive event logging
client.on("connect", function(connack) {
  console.log("🎉 MQTT Connected successfully!");
  console.log("Connection acknowledgment:", connack);
  
  const topics = ['ultrasonic', 'temp', 'humidity', 'light'];
  
  topics.forEach(topic => {
    client.subscribe(topic, (err) => {
      if (err) {
        console.error(`❌ Subscription error for '${topic}':`, err);
      } else {
        console.log(`✅ Successfully subscribed to '${topic}'`);
      }
    });
  });
});

client.on("error", function(error) {
  console.error("❌ MQTT Connection error:", error);
  console.error("Error code:", error.code);
  console.error("Error message:", error.message);
  
  // Provide specific troubleshooting based on error
  if (error.code === 'ECONNREFUSED') {
    console.log('🔧 Troubleshooting ECONNREFUSED:');
    console.log('1. Check if MQTT broker is running');
    console.log('2. Verify the broker URL and port');
    console.log('3. Check firewall settings');
  } else if (error.code === 'ENOTFOUND') {
    console.log('🔧 Troubleshooting ENOTFOUND:');
    console.log('1. Check if the hostname is correct');
    console.log('2. Verify DNS resolution');
  }
});

client.on("close", function() {
  console.log("🔌 MQTT Connection closed");
});

client.on("disconnect", function() {
  console.log("❌ MQTT Client disconnected");
});

client.on("offline", function() {
  console.log("📴 MQTT Client went offline");
});

client.on("reconnect", function() {
  console.log("🔄 MQTT Attempting to reconnect...");
});

client.on("end", function() {
  console.log("🏁 MQTT Connection ended");
});

// Test connection after a delay
setTimeout(() => {
  console.log('📊 Connection Status Check:');
  console.log('Connected:', client.connected);
  console.log('Disconnecting:', client.disconnecting);
  console.log('Disconnected:', client.disconnected);
  console.log('Reconnecting:', client.reconnecting);
}, 5000);

const corsOptions = {
  origin: '*'
};

APP.use(cors(corsOptions));
APP.use(express.json());

// Readings from sensors 
let latestTemp = null;
let latestUltrasonic = null;
let latestHumidity = null;
let latestLight = null;

io.on("connection", (socket) => {
  console.log("🌐 Frontend connected to socket");

  // Send connection status
  socket.emit('mqtt_status', { 
    connected: client.connected,
    message: client.connected ? 'MQTT Connected' : 'MQTT Disconnected'
  });

  // Send the latest sensor data to the newly connected client
  if (latestTemp) socket.emit('temp', latestTemp);
  if (latestUltrasonic) socket.emit('ultrasonic', latestUltrasonic);
  if (latestHumidity) socket.emit('humidity', latestHumidity);
  if (latestLight) socket.emit('light', latestLight);

  socket.on('display', (message) => {
    console.log('📤 Received message from frontend:', message);
    if (client.connected) {
      client.publish("display", message.toString(), (err) => {
        if (err) {
          console.error('❌ Publish error:', err);
        } else {
          console.log('✅ Message published successfully');
        }
      });
    } else {
      console.error('❌ Cannot publish: MQTT client not connected');
      socket.emit('error', 'MQTT broker not connected');
    }
  });

  socket.on('take_picture', () => {
    console.log('📸 Taking picture and getting AI description...');
    
    const pythonProcess = spawn('python3', ['../AI/receive.py'], {
      cwd: __dirname
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`🐍 Python output: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`🐍 Python error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      console.log(`🐍 Python script finished with code ${code}`);
      if (code === 0) {
        socket.emit('picture_taken', { success: true, message: 'Picture analyzed successfully!' });
      } else {
        socket.emit('picture_taken', { success: false, message: 'Failed to analyze picture' });
      }
    });
  });

  socket.on("disconnect", () => {
    console.log("🔌 Frontend disconnected from socket");
  });
});

// Only emit data if we have valid values and MQTT is connected
setInterval(() => {
  if (client.connected) {
    if (latestTemp !== null) io.emit('temp', latestTemp);
    if (latestUltrasonic !== null) io.emit('ultrasonic', latestUltrasonic);
    if (latestHumidity !== null) io.emit('humidity', latestHumidity);
    if (latestLight !== null) io.emit('light', latestLight);
  }
}, 1000);

server.listen(8000, () => {
  console.log('🚀 Server is running on port 8000');
  console.log('🔗 MQTT Status:', client.connected ? '✅ Connected' : '⏳ Connecting...');
});

client.on('message', (topic, payload) => {
  console.log("📥 Received from broker:", topic, payload.toString());
  
  switch(topic) {
    case 'temp':
      latestTemp = payload.toString();
      io.emit('temp', latestTemp);
      break;
    case 'ultrasonic':
      latestUltrasonic = payload.toString();
      io.emit('ultrasonic', latestUltrasonic);
      break;
    case 'humidity':
      latestHumidity = payload.toString();
      io.emit('humidity', latestHumidity);
      break;
    case 'light':
      latestLight = payload.toString();
      io.emit('light', latestLight);
      break;
    default:
      console.log('❓ Unknown topic:', topic);
  }
});
